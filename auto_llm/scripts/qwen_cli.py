#!/usr/bin/env python3
"""
本地 Qwen 推理包装脚本：
- 通过 stdin 接收 JSON（包含 system/user 提示）
- 使用 HuggingFace 加载模型生成回答
- 将生成文本通过 stdout 返回

用法示例：
python auto_exec/scripts/qwen_cli.py --model /home/.../qwen2.5 --max-new-tokens 1024
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qwen 本地推理 CLI")
    parser.add_argument("--model", required=True, help="模型目录或 HuggingFace 模型名称")
    parser.add_argument("--device", default="cuda", help="推理设备，如 cpu、cuda、cuda:0；默认自动选择")
    parser.add_argument("--dtype", default="bfloat16", help="权重精度，如 float16/bfloat16/auto")
    parser.add_argument("--max-new-tokens", type=int, default=1024, help="最大生成 token 数")
    parser.add_argument("--temperature", type=float, default=0.7, help="采样温度")
    parser.add_argument("--top-p", type=float, default=0.9, help="top-p 采样阈值")
    parser.add_argument("--no-chat-template", action="store_true", help="禁用 tokenizer chat_template，使用简单拼接")
    return parser.parse_args()


def resolve_dtype(dtype_str: str):
    mapping = {
        "float16": torch.float16,
        "fp16": torch.float16,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
        "float32": torch.float32,
    }
    return mapping.get(dtype_str.lower())


def load_model(args: argparse.Namespace):
    dtype = resolve_dtype(args.dtype) if args.dtype else None
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True,
    )

    model_kwargs: Dict[str, Any] = {
        "trust_remote_code": True,
    }
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype
    if args.device is None:
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        **model_kwargs,
    )

    if args.device is not None:
        model = model.to(args.device)

    model.eval()
    return tokenizer, model


def build_prompt(tokenizer: AutoTokenizer, system_msg: str, user_msg: str, disable_chat_template: bool) -> str:
    if disable_chat_template:
        return f"{system_msg.strip()}\n\n{user_msg.strip()}".strip()

    messages: List[Dict[str, str]] = []
    if system_msg:
        messages.append({"role": "system", "content": system_msg})
    messages.append({"role": "user", "content": user_msg})

    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        return f"{system_msg.strip()}\n\n{user_msg.strip()}".strip()


def main() -> None:
    args = parse_args()
    tokenizer, model = load_model(args)

    payload_raw = sys.stdin.read()
    if not payload_raw:
        print("[qwen_cli] 未收到输入 payload", file=sys.stderr)
        raise SystemExit(1)

    payload = json.loads(payload_raw)
    system_prompt = payload.get("system", "")
    user_prompt = payload.get("user", "")

    prompt_text = build_prompt(tokenizer, system_prompt, user_prompt, args.no_chat_template)
    inputs = tokenizer(prompt_text, return_tensors="pt")

    if args.device and args.device.startswith("cuda"):
        inputs = {k: v.to(args.device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            do_sample=True,
        )

    generated = output_ids[0][inputs["input_ids"].shape[-1]:]
    text = tokenizer.decode(generated, skip_special_tokens=True)

    sys.stdout.write(text.strip())


if __name__ == "__main__":
    main()
