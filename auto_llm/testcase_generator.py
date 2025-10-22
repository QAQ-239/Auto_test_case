"""用户故事到标准化测试用例的生成工具"""

from __future__ import annotations

import json
import re
import textwrap
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .generator.llm_client import LLMClient


DEFAULT_TESTCASE_GUIDE = textwrap.dedent(
    """
    你是一名资深测试架构师，任务是根据给定的用户故事或需求文档生成结构化的测试用例。

    请严格按照以下 JSON 模板输出（禁止额外文本、禁止 Markdown 代码块、禁止注释）：
    {
      "suite_id": "",
      "suite_name": "",
      "description": "",
      "context": {
        "target": "",
        "language": "python",
        "framework": "pytest",
        "entry_point": "tests/test_generated.py"
      },
      "fixtures": [
        {
          "name": "",
          "type": "http",
          "details": {"base_url": ""}
        }
      ],
      "test_cases": [
        {
          "id": "",
          "title": "",
          "priority": "P0",
          "steps": ["步骤1", "步骤2"],
          "expected_result": ""
        }
      ]
    }

    约束：
    - 保证输出是单个合法 JSON（UTF-8），不得出现 ```, ```json 或其它多余包装。
    - 测试用例至少 3 条，覆盖正向、异常和边界场景；如需求涉及性能、安全、权限请额外补充相关用例。
    - 步骤需具体可执行，期望结果可验证，推荐使用中文表述。
    - 若用户故事未给出目标地址或入口文件，可使用占位值，如 http://placeholder/api、tests/test_generated.py。
    - 若存在鉴权、前置数据、依赖服务，请在 fixtures 中补充说明或给出准备步骤。
    - 如需求含糊，可在 description 增加假设说明，但仍需生成可执行的测试用例。
    """
).strip()

REPAIR_TESTCASE_GUIDE = textwrap.dedent(
    """
    你是一名严谨的测试文档整理专家。现有一段内容本应是符合 JSON 模板的测试套件描述，但其中存在语法错误或缺失。

    请修正它，使之成为合法、可解析的 JSON，且严格遵循以下结构：
    {
      "suite_id": "",
      "suite_name": "",
      "description": "",
      "context": {
        "target": "",
        "language": "",
        "framework": "",
        "entry_point": ""
      },
      "fixtures": [...],
      "test_cases": [...]
    }

    要求：
    - 仅输出修正后的 JSON，不要添加额外说明或 Markdown 代码块。
    - 允许在必要时补全缺失的引号、逗号或收尾符号，但不要杜撰与原意无关的字段。
    - 保持原有语义（测试步骤、期望结果等），仅做格式层面的修复。
    """
).strip()


@dataclass
class StoryMetadata:
    suite_id: Optional[str] = None
    suite_name: Optional[str] = None
    target: Optional[str] = None
    entry_point: Optional[str] = None
    fixtures_hint: Optional[str] = None


def build_user_prompt(story: str, metadata: Optional[StoryMetadata] = None) -> str:
    metadata = metadata or StoryMetadata()
    parts = ["【用户故事 / 需求文档】", story.strip()]

    hints = []
    if metadata.suite_id:
        hints.append(f"suite_id: {metadata.suite_id}")
    if metadata.suite_name:
        hints.append(f"suite_name: {metadata.suite_name}")
    if metadata.target:
        hints.append(f"目标系统地址: {metadata.target}")
    if metadata.entry_point:
        hints.append(f"入口文件: {metadata.entry_point}")
    if metadata.fixtures_hint:
        hints.append(f"fixtures 提示: {metadata.fixtures_hint}")

    if hints:
        parts.append("\n【生成补充说明】")
        parts.append("; ".join(hints))

    parts.append("\n【输出要求】请直接返回符合上述模板的 JSON，禁止多余说明。")
    return "\n".join(parts)


def _extract_json(text: str) -> str:
    candidate = text.strip()

    code_block = re.search(r"```(?:json)?\s*(.*?)```", candidate, re.DOTALL | re.IGNORECASE)
    if code_block:
        candidate = code_block.group(1).strip()

    if candidate.startswith("{") and candidate.endswith("}"):
        return candidate

    first = candidate.find("{")
    last = candidate.rfind("}")
    if first != -1 and last != -1 and first < last:
        return candidate[first : last + 1]

    raise ValueError("未能从模型输出中提取 JSON")


