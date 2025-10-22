#!/usr/bin/env python3
"""
自动执行入口：
1. 读取执行请求
2. 构建 pytest 命令
3. 执行并记录时长
4. 调用 collect 汇总产物
"""
import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = BASE_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
PYTEST_STDOUT = ARTIFACTS_DIR / "pytest_stdout.log"
PYTEST_STDERR = ARTIFACTS_DIR / "pytest_stderr.log"
PYTEST_LOG = ARTIFACTS_DIR / "pytest.log"


def load_request(path: pathlib.Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_pytest_cmd(req: Dict) -> List[str]:
    suite = req.get("suite", {})
    framework = suite.get("framework", "pytest")
    if framework != "pytest":
        raise ValueError(f"暂不支持的测试框架: {framework}")

    paths = suite.get("paths") or ["tests/"]
    config = suite.get("config", {})
    reruns = config.get("reruns", 0)
    timeout_s = config.get("timeout_s")
    parallel = config.get("parallel", 0)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *paths,
        "--log-file",
        str(PYTEST_LOG),
        "--log-file-level=INFO",
        "--json-report",
        f"--json-report-file={ARTIFACTS_DIR / 'report.json'}",
        f"--junitxml={ARTIFACTS_DIR / 'junit.xml'}",
        "--cov=.",
        f"--cov-report=xml:{ARTIFACTS_DIR / 'coverage.xml'}",
        f"--benchmark-json={ARTIFACTS_DIR / 'bench.json'}",
        "-q",
    ]

    if reruns:
        cmd += ["--reruns", str(reruns)]

    if timeout_s:
        cmd += ["--timeout", str(int(timeout_s))]

    if parallel:
        cmd += ["-n", str(int(parallel))]

    return cmd


def run_pytest(cmd: List[str], env: Dict[str, str]) -> Tuple[int, float]:
    print("[runner] running:", " ".join(cmd))
    start = time.time()
    result = subprocess.run(
        cmd,
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    duration = time.time() - start

    PYTEST_STDOUT.write_text(result.stdout or "", encoding="utf-8")
    PYTEST_STDERR.write_text(result.stderr or "", encoding="utf-8")

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    return result.returncode, duration


def main() -> None:
    default_req = BASE_DIR / "input_examples" / "exec_request.json"
    req_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else default_req
    request = load_request(req_path)

    env = os.environ.copy()
    for key, value in request.get("env", {}).items():
        env[key] = str(value)

    pytest_cmd = build_pytest_cmd(request)
    exit_code, duration = run_pytest(pytest_cmd, env)

    run_id = request.get("run_id")
    collect_cmd: List[Optional[str]] = [
        sys.executable,
        str(BASE_DIR / "runner" / "collect.py"),
        f"{duration}",
        f"{exit_code}",
        run_id or "",
    ]
    subprocess.check_call(
        [arg for arg in collect_cmd if arg is not None],
        cwd=BASE_DIR,
        env=env,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
