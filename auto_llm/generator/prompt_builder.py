"""
提示词构建模块：根据标准化测试用例生成给 LLM 的系统提示与用户提示。
"""
from __future__ import annotations

import textwrap
from typing import Any, Dict, List


DEFAULT_SCRIPT_GUIDE = textwrap.dedent(
    # """
    # 你是一名资深测试开发工程师，需要根据标准化测试用例生成可运行的自动化脚本。
    # 针对每一个测试用例都一步一步的思考该怎么去写测试脚本。
    # 请严格遵循以下约束：

    # 1. 使用 Python 与 pytest 框架，文件落在 tests/ 目录，入口文件名来自 entry_point 字段。
    # 2. 如果测试所需的函数或客户端不存在，请在同一脚本内定义（例如 add/sub/mul/div 等），避免引用未知模块。
    # 3. 仅输出纯粹的 Python 源码，禁止输出 Markdown 代码块（严禁出现 ```、```python、```py 等标记）或使用三引号包裹全文。
    # 4. 每个测试函数必须以 test_ 开头，并及时记录步骤/断言，使用 pytest 原生断言。
    # 5. 失败时需要给出有意义的错误信息；仅在必要时添加 fixture 或辅助函数。
    # 6. 如需求包含性能指标，可使用 pytest-benchmark；否则避免多余依赖。
    # 7. 生成的脚本需可直接通过 `pytest -q tests/入口文件` 运行。
    # 8. 严禁保留 TODO 或占位符，所有逻辑必须可执行。
    # 9. 针对每一条测试用例都要写测试脚本。
    # """
    """
    你是一名资深测试开发工程师，需要把“标准化测试用例 + 表单配置”转换为可运行的 pytest 测试脚本。
    请逐条内化以下规则，并依据输入自动选择“HTTP模式”或“本地模式”。
    【输入契约】
    - suite_id / suite_name：用于标识本次测试集和可读标题
    - target_url：可为空；不为空时表示存在可访问的服务根地址（例如 http://localhost:8000）
    - entry_point：脚本输出路径（例如 tests/test_calc_api.py）
    - fixtures：可为空；用于指出可能需要的登录/鉴权/数据准备信息
    - cases[]：标准化测试用例数组（已结构化）
    【模式判定】
    - 若 target_url 为非空、非占位串（不为 "N/A"、"-"、"None"），则启用 **HTTP模式**：
    - 使用 requests 调用接口；为每次请求设置超时（例如 5s）
    - 路径与方法以用例为准；请求体按 JSON 发送；断言包含状态码与 JSON 内容
    - 若 target_url 为空或显式声明“本地模式”，则启用 **本地模式**：
    - 严禁使用 requests / http 客户端
    - 被测函数（如 add/sub/mul/div）若在环境中不存在，必须在 **同一脚本内完整定义**
    - 直接调用本地函数并断言返回值/异常
    【通用约束（两种模式都必须遵守）】
    1) 仅使用 Python + pytest；每个测试函数以 test_ 开头
    2) 入口文件名严格使用 entry_point 字段；脚本可直接运行：pytest -q {entry_point}
    3) 输出必须是纯 Python 源码，禁止使用 Markdown 代码块（```、```python 等）
    4) 不得保留 TODO / pass 占位；逻辑必须可执行
    5) 失败分支需有明确断言：例如除法 b=0 时验证“divide by zero”（HTTP模式断言 error 字段；本地模式断言 ZeroDivisionError）
    6) 必要时可定义 fixture（例如 base_url），但避免无意义 fixture
    7) 若 cases[] 中包含对“result / error”键的要求，必须显式断言这些键
    8) 不得引用未知外部模块；HTTP模式仅允许使用 requests 访问 target_url；本地模式禁止 import 被测模块，需内联实现
    9) 若 target_url 缺失或为 placeholder，请坚持本地模式（自包含实现）；仅在确认可访问真实服务时才使用 HTTP 请求
    【输出要求】
    - 只输出最终的 Python 源码，符合以上约束
    - 脚本自包含、结构清晰、可直接运行
    """
).strip()

DEFAULT_CI_GUIDE = textwrap.dedent(
    """
    你是一名 DevOps 工程师，需要为当前项目生成一个 GitHub Actions 工作流 YAML。
    目标是展示如何在 CI 中安装依赖、运行自动化测试流水线，并收集产物。

    约束：
    1. 仅输出纯粹的 YAML 文本，禁止使用 Markdown 代码块或额外说明。
    2. 充分利用项目已有脚本与命令，确保步骤可直接在 ubuntu-latest 环境运行。
    3. 需要包含依赖安装、运行测试、归档 artifacts 等关键步骤。
    4. 允许在步骤中使用环境变量或条件，但要简洁清晰，便于后续扩展。
    """
).strip()

