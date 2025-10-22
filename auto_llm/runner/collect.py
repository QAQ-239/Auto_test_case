#!/usr/bin/env python3
"""
采集 pytest 产物并输出结构化总结
"""
import json
import pathlib
import sys
import time
import zipfile
from typing import Any, Dict, List, Optional

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = BASE_DIR / "artifacts"
PYTEST_STDOUT = ARTIFACTS_DIR / "pytest_stdout.log"
PYTEST_STDERR = ARTIFACTS_DIR / "pytest_stderr.log"
PYTEST_LOG = ARTIFACTS_DIR / "pytest.log"


def read_json(path: pathlib.Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def summarize(duration_s: float, exit_code: int, run_id: Optional[str]) -> Dict[str, Any]:
    report = read_json(ARTIFACTS_DIR / "report.json")
    tests = report.get("tests", [])

    failures: List[Dict[str, Any]] = []
    for case in tests:
        if case.get("outcome") == "failed":
            failure_info: Dict[str, Any] = {
                "nodeid": case.get("nodeid"),
                "outcome": case.get("outcome"),
                "line": case.get("lineno"),
            }
            call_info = case.get("call") or {}
            if isinstance(call_info, dict):
                failure_info["duration"] = call_info.get("duration")
                longrepr = call_info.get("longrepr") or call_info.get("crash")
                if longrepr:
                    failure_info["longrepr"] = longrepr
            failures.append(failure_info)

    totals = {
        "total": len(tests),
        "passed": sum(1 for item in tests if item.get("outcome") == "passed"),
        "failed": sum(1 for item in tests if item.get("outcome") == "failed"),
        "skipped": sum(1 for item in tests if item.get("outcome") == "skipped"),
    }

    artifact_candidates = {
        "junit_xml": ARTIFACTS_DIR / "junit.xml",
        "json_report": ARTIFACTS_DIR / "report.json",
        "coverage_xml": ARTIFACTS_DIR / "coverage.xml",
        "bench_json": ARTIFACTS_DIR / "bench.json",
        "pytest_stdout": PYTEST_STDOUT,
        "pytest_stderr": PYTEST_STDERR,
        "pytest_log": PYTEST_LOG,
    }
    artifacts: Dict[str, str] = {
        name: str(path)
        for name, path in artifact_candidates.items()
        if path.exists()
    }

    summary = {
        "run_id": run_id or f"{int(time.time())}",
        "duration_s": float(duration_s),
        "exit_code": int(exit_code),
        "totals": totals,
        "artifacts": artifacts,
    }

    if failures:
        summary["failures"] = failures

    if PYTEST_STDOUT.exists() or PYTEST_STDERR.exists():
        summary["logs"] = {
            "stdout": str(PYTEST_STDOUT) if PYTEST_STDOUT.exists() else None,
            "stderr": str(PYTEST_STDERR) if PYTEST_STDERR.exists() else None,
            "pytest_log": str(PYTEST_LOG) if PYTEST_LOG.exists() else None,
        }
    return summary


def pack_artifacts(out_zip: pathlib.Path) -> None:
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as bundle:
        for file_path in ARTIFACTS_DIR.rglob("*"):
            if file_path.is_file():
                bundle.write(file_path, file_path.relative_to(ARTIFACTS_DIR))


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: collect.py <duration_s> <exit_code> [run_id]")

    duration_s = float(sys.argv[1])
    exit_code = int(sys.argv[2])
    run_id = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None

    summary = summarize(duration_s, exit_code, run_id)
    bundle_zip = ARTIFACTS_DIR / f"bundle_{summary['run_id']}.zip"
    pack_artifacts(bundle_zip)
    summary["artifacts"]["bundle_zip"] = str(bundle_zip)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
