"""
提示词构建模块：根据标准化测试用例生成给 LLM 的系统提示与用户提示。
"""
from __future__ import annotations

import textwrap
from typing import Any, Dict, List


DEFAULT_SCRIPT_GUIDE = textwrap.dedent(
    """
    你是一名资深测试开发工程师，需要根据标准化测试用例生成可运行的自动化脚本。
    生成脚本时必须遵循以下约束：

    1. 使用 Python 与 pytest 框架，文件放在 tests/ 目录下，入口文件名来自 entry_point 字段。
    2. 引入必要的依赖（如 requests、httpx 等），避免遗漏 import。
    3. 每个测试用例需包含：
       - 清晰的函数命名，包含 test_ 前缀与用例 ID。
       - 对测试步骤的注释或日志，便于追踪。
       - 对期望结果的断言，使用 pytest 原生断言。
    4. 若涉及固定前置条件，可生成 pytest fixture（例如 HTTP 客户端、鉴权 Token 等）。
    5. 失败时需要输出有价值的日志信息，例如响应内容、状态码等。
    6. 如有性能要求，使用 pytest-benchmark 或自定义计时逻辑，并确保不会阻塞整个脚本。
    7. 代码需自包含，可直接通过 `pytest -q tests/目标文件` 运行。
    8. 严格不要使用占位符，所有 TODO 需补全为可执行实现。

    输出仅包含完整的 Python 源代码，使用 Markdown 代码块包裹（```python）。
    """
).strip()


class PromptBuilder:
    """根据测试套件信息生成提示词文本。"""

    def __init__(self, script_guide: str | None = None) -> None:
        self.script_guide = script_guide or DEFAULT_SCRIPT_GUIDE

    def build_system_prompt(self) -> str:
        return self.script_guide

    def build_user_prompt(self, suite: Dict[str, Any]) -> str:
        sections: List[str] = []
        sections.append(self._render_suite_header(suite))
        sections.append(self._render_fixtures(suite.get("fixtures", [])))
        sections.append(self._render_test_cases(suite.get("test_cases", [])))
        sections.append(self._render_output_requirements(suite))
        return "\n\n".join([part for part in sections if part])

    def _render_suite_header(self, suite: Dict[str, Any]) -> str:

        context = suite.get("context", {})
        lines = [
            f"测试套件 ID: {suite.get('suite_id', 'N/A')}",
            f"测试套件名称: {suite.get('suite_name', 'N/A')}",
            f"套件描述: {suite.get('description', '无')}",
            f"目标语言: {context.get('language', 'python')}",
            f"测试框架: {context.get('framework', 'pytest')}",
            f"入口文件: {context.get('entry_point', 'tests/test_generated.py')}",
            f"目标系统/地址: {context.get('target', '未知')}",
        ]
        return "\n".join(lines)

    def _render_fixtures(self, fixtures: List[Dict[str, Any]]) -> str:
        if not fixtures:
            return ""
        lines = ["可用的固定装置（fixtures）："]
        for fixture in fixtures:
            detail_lines = [
                f"- 名称: {fixture.get('name')}",
                f"  类型: {fixture.get('type', 'custom')}",
            ]
            details = fixture.get("details")
            if isinstance(details, dict):
                detail_lines.append("  详细配置:")
                for key, value in details.items():
                    detail_lines.append(f"    {key}: {value}")
            lines.extend(detail_lines)
        return "\n".join(lines)

    def _render_test_cases(self, test_cases: List[Dict[str, Any]]) -> str:
        if not test_cases:
            return "（当前没有测试用例，请至少生成一个样例）"

        blocks: List[str] = []
        for case in test_cases:

            header = f"[{case.get('id', 'TC')}] {case.get('title', '未命名用例')} ({case.get('priority', 'P?')})"
            steps = case.get("steps", [])
            expected = case.get("expected_result", "未提供期望结果")
            step_lines = "\n".join([f"  {idx+1}. {step}" for idx, step in enumerate(steps)])
            block = textwrap.dedent(
                f"""
                用例: {header}
                步骤:
                {step_lines or '  暂无步骤'}
                期望结果: {expected}
                """
            ).strip()
            blocks.append(block)
        return "\n\n".join(blocks)

    def _render_output_requirements(self, suite: Dict[str, Any]) -> str:
        context = suite.get("context", {})
        entry_point = context.get("entry_point", "tests/test_generated.py")
        return (
            "请基于上述信息生成完整的测试脚本。"
            f"\n输出文件路径: {entry_point}"
            "\n确保所有用例均被实现，并在适当位置添加注释或日志。"
        )
