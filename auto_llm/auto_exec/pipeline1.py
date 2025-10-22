#!/usr/bin/env python3
"""
一键流水线脚本：
1. 调用第二阶段生成器，根据标准化测试用例生成自动化脚本
2. 自动构造执行请求，仅运行新生成的脚本
3. 调用 runner/run.py 执行测试，并输出结果摘要
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from ..generator.llm_client import LLMClient, load_local_qwen_client
from ..generator.prompt_builder import PromptBuilder
from ..generator.tooling import WorkspaceManager, extract_code_block

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_EXEC_TEMPLATE = BASE_DIR / "input_examples" / "exec_request.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成测试脚本并执行的一键流水线")
    parser.add_argument("--suite", required=True, help="标准化测试用例 JSON 路径")
    parser.add_argument(
        "--output-root",
        default=str(BASE_DIR),
        help="生成测试脚本输出根目录，默认项目根目录",
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "subprocess", "http"],
        default="mock",
        help="LLM 调用模式",
    )
    parser.add_argument("--mock-response", help="mock 模式下的模型响应文件")
    parser.add_argument(
        "--subprocess-cmd",
        nargs="+",
        help="本地子进程调用命令，例如：python auto_exec/scripts/qwen_cli.py --model ...",
    )
    parser.add_argument(
        "--local-qwen",
        help="快捷方式：传入可执行的本地模型脚本，相当于 --mode subprocess --subprocess-cmd <path>",
    )
    parser.add_argument("--system-guide", help="自定义系统提示词模板文件")
    parser.add_argument(
        "--http-endpoint",
        help="HTTP 模式下的推理 API 地址",
    )
    parser.add_argument(
        "--http-model",
        help="HTTP 模式下使用的模型名称",
    )
    parser.add_argument(
        "--http-header",
        action="append",
        default=[],
        help="附加 HTTP 头，格式 key:value，可重复",
    )
    parser.add_argument(
        "--http-api-key",
        help="直接传入 API Key，优先级高于环境变量",
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
        "--request-template",
        default=str(DEFAULT_EXEC_TEMPLATE),
        help="执行请求模板 JSON，默认使用 input_examples/exec_request.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只生成脚本不执行测试",
    )
    parser.add_argument(
        "--runner-path",
        help="自定义 runner/run.py 路径，默认尝试 auto_exec/runner/run.py 或上级 runner/run.py",
    )
    return parser.parse_args()


def load_suite(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_exec_template(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_subprocess_cmd(cmd_args: Optional[list[str]]) -> Optional[list[str]]:
    if not cmd_args:
        return None
    if len(cmd_args) == 1:
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


def generate_script(
    suite: Dict[str, Any],
    client: LLMClient,
    output_root: Path,
    guide_text: Optional[str] = None,
) -> Path:
    builder = PromptBuilder(script_guide=guide_text)
    system_prompt = builder.build_system_prompt()
    user_prompt = builder.build_user_prompt(suite)

    response = client.generate_code(system_prompt, user_prompt)
    code_text = extract_code_block(response)

    entry_point = suite.get("context", {}).get("entry_point", "tests/test_generated.py")
    workspace = WorkspaceManager(output_root)
    target_path = workspace.write_file(entry_point, code_text)
    print(f"[pipeline] 已生成脚本: {target_path}")
    return target_path


def prepare_exec_request(template: Dict[str, Any], script_relative: str) -> Dict[str, Any]:
    modified = dict(template)
    suite = dict(modified.get("suite", {}))
    suite["paths"] = [script_relative]
    modified["suite"] = suite
    return modified


def resolve_runner_path(custom_path: Optional[str]) -> Path:
    if custom_path:
        path = Path(custom_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"未找到指定的 runner 路径: {path}")
        return path

    candidates = [
        BASE_DIR / "runner" / "run.py",
        BASE_DIR.parent / "runner" / "run.py",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "未在默认位置找到 runner/run.py，请使用 --runner-path 指定具体路径。"
    )


def run_tests(exec_request: Dict[str, Any], runner_path: Path) -> tuple[int, str, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(exec_request, tmp, ensure_ascii=False, indent=2)
        tmp_path = Path(tmp.name)
    print(f"[pipeline] 执行请求写入: {tmp_path}")

    cmd = [sys.executable, str(runner_path), str(tmp_path)]
    print(f"[pipeline] 调用: {' '.join(cmd)}")
    runner_cwd = runner_path.parent.parent
    result = subprocess.run(
        cmd,
        cwd=runner_cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        print(f"[pipeline] 测试执行失败，退出码 {result.returncode}", file=sys.stderr)
    return result.returncode, result.stdout or "", result.stderr or ""


def main() -> None:
    args = parse_args()

    suite_path = Path(args.suite).resolve()
    suite = load_suite(suite_path)

    guide_text = None
    if args.system_guide:
        guide_text = Path(args.system_guide).read_text(encoding="utf-8")

    client = build_client(args)
    output_root = Path(args.output_root).resolve()

    script_path = generate_script(suite, client, output_root, guide_text)
    script_relative = str(script_path.relative_to(output_root))

    if args.dry_run:
        print("[pipeline] dry-run 模式，跳过测试执行。")
        return

    exec_template = load_exec_template(Path(args.request_template).resolve())
    exec_request = prepare_exec_request(exec_template, script_relative)

    runner_path = resolve_runner_path(args.runner_path)
    exit_code, _, _ = run_tests(exec_request, runner_path)
    if exit_code == 0:
        print("[pipeline] 测试执行完成，结果成功。")
    else:
        print("[pipeline] 测试执行完成，存在失败，请查看 artifacts/ 日志与摘要。", file=sys.stderr)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
