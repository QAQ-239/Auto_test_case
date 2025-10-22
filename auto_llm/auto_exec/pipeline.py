#!/usr/bin/env python3
"""
一键流水线脚本：
1. 调用第二阶段生成器，根据标准化测试用例生成自动化脚本
2. 自动构造执行请求，仅运行新生成的脚本
3. 调用 runner/run.py 执行测试，并输出结果摘要
"""
from __future__ import annotations

print(f"[pipeline] module loaded from: {__file__}")

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..generator.llm_client import LLMClient, load_local_qwen_client
from ..generator.prompt_builder import PromptBuilder
from ..generator.tooling import WorkspaceManager, extract_code_block
from ..testcase_generator import StoryMetadata, generate_test_suite

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_EXEC_TEMPLATE = BASE_DIR / "input_examples" / "exec_request.json"
DEFAULT_ARTIFACTS_DIR = BASE_DIR / "artifacts"
DEFAULT_CI_OUTPUT = BASE_DIR.parent / "artifacts" / "generated_ci.yml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成测试脚本并执行的一键流水线")
    parser.add_argument("--suite", help="标准化测试用例 JSON 路径")
    parser.add_argument("--story", help="用户故事或需求文档内容（直接输入文本）")
    parser.add_argument("--story-file", help="用户故事或需求文档文件路径")
    parser.add_argument("--suite-id", help="自动生成测试套件时使用的 suite_id")
    parser.add_argument("--suite-name", help="自动生成测试套件时使用的 suite_name")
    parser.add_argument("--target", help="测试上下文中的目标地址，例如 API 网关")
    parser.add_argument("--entry-point", help="自动生成测试套件时的入口文件名")
    parser.add_argument("--fixtures-hint", help="提醒模型在 fixtures 中补充的额外信息，例如鉴权方式")
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
        "--http-schema",
        choices=["openai", "simple"],
        default="openai",
        help="HTTP 请求 payload 结构：openai 使用 messages 数组，simple 使用 system/user 字段",
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
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="当测试失败时，使用同一大模型分析 artifacts 日志并自动修复测试代码",
    )
    parser.add_argument(
        "--max-fixes",
        type=int,
        default=2,
        help="自动修复的最大迭代次数（默认 2）",
    )
    parser.add_argument(
        "--artifacts-path",
        default=str(DEFAULT_ARTIFACTS_DIR),
        help="测试产物目录（包含日志与报告），可设置为绝对路径",
    )
    parser.add_argument(
        "--ci-output",
        default=str(DEFAULT_CI_OUTPUT),
        help="生成的 CI/CD YAML 保存路径，留空可通过 --skip-ci 禁用",
    )
    parser.add_argument(
        "--skip-ci",
        action="store_true",
        help="跳过 CI/CD YAML 生成",
    )
    parser.add_argument(
        "--ci-python",
        default="3.10",
        help="CI 工作流中的 Python 版本提示，默认 3.10",
    )
    parser.add_argument(
        "--git-auto-push",
        action="store_true",
        help="测试脚本成功执行后自动进行 git add/commit/push",
    )
    parser.add_argument(
        "--git-root",
        default=str(BASE_DIR.parent.parent),
        help="git 仓库根目录，默认推测为项目根",
    )
    parser.add_argument(
        "--git-remote",
        default="origin",
        help="git push 的远程名称，默认 origin",
    )
    parser.add_argument(
        "--git-branch",
        help="git push 的分支名称，未提供时自动检测当前分支",
    )
    parser.add_argument(
        "--git-commit-message",
        default="chore: update generated tests",
        help="git 提交信息，默认 'chore: update generated tests'",
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
            http_schema=getattr(args, "http_schema", "openai"),
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


# ----------------------- CI/CD generation ----------------------------------
def _resolve_output_path(base_root: Path, path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        return (base_root / path).resolve()
    return path


def generate_ci_yaml(
    suite: Dict[str, Any],
    client: LLMClient,
    output_root: Path,
    ci_output_path: str,
    ci_context: Dict[str, str],
) -> Tuple[Path, str]:
    """
    调用 LLM 生成 CI/CD YAML 并写入目标路径。
    返回 (文件路径, 文本内容)。
    """
    builder = PromptBuilder()
    system_prompt, user_prompt = builder.build_ci_prompts(suite, ci_context)
    response = client.generate_code(system_prompt, user_prompt)
    yaml_text = extract_code_block(response).strip()
    target_path = _resolve_output_path(output_root, ci_output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(yaml_text, encoding="utf-8")
    print(f"[pipeline] 已生成 CI 工作流: {target_path}")
    return target_path, yaml_text


def _run_git_command(cmd: List[str], cwd: Path) -> Tuple[int, str, str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def git_auto_push(
    repo_root: Path,
    files: List[Path],
    commit_message: str,
    remote: str,
    branch: Optional[str],
) -> Tuple[bool, str]:
    """
    在测试成功后自动执行 git add/commit/push。
    返回 (成功标记, 日志字符串)。
    """
    log_lines: List[str] = []
    repo_root = repo_root.resolve()
    if not (repo_root / ".git").exists():
        log_lines.append(f"[git] 仓库根目录 {repo_root} 未检测到 .git，跳过自动推送。")
        return False, "\n".join(log_lines)

    rel_paths: List[str] = []
    for path in files:
        if not path:
            continue
        resolved = path.resolve()
        try:
            rel_paths.append(str(resolved.relative_to(repo_root)))
        except ValueError:
            # 若不在仓库内，则使用绝对路径
            rel_paths.append(str(resolved))

    if not rel_paths:
        log_lines.append("[git] 没有需要提交的文件。")
        return False, "\n".join(log_lines)

    add_cmd = ["git", "add"] + rel_paths
    code, out, err = _run_git_command(add_cmd, repo_root)
    log_lines.append(f"[git] {' '.join(add_cmd)}")
    if out:
        log_lines.append(out.strip())
    if err:
        log_lines.append(err.strip())
    if code != 0:
        log_lines.append("[git] git add 失败，停止后续步骤。")
        return False, "\n".join(log_lines)

    commit_cmd = ["git", "commit", "-m", commit_message]
    code, out, err = _run_git_command(commit_cmd, repo_root)
    log_lines.append(f"[git] {' '.join(commit_cmd)}")
    if out:
        log_lines.append(out.strip())
    if err:
        log_lines.append(err.strip())
    if code != 0:
        if "nothing to commit" in (out + err):
            log_lines.append("[git] 无需提交，跳过 push。")
            return True, "\n".join(log_lines)
        log_lines.append("[git] git commit 失败，停止后续步骤。")
        return False, "\n".join(log_lines)

    target_branch = branch
    if not target_branch:
        code, out, err = _run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_root)
        if code == 0:
            target_branch = out.strip()
        else:
            log_lines.append("[git] 无法获取当前分支，默认使用 HEAD 推送。")

    push_cmd = ["git", "push", remote]
    if target_branch:
        push_cmd.append(target_branch)
    code, out, err = _run_git_command(push_cmd, repo_root)
    log_lines.append(f"[git] {' '.join(push_cmd)}")
    if out:
        log_lines.append(out.strip())
    if err:
        log_lines.append(err.strip())
    if code != 0:
        log_lines.append("[git] git push 失败。")
        return False, "\n".join(log_lines)

    log_lines.append("[git] 自动推送完成。")
    return True, "\n".join(log_lines)


# ----------------------- Auto-fix utilities -------------------------------
def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def collect_failure_context(artifacts_dir: Path) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    读取摘要与关键日志，供 LLM 进行失败原因分析与修复。
    返回 (summary_json, logs_map)
    """
    summary_path = artifacts_dir / "report.json"
    junit_path = artifacts_dir / "junit.xml"
    cov_path = artifacts_dir / "coverage.xml"
    bench_path = artifacts_dir / "bench.json"
    stdout_path = artifacts_dir / "pytest_stdout.log"
    stderr_path = artifacts_dir / "pytest_stderr.log"
    plain_log = artifacts_dir / "pytest.log"

    summary_json: Dict[str, Any] = {}
    try:
        if summary_path.exists():
            summary_json = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        summary_json = {}

    logs = {
        "junit_xml": _read_text(junit_path),
        "coverage_xml": _read_text(cov_path),
        "bench_json": _read_text(bench_path),
        "pytest_stdout": _read_text(stdout_path),
        "pytest_stderr": _read_text(stderr_path),
        "pytest_log": _read_text(plain_log),
    }
    return summary_json, logs


def try_auto_fix(
    suite: Dict[str, Any],
    client: LLMClient,
    output_root: Path,
    artifacts_dir: Path,
    runner_path: Path,
    exec_template: Dict[str, Any],
    script_relative: str,
    max_fixes: int,
) -> Tuple[int, str, str, str]:
    """
    当首次执行失败时，迭代：收集日志 -> 让 LLM 生成修复版本 -> 覆盖写回 -> 重跑。
    返回 (最终退出码, 最新 stdout, 最新 stderr, 修复日志字符串)。
    """
    builder = PromptBuilder()
    workspace = WorkspaceManager(output_root)
    entry_point = suite.get("context", {}).get("entry_point", "tests/test_generated.py")

    log_messages: List[str] = []
    last_stdout = ""
    last_stderr = ""
    for attempt in range(1, max_fixes + 1):
        msg = f"[pipeline][auto-fix] 第 {attempt}/{max_fixes} 次尝试修复 …"
        print(msg)
        log_messages.append(msg)
        current_code = workspace.read_file(entry_point) or ""
        summary_json, logs = collect_failure_context(artifacts_dir)
        system_prompt, user_prompt = builder.build_repair_prompts(
            suite, current_code, summary_json, logs
        )
        try:
            response = client.generate_code(system_prompt, user_prompt)
            repaired_code = extract_code_block(response)
            workspace.write_file(entry_point, repaired_code, overwrite=True)
        except Exception as exc:  # noqa: BLE001
            err_msg = f"[pipeline][auto-fix] 生成或写回修复代码失败: {exc}"
            print(err_msg, file=sys.stderr)
            log_messages.append(err_msg)
            return 1, last_stdout, last_stderr, "\n".join(log_messages)

        # 重新执行
        exec_request = prepare_exec_request(exec_template, script_relative)
        exit_code, last_stdout, last_stderr = run_tests(exec_request, runner_path)
        if exit_code == 0:
            success_msg = "[pipeline][auto-fix] 修复成功，测试通过。"
            print(success_msg)
            log_messages.append(success_msg)
            return 0, last_stdout, last_stderr, "\n".join(log_messages)

    fail_msg = "[pipeline][auto-fix] 修复尝试耗尽，仍存在失败。"
    print(fail_msg, file=sys.stderr)
    log_messages.append(fail_msg)
    return 1, last_stdout, last_stderr, "\n".join(log_messages)


def main() -> None:
    args = parse_args()

    if not args.suite and not args.story and not args.story_file:
        raise SystemExit("请提供 --suite 或 --story/--story-file 之一")

    client = build_client(args)
    output_root = Path(args.output_root).resolve()

    suite: Dict[str, Any]
    suite_json_str: Optional[str] = None

    if args.story or args.story_file:
        if args.story:
            story_text = args.story
        else:
            story_path = Path(args.story_file).resolve()
            if not story_path.exists():
                raise SystemExit(f"未找到故事文件: {story_path}")
            story_text = story_path.read_text(encoding="utf-8")

        metadata = StoryMetadata(
            suite_id=args.suite_id,
            suite_name=args.suite_name,
            target=args.target,
            entry_point=args.entry_point,
            fixtures_hint=args.fixtures_hint,
        )

        suite = generate_test_suite(story_text, client, metadata)
        suite_json_str = json.dumps(suite, ensure_ascii=False, indent=2)

        if args.suite:
            suite_path = Path(args.suite).resolve()
            suite_path.parent.mkdir(parents=True, exist_ok=True)
            suite_path.write_text(suite_json_str, encoding="utf-8")
            print(f"[pipeline] 已根据用户故事生成测试套件并写入 {suite_path}")
        else:
            tmp_suite = tempfile.NamedTemporaryFile("w", suffix="_suite.json", delete=False)
            tmp_suite.write(suite_json_str)
            tmp_suite.close()
            print(f"[pipeline] 已根据用户故事生成测试套件: {tmp_suite.name}")
    else:
        suite_path = Path(args.suite).resolve()
        if not suite_path.exists():
            raise SystemExit(f"未找到测试套件文件: {suite_path}")
        suite = load_suite(suite_path)

    guide_text = None
    if args.system_guide:
        guide_text = Path(args.system_guide).read_text(encoding="utf-8")

    script_path = generate_script(suite, client, output_root, guide_text)
    ci_path: Optional[Path] = None
    repo_root = Path(args.git_root).resolve()
    entry_point = suite.get("context", {}).get("entry_point", "tests/test_generated.py")

    if not args.skip_ci and args.ci_output:
        try:
            artifacts_hint = getattr(args, "artifacts_path", str(DEFAULT_ARTIFACTS_DIR))
            script_rel_repo = os.path.relpath(script_path.resolve(), repo_root)
            ci_context = {
                "python_version": args.ci_python,
                "test_command": f"python -m pytest {script_rel_repo}",
                "artifacts_path": artifacts_hint,
                "requirements_file": "auto_llm/requirements.txt",
                "entry_point": entry_point,
            }
            ci_path, _ = generate_ci_yaml(
                suite=suite,
                client=client,
                output_root=output_root,
                ci_output_path=args.ci_output,
                ci_context=ci_context,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[pipeline] 生成 CI 工作流失败: {exc}", file=sys.stderr)

    runner_path = resolve_runner_path(args.runner_path)
    script_location = str(script_path.resolve())

    if args.dry_run:
        print("[pipeline] dry-run 模式，跳过测试执行。")
        if ci_path:
            print(f"[pipeline] CI 工作流文件位于: {ci_path}")
        return

    exec_template = load_exec_template(Path(args.request_template).resolve())
    exec_request = prepare_exec_request(exec_template, script_location)
    print(f"[pipeline] 准备执行脚本路径: {script_location}")
    print(f"[pipeline] pytest paths: {exec_request.get('suite', {}).get('paths')}")
    exit_code, runner_stdout, runner_stderr = run_tests(exec_request, runner_path)
    if exit_code == 0:
        print("[pipeline] 测试执行完成，结果成功。")
        print(runner_stdout, end="")
        if ci_path:
            print(f"[pipeline] CI 工作流文件位于: {ci_path}")
        if args.git_auto_push:
            files_to_push = [script_path]
            if ci_path:
                files_to_push.append(ci_path)
            success, git_log = git_auto_push(
                repo_root=repo_root,
                files=files_to_push,
                commit_message=args.git_commit_message,
                remote=args.git_remote,
                branch=args.git_branch,
            )
            print(git_log)
            if not success:
                print("[pipeline] git push 未成功，请检查日志。", file=sys.stderr)
        return

    print("[pipeline] 初次执行存在失败。", file=sys.stderr)

    if getattr(args, "auto_fix", False):
        artifacts_dir = Path(getattr(args, "artifacts_path", str(DEFAULT_ARTIFACTS_DIR))).resolve()
        final_code, fixed_stdout, fixed_stderr, fix_log = try_auto_fix(
            suite=suite,
            client=client,
            output_root=output_root,
            artifacts_dir=artifacts_dir,
            runner_path=runner_path,
            exec_template=exec_template,
            script_relative=script_location,
            max_fixes=int(getattr(args, "max_fixes", 2)),
        )
        if fix_log:
            print(fix_log, file=sys.stderr)
        if final_code == 0:
            print("[pipeline] 自动修复成功，使用修复后的结果。")
            runner_stdout = fixed_stdout or runner_stdout
            runner_stderr = fixed_stderr or runner_stderr
            print(runner_stdout, end="")
            if ci_path:
                print(f"[pipeline] CI 工作流文件位于: {ci_path}")
            if args.git_auto_push:
                files_to_push = [script_path]
                if ci_path:
                    files_to_push.append(ci_path)
                success, git_log = git_auto_push(
                    repo_root=repo_root,
                    files=files_to_push,
                    commit_message=args.git_commit_message,
                    remote=args.git_remote,
                    branch=args.git_branch,
                )
                print(git_log)
                if not success:
                    print("[pipeline] git push 未成功，请检查日志。", file=sys.stderr)
            return

    print("[pipeline] 测试执行完成，存在失败，请查看 artifacts/ 日志与摘要。", file=sys.stderr)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
