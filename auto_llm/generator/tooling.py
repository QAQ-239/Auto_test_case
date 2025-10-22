"""
工具调用封装：用于管理文件写入、代码解析等与“工具”相关的操作。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


CODE_BLOCK_PATTERN = re.compile(
    r"```(?:python)?\s*(?P<code>.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def extract_code_block(llm_output: str) -> str:
    """
    从 LLM 输出中提取 Python 代码块。
    若不存在代码块，则返回原文本，交由上层处理。
    """
    match = CODE_BLOCK_PATTERN.search(llm_output)
    if not match:
        return llm_output.strip()
    return match.group("code").strip()


class WorkspaceManager:
    """管理脚本生成目录及文件落盘。"""

    def __init__(self, root: Path) -> None:
        self.root = root

    def write_file(self, relative_path: str, content: str, overwrite: bool = True) -> Path:
        target_path = self.root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists() and not overwrite:
            raise FileExistsError(f"{target_path} 已存在，且 overwrite=False")
        target_path.write_text(content, encoding="utf-8")
        return target_path

    def read_file(self, relative_path: str) -> Optional[str]:
        target_path = self.root / relative_path
        if not target_path.exists():
            return None
        return target_path.read_text(encoding="utf-8")

    def exists(self, relative_path: str) -> bool:
        return (self.root / relative_path).exists()
