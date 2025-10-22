"""Gradio 界面：用户故事 → 测试用例 → 脚本生成 → 自动执行"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Optional, Tuple

import gradio as gr

from auto_llm.auto_exec import pipeline as pipeline_mod
from auto_llm.testcase_generator import StoryMetadata, generate_test_suite

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SUITE_PATH = BASE_DIR / "case_inputs" / "test_suite_math.json"
DEFAULT_REQUEST_TEMPLATE = BASE_DIR / "input_examples" / "exec_request.json"
DEFAULT_RUNNER_PATH = BASE_DIR / "runner" / "run.py"
DEFAULT_OUTPUT_ROOT = pipeline_mod.BASE_DIR
DEFAULT_ARTIFACTS_DIR = BASE_DIR / "artifacts"
DEFAULT_CI_OUTPUT_PATH = pipeline_mod.DEFAULT_CI_OUTPUT
DEFAULT_GIT_ROOT = pipeline_mod.BASE_DIR.parent.parent


def _parse_http_headers(text: Optional[str]) -> list[str]:
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def _extract_summary(stdout: str) -> Tuple[Optional[Dict], Optional[str]]:
    if not stdout:
        return None, "输出为空"
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
        return None, "未解析到结构化摘要"
    return candidate, None


def _load_default_suite() -> str:
    if DEFAULT_SUITE_PATH.exists():
        return DEFAULT_SUITE_PATH.read_text(encoding="utf-8")
    return ""


def run_pipeline_interactive(
    story_text: str,
    suite_json: str,
    mode: str,
    run_pytest: bool,
    mock_response_path: Optional[str],
    subprocess_cmd: Optional[str],
    local_qwen_path: Optional[str],
    http_endpoint: Optional[str],
    http_model: Optional[str],
    http_api_key: Optional[str],
    http_api_key_env: str,
    http_timeout: float,
    custom_system_prompt: Optional[str],
    request_template_path: Optional[str],
    runner_path: Optional[str],
    auto_fix: bool,
    max_fixes: int,
    artifacts_path: Optional[str],
    suite_id_hint: Optional[str],
    suite_name_hint: Optional[str],
    target_hint: Optional[str],
    entry_point_hint: Optional[str],
    fixtures_hint: Optional[str],
    generate_ci: bool,
    ci_output_path: Optional[str],
    ci_python_version: str,
    git_auto_push: bool,
    git_root: Optional[str],
    git_remote: Optional[str],
    git_branch: Optional[str],
    git_commit_message: Optional[str],
) -> Tuple[str, str, str, str, str, str, str, str, str]:
    story_clean = (story_text or "").strip()
    suite_clean = (suite_json or "").strip()
    suite_display = ""
    ci_yaml_text = ""
    ci_path_display = ""
    git_log_output = ""
    git_status_note = ""

    def _result(
        status: str,
        suite_str: str,
        script_str: str,
        stdout_str: str,
        stderr_str: str,
        artifact_str: str,
        fix_log: str,
        ci_yaml: str,
        git_log: str,
    ):
        return (
            status,
            suite_str,
            script_str,
            stdout_str,
            stderr_str,
            artifact_str,
            fix_log,
            ci_yaml,
            git_log,
        )

    def _error(message: str) -> Tuple[str, str, str, str, str, str, str, str, str]:
        return _result(
            f"❌ {message}",
            suite_display,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        )

    args = SimpleNamespace()
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
    args.auto_fix = auto_fix
    args.max_fixes = max_fixes
    args.artifacts_path = artifacts_path.strip() if artifacts_path else str(DEFAULT_ARTIFACTS_DIR)
    args.http_endpoint = http_endpoint.strip() if http_endpoint else None
    args.http_model = http_model.strip() if http_model else None
    args.http_header = []
    args.http_api_key = http_api_key
    args.http_api_key_env = http_api_key_env or "LLM_API_KEY"
    args.http_timeout = http_timeout
    args.http_schema = "simple"
    args.suite_id = suite_id_hint or None
    args.suite_name = suite_name_hint or None
    args.target = target_hint or None
    args.entry_point = entry_point_hint or None
    args.fixtures_hint = fixtures_hint or None
    args.story = story_clean or None
    args.story_file = None

    try:
        client = pipeline_mod.build_client(args)
    except Exception as exc:  # noqa: BLE001
        return _error(f"创建 LLM 客户端失败：{exc}")

    if story_clean:
        metadata = StoryMetadata(
            suite_id=args.suite_id,
            suite_name=args.suite_name,
            target=args.target,
            entry_point=args.entry_point,
            fixtures_hint=args.fixtures_hint,
        )
        try:
            suite_data = generate_test_suite(story_clean, client, metadata)
            suite_display = json.dumps(suite_data, ensure_ascii=False, indent=2)
        except Exception as exc:  # noqa: BLE001
            return _error(f"根据用户故事生成测试用例失败：{exc}")
    else:
        if not suite_clean:
            return _error("请至少提供标准化测试用例 JSON 或用户故事文本")
        try:
            suite_data = json.loads(suite_clean)
            suite_display = json.dumps(suite_data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError as exc:
            return _error(f"JSON 解析失败：{exc}")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(suite_data, tmp, ensure_ascii=False, indent=2)
        suite_tmp_path = tmp.name

    args.suite = suite_tmp_path

    guide_text = custom_system_prompt.strip() if custom_system_prompt else None
    output_root_path = Path(args.output_root).resolve()
    try:
        script_path = pipeline_mod.generate_script(
            suite_data,
            client,
            output_root_path,
            guide_text,
        )
    except Exception as exc:  # noqa: BLE001
        return _error(f"生成脚本失败：{exc}")

    script_text = script_path.read_text(encoding="utf-8")
    script_location = str(script_path.resolve())
    repo_root_value = git_root.strip() if git_root and git_root.strip() else str(pipeline_mod.BASE_DIR.parent.parent)
    repo_root_path = Path(repo_root_value).resolve()
    ci_path_obj: Optional[Path] = None

    if generate_ci and ci_output_path and ci_output_path.strip():
        try:
            artifacts_hint = artifacts_path.strip() if artifacts_path else str(DEFAULT_ARTIFACTS_DIR)
            script_rel_repo = os.path.relpath(script_path.resolve(), repo_root_path)
            ci_context = {
                "python_version": ci_python_version or "3.10",
                "test_command": f"python -m pytest {script_rel_repo}",
                "artifacts_path": artifacts_hint,
                "requirements_file": "auto_llm/requirements.txt",
                "entry_point": suite_data.get("context", {}).get("entry_point", "tests/test_generated.py"),
            }
            ci_path_obj, ci_yaml_text = pipeline_mod.generate_ci_yaml(
                suite=suite_data,
                client=client,
                output_root=output_root_path,
                ci_output_path=ci_output_path.strip(),
                ci_context=ci_context,
            )
            ci_path_display = str(ci_path_obj)
        except Exception as exc:  # noqa: BLE001
            ci_yaml_text = f"# 生成 CI 工作流失败: {exc}"

    if not run_pytest:
        return _result(
            "✅ 已生成脚本（未执行测试）",
            suite_display,
            script_text,
            "",
            "",
            ci_path_display,
            ci_yaml_text,
            git_log_output,
        )

    try:
        exec_template = pipeline_mod.load_exec_template(Path(args.request_template).resolve())
        exec_request = pipeline_mod.prepare_exec_request(exec_template, script_location)
        runner_path_resolved = pipeline_mod.resolve_runner_path(args.runner_path)
        exit_code, runner_stdout, runner_stderr = pipeline_mod.run_tests(exec_request, runner_path_resolved)
    except Exception as exc:  # noqa: BLE001
        return _result(
            f"❌ 测试执行失败：{exc}",
            suite_display,
            script_text,
            "",
            "",
            "",
            "",
            ci_yaml_text,
            git_log_output,
        )

    fix_log_output = ""
    if auto_fix and exit_code != 0:
        artifacts_dir = Path(args.artifacts_path).resolve()
        final_code, fixed_stdout, fixed_stderr, fix_log = pipeline_mod.try_auto_fix(
            suite=suite_data,
            client=client,
            output_root=output_root_path,
            artifacts_dir=artifacts_dir,
            runner_path=runner_path_resolved,
            exec_template=exec_template,
            script_relative=script_location,
            max_fixes=max_fixes,
        )
        if final_code == 0:
            script_text = script_path.read_text(encoding="utf-8")
            exit_code = 0
            runner_stdout = fixed_stdout or runner_stdout
            runner_stderr = fixed_stderr or runner_stderr
            runner_stdout += "\n[自动修复] 修复成功，测试通过。"
        if fix_log:
            fix_log_output = fix_log

    if exit_code == 0 and git_auto_push:
        commit_message_value = (
            git_commit_message.strip() if git_commit_message and git_commit_message.strip() else "chore: update generated tests"
        )
        remote_value = git_remote.strip() if git_remote and git_remote.strip() else "origin"
        branch_value = git_branch.strip() if git_branch and git_branch.strip() else None
        files_to_stage = [script_path]
        if ci_path_obj:
            files_to_stage.append(ci_path_obj)
        success, git_log = pipeline_mod.git_auto_push(
            repo_root=repo_root_path,
            files=files_to_stage,
            commit_message=commit_message_value,
            remote=remote_value,
            branch=branch_value,
        )
        git_log_output = git_log
        git_status_note = "（git push 完成）" if success else "（git push 失败，请查看日志）"

    if not fix_log_output and "[pipeline][auto-fix" in runner_stdout:
        fix_log_output = "\n".join(
            line for line in runner_stdout.splitlines() if "[pipeline][auto-fix" in line
        )

    artifact_lines = ""
    summary, summary_err = _extract_summary(runner_stdout)
    artifacts_info = summary.get("artifacts") if isinstance(summary, dict) else None
    if isinstance(artifacts_info, dict):
        artifact_lines = "\n".join(f"{k}: {v}" for k, v in artifacts_info.items())
    if ci_path_display:
        artifact_lines = (artifact_lines + "\n" if artifact_lines else "") + f"ci_workflow: {ci_path_display}"

    status = "✅ 测试执行完成" if exit_code == 0 else f"⚠️ 测试执行完成，退出码 {exit_code}"
    if git_status_note and exit_code == 0:
        status += git_status_note
    return _result(
        status,
        suite_display,
        script_text,
        runner_stdout,
        runner_stderr,
        artifact_lines,
        fix_log_output,
        ci_yaml_text,
        git_log_output,
    )


DEFAULT_SUITE_TEXT = _load_default_suite()


with gr.Blocks(title="自动化测试生成与执行 Demo") as demo:
    gr.Markdown("## 开源大模型驱动的自动化软件测试与部署系统")

    with gr.Row():
        with gr.Column(scale=2):
            story_input = gr.Textbox(
                lines=12,
                label="用户故事 / 需求文档（可选）",
                placeholder="粘贴自然语言需求，例如用户故事、PRD" ,
            )
            suite_input = gr.Textbox(
                value=DEFAULT_SUITE_TEXT,
                lines=12,
                label="标准化测试用例 JSON（可选）",
                placeholder="若已有结构化测试用例，可直接粘贴 JSON",
            )
            suite_id_box = gr.Textbox(label="suite_id 提示", placeholder="例如 blog-api-smoke-001")
            suite_name_box = gr.Textbox(label="suite_name 提示", placeholder="如 Blog API 冒烟测试")
            target_box = gr.Textbox(label="目标地址提示", placeholder="http://localhost:8000")
            entry_point_box = gr.Textbox(label="入口文件提示", placeholder="tests/test_blog_api.py")
            fixtures_hint_box = gr.Textbox(label="fixtures 提示", placeholder="例如 需要鉴权 token")

        with gr.Column():
            mode_radio = gr.Radio(
                choices=["mock", "subprocess", "http"],
                value="mock",
                label="LLM 模式",
            )
            run_checkbox = gr.Checkbox(value=True, label="生成后执行 pytest")
            mock_file = gr.Textbox(label="mock 响应文件（可选）")
            subprocess_cmd_box = gr.Textbox(label="本地模型命令（subprocess）")
            local_qwen_box = gr.Textbox(label="local-llm快捷脚本路径")
            http_endpoint_box = gr.Textbox(label="HTTP Endpoint")
            http_model_box = gr.Textbox(label="HTTP 模型名称")
            http_key_box = gr.Textbox(label="API Key (可选)")
            http_key_env_box = gr.Textbox(value="LLM_API_KEY", label="API Key 环境变量名")
            http_timeout_slider = gr.Slider(10, 300, value=60, step=5, label="HTTP Timeout (秒)")
            system_prompt_box = gr.Textbox(label="自定义系统提示词 (可选)", lines=6)
            request_template_box = gr.Textbox(value=str(DEFAULT_REQUEST_TEMPLATE), label="执行请求模板路径")
            runner_path_box = gr.Textbox(value=str(DEFAULT_RUNNER_PATH), label="runner/run.py 路径")

            gr.Markdown("### 🔧 自动修复设置")
            auto_fix_checkbox = gr.Checkbox(value=False, label="启用自动修复")
            max_fixes_slider = gr.Slider(1, 10, value=2, step=1, label="最大修复次数")
            artifacts_path_box = gr.Textbox(
                value=str(DEFAULT_ARTIFACTS_DIR),
                label="测试产物目录",
            )
            gr.Markdown("### 🚀 CI/CD 与仓库同步")
            generate_ci_checkbox = gr.Checkbox(value=True, label="生成 CI/CD YAML")
            ci_output_path_box = gr.Textbox(
                value=str(DEFAULT_CI_OUTPUT_PATH),
                label="CI YAML 输出路径",
            )
            ci_python_box = gr.Textbox(value="3.10", label="CI Python 版本")
            git_push_checkbox = gr.Checkbox(value=False, label="测试成功后自动 git push")
            git_root_box = gr.Textbox(
                value=str(DEFAULT_GIT_ROOT),
                label="git 仓库根目录",
            )
            git_remote_box = gr.Textbox(value="origin", label="git 远程名称")
            git_branch_box = gr.Textbox(label="git 分支 (可选)")
            git_commit_box = gr.Textbox(
                value="chore: update generated tests",
                label="git 提交信息",
            )

    run_button = gr.Button("运行流水线", variant="primary")

    status_output = gr.Markdown()
    suite_output = gr.Code(label="生成的测试套件 JSON", language="json")
    script_output = gr.Code(label="生成的测试脚本", language="python")
    stdout_output = gr.Textbox(label="runner stdout", lines=10)
    stderr_output = gr.Textbox(label="runner stderr", lines=6)
    artifacts_output = gr.Textbox(label="产物路径", lines=6)
    autofix_output = gr.Textbox(label="自动修复日志", lines=6)
    ci_yaml_output = gr.Code(label="生成的 CI 工作流 YAML", language="yaml")
    git_log_output_box = gr.Textbox(label="Git 自动推送日志", lines=6)

    run_button.click(
        fn=run_pipeline_interactive,
        inputs=[
            story_input,
            suite_input,
            mode_radio,
            run_checkbox,
            mock_file,
            subprocess_cmd_box,
            local_qwen_box,
            http_endpoint_box,
            http_model_box,
            http_key_box,
            http_key_env_box,
            http_timeout_slider,
            system_prompt_box,
            request_template_box,
            runner_path_box,
            auto_fix_checkbox,
            max_fixes_slider,
            artifacts_path_box,
            suite_id_box,
            suite_name_box,
            target_box,
            entry_point_box,
            fixtures_hint_box,
            generate_ci_checkbox,
            ci_output_path_box,
            ci_python_box,
            git_push_checkbox,
            git_root_box,
            git_remote_box,
            git_branch_box,
            git_commit_box,
        ],
        outputs=[
            status_output,
            suite_output,
            script_output,
            stdout_output,
            stderr_output,
            artifacts_output,
            autofix_output,
            ci_yaml_output,
            git_log_output_box,
        ],
)


def launch() -> None:
    """供外部 python -m auto_llm.app 调用"""

    demo.launch()


if __name__ == "__main__":
    launch()
