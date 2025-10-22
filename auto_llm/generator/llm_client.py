"""
LLM 客户端封装，负责与大模型交互。

目前支持三种模式：
1. mock：从指定文件读取预置响应，便于离线调试。
2. subprocess：通过命令行调用本地模型，可对接 /home/.../qwen2.5 等离线推理脚本。
3. （预留）HTTP：可在后续接入竞赛提供的 API。
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Iterable, List, Optional

import requests
from requests import RequestException


class LLMClient:
    """简单的对话式大模型客户端。"""

    def __init__(
        self,
        mode: str = "mock",
        mock_response_path: Optional[str] = None,
        subprocess_cmd: Optional[Iterable[str]] = None,
        http_endpoint: Optional[str] = None,
        http_headers: Optional[dict] = None,
        http_model: Optional[str] = None,
        http_timeout: Optional[float] = None,
        http_schema: str = "openai",
    ) -> None:
        self.mode = mode
        self.mock_response_path = Path(mock_response_path) if mock_response_path else None
        self.subprocess_cmd = list(subprocess_cmd) if subprocess_cmd else None
        self.http_endpoint = http_endpoint
        self.http_headers = http_headers or {}
        self.http_model = http_model
        self.http_timeout = http_timeout or 60.0
        self.http_schema = http_schema

    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        if self.mode == "mock":
            return self._from_mock()
        if self.mode == "subprocess":
            return self._from_subprocess(system_prompt, user_prompt)
        if self.mode == "http":
            return self._from_http(system_prompt, user_prompt)
        raise ValueError(f"未知模式: {self.mode}")

    # --- mode handlers -------------------------------------------------
    def _from_mock(self) -> str:
        if not self.mock_response_path:
            raise RuntimeError("mock 模式需要提供 mock_response_path")
        return self.mock_response_path.read_text(encoding="utf-8")

    def _from_subprocess(self, system_prompt: str, user_prompt: str) -> str:
        if not self.subprocess_cmd:
            raise RuntimeError("subprocess 模式需要提供 subprocess_cmd")

        payload = json.dumps(
            {
                "system": system_prompt,
                "user": user_prompt,
            },
            ensure_ascii=False,
        )
        proc = subprocess.run(
            list(self.subprocess_cmd),
            input=payload.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"子进程调用失败，退出码 {proc.returncode}，stderr={proc.stderr.decode('utf-8', errors='ignore')}"
            )
        return proc.stdout.decode("utf-8")

    def _from_http(self, system_prompt: str, user_prompt: str) -> str:
        if not self.http_endpoint:
            raise RuntimeError("HTTP 模式需要提供 http_endpoint")

        headers = dict(self.http_headers)
        headers.setdefault("Content-Type", "application/json")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        if self.http_schema == "simple":
            payload = {
                "system": system_prompt,
                "user": user_prompt,
            }
            if self.http_model:
                payload["model"] = self.http_model
        else:
            payload = {"messages": messages}
            if self.http_model:
                payload["model"] = self.http_model

        try:
            response = requests.post(
                self.http_endpoint,
                json=payload,
                headers=headers,
                timeout=self.http_timeout,
            )
        except RequestException as exc:
            raise RuntimeError(f"HTTP 调用失败: {exc}") from exc

        if response.status_code >= 400:
            raise RuntimeError(
                f"HTTP 调用返回错误码 {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"无法解析模型响应为 JSON: {response.text}"
            ) from exc

        # 尝试兼容常见的 OpenAI/通义 API 返回格式
        if isinstance(data, dict):
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    message = first.get("message")
                    if isinstance(message, dict):
                        content = message.get("content")
                        if content:
                            return content.strip()
                    content = first.get("text")
                    if isinstance(content, str):
                        return content.strip()
            # 备用字段，例如部分 API 使用 output_text 或 data 字段
            for key in ("output_text", "data", "result"):
                value = data.get(key)
                if isinstance(value, str):
                    return value.strip()
                if isinstance(value, list) and value and isinstance(value[0], str):
                    return value[0].strip()
            if "output" in data:
                value = data["output"]
                if isinstance(value, str):
                    return value.strip()
                if isinstance(value, dict):
                    text = value.get("text")
                    if isinstance(text, str):
                        return text.strip()

        raise RuntimeError(f"未能在响应中找到文本内容: {data}")


def load_local_qwen_client(model_path: Path | str) -> LLMClient:
    """
    根据约定创建一个调用本地 Qwen 推理脚本的客户端。
    约定：目标脚本支持通过 stdin 接收 JSON payload，stdout 输出回答文本。
    """
    cmd = [str(model_path)]
    return LLMClient(mode="subprocess", subprocess_cmd=cmd)
