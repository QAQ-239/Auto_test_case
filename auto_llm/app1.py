"""Gradio 界面：标准化测试用例 -> 大模型脚本生成 -> 自动执行 -> 结果回显"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

import gradio as gr

from auto_llm.auto_exec import pipeline as pipeline_mod

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SUITE_PATH = BASE_DIR / "case_inputs" / "test_suite_math.json"
DEFAULT_REQUEST_TEMPLATE = BASE_DIR / "input_examples" / "exec_request.json"
DEFAULT_RUNNER_PATH = BASE_DIR / "runner" / "run.py"
DEFAULT_OUTPUT_ROOT = pipeline_mod.BASE_DIR


def _parse_http_headers(text: str | None) -> List[str]:
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines


def _extract_summary(stdout: str) -> Tuple[Optional[Dict], Optional[str]]:
    if not stdout:
        return None, None
    candidate = None
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        if line.startswith("{"):
            try:
                candidate = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    if candidate is None:
        return None, "未在输出中解析到结构化摘要，请检查 runner 输出。"
    return candidate, None


def _load_default_suite() -> str:
    if DEFAULT_SUITE_PATH.exists():
        return DEFAULT_SUITE_PATH.read_text(encoding="utf-8")
    return ""


def run_pipeline_interactive(
    suite_json: str,
    mode: str,
    run_pytest: bool,
    mock_response_path: Optional[str],
    subprocess_cmd: Optional[str],
    local_qwen_path: Optional[str],
    http_endpoint: Optional[str],
    http_model: Optional[str],
    http_headers_text: Optional[str],
    http_api_key: Optional[str],
    http_api_key_env: str,
    http_timeout: float,
    custom_system_prompt: Optional[str],
    request_template_path: Optional[str],
    runner_path: Optional[str],
) -> Tuple[str, str, Optional[Dict], str, str, str, Optional[str]]:
    try:
        suite_data = json.loads(suite_json)
    except json.JSONDecodeError as exc:
        return (
            f"❌ JSON 解析失败：{exc}",
            "",
            None,
            "",
            "",
            "",
            None,
        )

    # 写入临时文件，便于复用 pipeline 工具
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(suite_data, tmp, ensure_ascii=False, indent=2)
        suite_tmp_path = tmp.name

    args = SimpleNamespace()
    args.suite = suite_tmp_path
    args.output_root = str(DEFAULT_OUTPUT_ROOT)
    args.mode = mode
    args.mock_response = mock_response_path.strip() if mock_response_path else None
    args.subprocess_cmd = [subprocess_cmd.strip()] if subprocess_cmd and subprocess_cmd.strip() else None
    args.local_qwen = local_qwen_path.strip() if local_qwen_path else None
    args.system_guide = None
    args.dry_run = not run_pytest
    args.request_template = (
        request_template_path.strip() if request_template_path else str(DEFAULT_REQUEST_TEMPLATE)
    )
    args.runner_path = runner_path.strip() if runner_path else str(DEFAULT_RUNNER_PATH)

    args.http_endpoint = http_endpoint.strip() if http_endpoint else None
    args.http_model = http_model.strip() if http_model else None
    args.http_header = _parse_http_headers(http_headers_text)
    args.http_api_key = http_api_key
    args.http_api_key_env = http_api_key_env or "LLM_API_KEY"
    args.http_timeout = http_timeout

    try:
        client = pipeline_mod.build_client(args)
    except Exception as exc:  # noqa: BLE001
        return (
            f"❌ 创建 LLM 客户端失败：{exc}",
            "",
            None,
            "",
            "",
            "",
            None,
        )

    guide_text = custom_system_prompt.strip() if custom_system_prompt else None
    try:
        script_path = pipeline_mod.generate_script(
            suite_data,
            client,
            Path(args.output_root),
            guide_text,
        )
    except Exception as exc:  # noqa: BLE001
        return (
            f"❌ 生成脚本失败：{exc}",
            "",
            None,
            "",
            "",
            "",
            None,
        )

    script_text = script_path.read_text(encoding="utf-8")
    script_relative = str(script_path.relative_to(Path(args.output_root)))

    if not run_pytest:
        status = "✅ 已生成脚本（未执行测试）。"
        return (
            status,
            script_text,
            {"message": "dry-run", "script_path": str(script_path)},
            "",
            "",
            "",
            None,
        )

    try:
        exec_template = pipeline_mod.load_exec_template(Path(args.request_template).resolve())
        exec_request = pipeline_mod.prepare_exec_request(exec_template, script_relative)
        runner_path_resolved = pipeline_mod.resolve_runner_path(args.runner_path)
        exit_code, runner_stdout, runner_stderr = pipeline_mod.run_tests(exec_request, runner_path_resolved)
    except Exception as exc:  # noqa: BLE001
        return (
            f"❌ 测试执行失败：{exc}",
            script_text,
            None,
            "",
            "",
            "",
            None,
        )

    summary, summary_err = _extract_summary(runner_stdout)
    if summary is None:
        summary_payload: Dict | None = {"error": summary_err or "未获取到摘要"}
    else:
        summary_payload = summary

    artifact_lines = ""
    bundle_path = None
    if isinstance(summary, dict):
        artifacts = summary.get("artifacts", {})
        if isinstance(artifacts, dict):
            artifact_lines = "\n".join(f"{k}: {v}" for k, v in artifacts.items())
            bundle = artifacts.get("bundle_zip")
            if bundle and Path(bundle).exists():
                bundle_path = bundle

    status = "✅ 测试执行完成" if exit_code == 0 else f"⚠️ 测试执行完成，退出码 {exit_code}"

    return (
        status,
        script_text,
        summary_payload,
        runner_stdout,
        runner_stderr,
        artifact_lines,
        bundle_path,
    )


DEFAULT_SUITE_TEXT = _load_default_suite()


with gr.Blocks(title="自动化测试生成与执行 Demo") as demo:
    gr.Markdown("## 标准化测试用例 → 大模型脚本 → 自动执行 → 结果汇总")

    with gr.Row():
        suite_input = gr.Textbox(
            value=DEFAULT_SUITE_TEXT,
            lines=18,
            label="标准化测试用例 JSON",
            placeholder="粘贴或编辑测试用例 JSON",
        )

        with gr.Column():
            mode_radio = gr.Radio(
                choices=["mock", "subprocess", "http"],
                value="mock",
                label="LLM 模式",
            )
            run_checkbox = gr.Checkbox(value=True, label="生成后执行 pytest")
            mock_file = gr.Textbox(label="mock 响应文件路径（可选）")
            subprocess_cmd_box = gr.Textbox(label="本地模型命令（subprocess）")
            local_qwen_box = gr.Textbox(label="本地模型脚本路径（local-qwen 快捷）")
            http_endpoint_box = gr.Textbox(label="HTTP Endpoint")
            http_model_box = gr.Textbox(label="HTTP 模型名称")
            http_headers_box = gr.Textbox(
                label="额外 HTTP 头 (每行一个 key:value)",
            )
            http_key_box = gr.Textbox(label="API Key (可选)")
            http_key_env_box = gr.Textbox(value="LLM_API_KEY", label="API Key 环境变量名")
            http_timeout_slider = gr.Slider(
                minimum=10,
                maximum=300,
                value=60,
                step=5,
                label="HTTP Timeout (秒)",
            )
            system_prompt_box = gr.Textbox(
                label="自定义系统提示词 (可选)",
                lines=6,
            )
            request_template_box = gr.Textbox(
                value=str(DEFAULT_REQUEST_TEMPLATE),
                label="执行请求模板路径",
            )
            runner_path_box = gr.Textbox(
                value=str(DEFAULT_RUNNER_PATH),
                label="runner/run.py 路径",
            )

    run_button = gr.Button("运行流水线", variant="primary")

    status_output = gr.Markdown()
    script_output = gr.Code(label="生成脚本", language="python")
    summary_output = gr.JSON(label="执行摘要")
    stdout_output = gr.Textbox(label="runner stdout", lines=10)
    stderr_output = gr.Textbox(label="runner stderr", lines=6)
    artifacts_output = gr.Textbox(label="产物路径", lines=6)
    bundle_output = gr.File(label="打包产物 (bundle_zip)")

    run_button.click(
        fn=run_pipeline_interactive,
        inputs=[
            suite_input,
            mode_radio,
            run_checkbox,
            mock_file,
            subprocess_cmd_box,
            local_qwen_box,
            http_endpoint_box,
            http_model_box,
            http_headers_box,
            http_key_box,
            http_key_env_box,
            http_timeout_slider,
            system_prompt_box,
            request_template_box,
            runner_path_box,
        ],
        outputs=[
            status_output,
            script_output,
            summary_output,
            stdout_output,
            stderr_output,
            artifacts_output,
            bundle_output,
        ],
    )


def launch():
    """供外部 python -m auto_llm.app 调用"""
    demo.launch()


if __name__ == "__main__":
    launch()