def _basic_json_sanitize(candidate: str) -> str:
    """
    针对常见的小错误进行快速修复：
    - 去除对象/数组末尾多余的逗号
    - 补齐未关闭的 } 或 ] 括号
    """
    text = candidate.strip()
    # 移除对象或数组结尾多余的逗号
    text = re.sub(r",\s*(?=[}\]])", "", text)

    # 统计括号并补齐
    stack: list[str] = []
    pairs = {"{": "}", "[": "]"}
    closing = {"}": "{", "]": "["}
    for ch in text:
        if ch in pairs:
            stack.append(ch)
        elif ch in closing:
            while stack and stack[-1] not in pairs:
                stack.pop()
            if stack and stack[-1] == closing[ch]:
                stack.pop()

    if stack:
        text += "".join(pairs[ch] for ch in reversed(stack))
    return text


def _decode_suite_response(
    response: str,
    client: LLMClient,
) -> Dict[str, Any]:
    json_text = _extract_json(response)
    data: Dict[str, Any] | None = None
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        sanitized = _basic_json_sanitize(json_text)
        if sanitized != json_text:
            try:
                data = json.loads(sanitized)
                json_text = sanitized
            except json.JSONDecodeError:
                data = None
        if data is None:
            repair_user_prompt = textwrap.dedent(
                f"""
                以下是模型返回但无法解析的内容，请在保持原意的基础上修复格式错误，使其成为合法 JSON：
                {response}

                请根据系统提示还原为结构正确的 JSON，并确保所有字段闭合、逗号和引号齐全。
                """
            ).strip()
            repair_response = client.generate_code(REPAIR_TESTCASE_GUIDE, repair_user_prompt)
            try:
                repair_json = _extract_json(repair_response)
            except ValueError as repair_extract_exc:
                raise ValueError(
                    f"解析模型输出失败: {exc}\n修复阶段未找到 JSON: {repair_extract_exc}"
                ) from repair_extract_exc
            try:
                data = json.loads(repair_json)
                json_text = repair_json
            except json.JSONDecodeError as repair_exc:
                raise ValueError(
                    f"解析模型输出失败: {exc}\n经过一次修复仍失败: {repair_exc}"
                ) from repair_exc

    if data is None:
        raise ValueError("生成结果为空，无法解析测试套件")

    if not isinstance(data, dict):
        raise ValueError(f"生成结果非 JSON 对象: {type(data)}")

    return data


def generate_test_suite(
    story: str,
    client: LLMClient,
    metadata: Optional[StoryMetadata] = None,
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    system_text = system_prompt or DEFAULT_TESTCASE_GUIDE
    user_text = build_user_prompt(story, metadata)

    attempts = 3
    base_prompt = user_text
    last_error: Optional[Exception] = None
    data: Dict[str, Any] | None = None

    for attempt in range(1, attempts + 1):
        current_prompt = base_prompt
        if attempt > 1:
            error_msg = str(last_error) if last_error else "输出无法解析"
            current_prompt = (
                base_prompt
                + "\n\n【注意】上一轮输出无法解析，请重新生成合法 JSON："
                f"{error_msg}\n请勿包含多余文字，确保所有字符串与括号闭合。"
            )

        response = client.generate_code(system_text, current_prompt)
        try:
            data = _decode_suite_response(response, client)
            break
        except ValueError as err:
            last_error = err
            data = None

    if data is None:
        raise ValueError(f"多次尝试生成测试套件仍失败：{last_error}") from last_error

    if "test_cases" not in data or not data["test_cases"]:
        raise ValueError("生成结果缺少 test_cases 或为空")

    context = data.setdefault("context", {})
    context.setdefault("language", "python")
    context.setdefault("framework", "pytest")
    if metadata and metadata.entry_point:
        context.setdefault("entry_point", metadata.entry_point)
    else:
        context.setdefault("entry_point", "tests/test_generated.py")
    if metadata and metadata.target:
        context.setdefault("target", metadata.target)
    if story:
        context.setdefault("origin_story", story.strip())

    fixtures = data.setdefault("fixtures", [])
    if not fixtures:
        fixtures.append(
            {
                "name": "client",
                "type": "http",
                "details": {"base_url": metadata.target if metadata and metadata.target else "http://placeholder/api"},
            }
        )

    return data