DEFAULT_CI_TEMPLATE = textwrap.dedent(
    """
    name: AutoLLM Pipeline

    on:
      push:
        branches: [ main ]
      pull_request:

    jobs:
      tests:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: '3.10'
          - name: Install dependencies
            run: |
              python -m pip install --upgrade pip
              pip install -r auto_llm/requirements.txt
          - name: Run automated pipeline
            run: |
              python -m auto_llm.auto_exec.pipeline --suite auto_llm/case_inputs/test_suite_math.json --mode mock --dry-run
          - name: Upload artifacts
            if: always()
            uses: actions/upload-artifact@v4
            with:
              name: auto-llm-artifacts
              path: auto_llm/artifacts/
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
        origin_story = suite.get("context", {}).get("origin_story")
        if origin_story:
            sections.append("原始用户故事 / 需求文档:\n" + origin_story)
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
        target = context.get("target")
        target_note = ""
        if not target or str(target).strip().lower() in {"", "未知", "n/a", "-", "none"} or "placeholder" in str(target).lower():
            target_note = "\n注意：当前目标地址为空或为占位值，请使用本地自包含逻辑，不要发送 HTTP 请求。"
        return (
            "请基于上述信息生成完整的测试脚本。"
            f"\n输出文件路径: {entry_point}"
            "\n确保所有用例均被实现，并在适当位置添加注释或日志。"
            f"{target_note}"
        )

    def _render_missing_module_hint(self, code: str) -> str:
        allowed_modules = {
            "pytest",
            "requests",
            "json",
            "math",
            "random",
            "time",
            "statistics",
            "itertools",
            "collections",
            "decimal",
            "fractions",
            "typing",
            "dataclasses",
            "pathlib",
            "os",
            "sys",
        }
        missing: List[str] = []
        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith("from ") and " import " in stripped:
                module = stripped.split(" ", 1)[1].split(" import ")[0].split(".")[0]
            elif stripped.startswith("import "):
                module = stripped.split(" ", 1)[1].split(",")[0].split(".")[0]
            else:
                continue
            module = module.strip()
            if not module or module in allowed_modules:
                continue
            missing.append(module)

        if not missing:
            return ""

        uniq = sorted(set(missing))
        modules_str = ", ".join(uniq)
        return (
            "检测到当前脚本引用了可能不存在的外部模块："
            f"{modules_str}。若项目中未提供这些实现，请删除相关 import，并在脚本内补全所需函数/逻辑。"
        )

    # --- Repair prompt building -------------------------------------------------
    def build_repair_prompts(
        self,
        suite: Dict[str, Any],
        current_code: str,
        summary_json: Dict[str, Any] | None,
        logs: Dict[str, str],
    ) -> tuple[str, str]:
        """
        基于失败摘要与日志构建“修复测试脚本”的提示词。

        返回 (system_prompt, user_prompt)。
        """
        entry_point = suite.get("context", {}).get("entry_point", "tests/test_generated.py")

        repair_guide = textwrap.dedent(
            # """
            # 你是一名资深测试开发工程师与代码修复专家。当前任务是在不改变被测功能语义的前提下，对已有 pytest/unittest 测试脚本进行“最小代价修复”，使脚本能够稳定通过执行。
            # 请逐条内化并严格遵守以下约束：
            # 【最终成功标准】
            # - 修复后的脚本必须可直接执行并通过：pytest -q {entry_point}
            # - 脚本必须可独立运行，不依赖外部未提供模块或服务
            # 【自包含优先原则（非常重要）】
            # - 若脚本 import 了不存在的模块（如 calculation_module），则必须：
            # 1) 删除该 import 语句
            # 2) 在同一脚本内补全被测函数的可运行实现（例如 add/sub/mul/div）
            # - 禁止保留任何无法解析或无法导入的依赖
            # 【允许的修改范围】
            # - 允许补全缺失函数、mock 逻辑、修正断言内容或调用方式
            # - 允许调整前置条件或测试输入以符合业务语义
            # - 允许删除/替换无效 import，但不能删除整个测试用例函数本身
            # 【禁止的行为】
            # - 禁止通过删除断言来回避错误
            # - 禁止调用 HTTP/外部服务（除非已有运行日志显示确实存在真实服务器）
            # - 禁止输出 Markdown 代码块符号（```、```python 等）
            # - 禁止留下 TODO、pass 或占位符
            # 【输出规则】
            # - 仅输出完整、最终版本 Python 源码，无 Markdown 包裹
            # - 代码必须自包含并可直接运行
            # - 文件结构与职责不发生跨文件分裂，每个测试用例必须保留或被等效修复

            # 请基于失败日志与现有脚本进行逐步思考后，输出最终可执行且能通过测试的完整修复脚本源码。

            # """

            """
            你是一名资深测试开发工程师与代码修复专家。任务是对现有 pytest 测试脚本进行“最小代价修复”，使其在目标模式下可稳定通过：pytest -q {entry_point}。
            【模式保持】
            - 若本次输入包含 target_url 且其为有效地址（非空/非占位），必须维持为 **HTTP模式**：
            - 使用 requests 访问 target_url；为每次请求设置合理超时
            - 不得引入除 requests 以外的 HTTP 客户端
            - 若 target_url 为空或显式本地模式，则必须维持 **本地模式**：
            - 禁止使用 HTTP/requests
            - 若脚本 import 了不存在的被测模块或工具（例如 calculator），必须删除该 import，并在同一脚本内补全被测函数实现，不得依赖外部库
            【修复边界】
            - 允许：修正断言、补全缺失函数、调整参数/前置、增加必要的 fixture、为 HTTP 请求补充 JSON/headers/timeout
            - 禁止：删除测试函数以回避失败、删除断言逃避校验、引入额外外部依赖/服务、输出 Markdown 代码块
            【成功标准】
            - 修复后可直接运行通过：pytest -q {entry_point}
            - 断言保持语义正确：正常路径断言 result，异常路径断言 error（HTTP）或对应异常（本地）
            - 所有逻辑可执行，脚本自包含
            【输出规范】
            - 仅输出修复后的完整 Python 源码（无解释文字、无 Markdown 包裹）
            """
        ).strip()

        sections: List[str] = []
        sections.append(self._render_suite_header(suite))
        origin_story = suite.get("context", {}).get("origin_story")
        if origin_story:
            sections.append("原始用户故事 / 需求文档:\n" + origin_story)
        sections.append("当前入口文件: " + entry_point)
        if summary_json:
            sections.append("失败摘要(JSON):\n" + textwrap.dedent(textwrap.fill(str(summary_json), width=120)))
        if logs:
            for name, content in logs.items():
                if not content:
                    continue
                # 限制每段日志长度以控制上下文大小
                snippet = content[-4000:]
                sections.append(f"日志[{name}] 片段(尾部截断):\n" + snippet)

        missing_hint = self._render_missing_module_hint(current_code)
        if missing_hint:
            sections.append(missing_hint)

        sections.append("当前测试代码:\n" + current_code)
        sections.append(
            "请基于上述信息，直接输出修复后的完整 Python 测试文件源码。禁止使用 Markdown 代码块或附加说明。"
        )

        user_prompt = "\n\n".join([part for part in sections if part])
        return repair_guide, user_prompt

    def build_ci_prompts(
        self,
        suite: Dict[str, Any],
        context: Dict[str, str],
    ) -> tuple[str, str]:
        """
        构建 CI/CD 工作流生成的提示词。
        context 传入与测试执行相关的命令、路径等信息。
        """
        entry_point = suite.get("context", {}).get("entry_point", "tests/test_generated.py")
        lines: list[str] = []
        lines.append(f"测试套件 ID: {suite.get('suite_id', 'N/A')}")
        lines.append(f"测试套件名称: {suite.get('suite_name', 'N/A')}")
        lines.append(f"入口测试文件: {entry_point}")
        if context:
            for key, value in context.items():
                if value:
                    lines.append(f"{key}: {value}")

        guidance = textwrap.dedent(
            f"""
            以下是一个可参考的模板，请据此生成适配当前项目的 YAML。注意需要根据提供的上下文命令进行调整，确保测试步骤执行 `pytest` 或流水线命令。

            示例模板：
            {DEFAULT_CI_TEMPLATE}

            需求：
            - 保留 on.push 与 on.pull_request 触发器。
            - 在运行测试步骤中使用命令: {context.get('test_command', 'pytest {entry_point}')}.
            - 如需收集制品，请上传 {context.get('artifacts_path', 'auto_llm/artifacts/')} 目录。
            """
        ).strip()

        user_prompt = "\n".join([part for part in (guidance, "\n".join(lines)) if part])
        return DEFAULT_CI_GUIDE, user_prompt
