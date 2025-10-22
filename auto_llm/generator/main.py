#!/usr/bin/env python3
"""
第二阶段脚本生成器：
给定标准测试用例 JSON，构建提示词并调用大模型生成自动化测试脚本。
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any, Dict

from .llm_client import LLMClient, load_local_qwen_client
from .prompt_builder import PromptBuilder
from .tooling import WorkspaceManager, extract_code_block

BASE_DIR = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="测试脚本自动生成器")
    parser.add_argument(
        "--suite",
        required=True,
        help="标准测试用例 JSON 文件路径",
    )
    parser.add_argument(
        "--output-root",
        default=str(BASE_DIR),
        help="脚本输出根目录（默认项目根目录）",
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "subprocess", "http"],
        default="mock",
        help="LLM 调用模式",
    )
    parser.add_argument(
        "--mock-response",
        help="mock 模式下，预置响应文件路径",
    )
    parser.add_argument(
        "--subprocess-cmd",
        nargs="+",
        help="subprocess 模式下调用本地模型的命令行，如 /home/.../qwen2.5 --format json",
    )
    parser.add_argument(
        "--local-qwen",
        help="快捷方式：传入本地 qwen 可执行脚本路径，相当于 --mode subprocess --subprocess-cmd <path>",
    )
    parser.add_argument(
        "--system-guide",
        help="自定义系统提示词模板文件",
    )
    parser.add_argument(
        "--http-endpoint",
        help="HTTP 模式下的推理 API 地址，例如 https://api.example.com/v1/chat/completions",
    )
    parser.add_argument(
        "--http-model",
        help="HTTP 模式下指定的模型名称，例如 gpt-4o 或 qwen-max",
    )
    parser.add_argument(
        "--http-header",
        action="append",
        default=[],
        help="附加 HTTP 头，格式 key:value，可重复传入",
    )
    parser.add_argument(
        "--http-api-key",
        help="直接指定 API Key，优先级高于环境变量",
    )
    parser.add_argument(
        "--http-api-key-env",
        default="LLM_API_KEY",
        help="从环境变量读取 API Key 的变量名，默认 LLM_API_KEY",
    )
    parser.add_argument(
        "--http-timeout",
        type=float,
        default=60.0,
        help="HTTP 请求超时时间（秒），默认 60",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印提示词与模型输出，不写入文件",
    )
    return parser.parse_args()


def load_suite(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data


def _normalize_subprocess_cmd(cmd_args: list[str] | None) -> list[str] | None:
    if not cmd_args:
        return None
    if len(cmd_args) == 1:
        # 允许传入带空格的整体命令字符串
        return shlex.split(cmd_args[0])
    return cmd_args


def _collect_http_headers(args: argparse.Namespace) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for raw in args.http_header or []:
        key, sep, value = raw.partition(":")
        if not sep:
            raise ValueError(f"无法解析 HTTP 头：{raw}，请使用 key:value 格式")
        headers[key.strip()] = value.strip()

    api_key = args.http_api_key or os.getenv(args.http_api_key_env or "")
    if api_key:
        headers.setdefault("Authorization", f"Bearer {api_key}")

    headers.setdefault("Content-Type", "application/json")
    return headers


def build_client(args: argparse.Namespace) -> LLMClient:
    if args.local_qwen:
        return load_local_qwen_client(args.local_qwen)
    if args.mode == "mock" and args.subprocess_cmd:
        # 用户未调整 mode，但提供了子进程命令；优先按 subprocess 处理
        cmd = _normalize_subprocess_cmd(args.subprocess_cmd)
        return LLMClient(mode="subprocess", subprocess_cmd=cmd)
    if args.mode == "mock":
        return LLMClient(mode="mock", mock_response_path=args.mock_response)
    if args.mode == "subprocess":
        cmd = _normalize_subprocess_cmd(args.subprocess_cmd)
        return LLMClient(mode="subprocess", subprocess_cmd=cmd)
    if args.mode == "http":
        if not args.http_endpoint:
            raise ValueError("HTTP 模式需要提供 --http-endpoint")
        headers = _collect_http_headers(args)
        return LLMClient(
            mode="http",
            http_endpoint=args.http_endpoint,
            http_headers=headers,
            http_model=args.http_model,
            http_timeout=args.http_timeout,
        )
    raise ValueError(f"不支持的模式: {args.mode}")


def main() -> None:
    args = parse_args()
    suite_path = Path(args.suite).resolve()
    if not suite_path.exists():
        raise SystemExit(f"未找到测试套件文件: {suite_path}")

    suite = load_suite(suite_path)

    # 构建提示词
    guide_text = None
    if args.system_guide:
        guide_text = Path(args.system_guide).read_text(encoding="utf-8")

    builder = PromptBuilder(script_guide=guide_text)
    system_prompt = builder.build_system_prompt()
    user_prompt = builder.build_user_prompt(suite)

    client = build_client(args)

    response_text = client.generate_code(system_prompt, user_prompt)
    code_text = extract_code_block(response_text)

    if args.dry_run:
        print("=== SYSTEM PROMPT ===")
        print(system_prompt)
        print("\n=== USER PROMPT ===")
        print(user_prompt)
        print("\n=== MODEL OUTPUT ===")
        print(response_text)
        return

    context = suite.get("context", {})
    entry_point = context.get("entry_point", "tests/test_generated.py")
    workspace = WorkspaceManager(Path(args.output_root))
    target_path = workspace.write_file(entry_point, code_text)

    print(f"[generator] 已将生成脚本写入 {target_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[generator][error] {exc}", file=sys.stderr)
        raise
