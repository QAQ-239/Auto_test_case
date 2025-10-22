#!/usr/bin/env python3
"""
DeepSeek Coder 本地推理包装脚本：
- 通过 stdin 接收 JSON（包含 system/user 提示）
- 使用 ModelScope + Transformers 加载 deepseek-ai/deepseek-coder-* 模型进行生成
- 将生成文本通过 stdout 返回

用法示例：
python auto_llm/scripts/deepseek_cli.py --model deepseek-ai/deepseek-coder-6.7b-instruct
python auto_llm/scripts/deepseek_cli.py --model /path/to/local-model --device cuda:0 --max-new-tokens 800
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

import torch
from modelscope import AutoModelForCausalLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DeepSeek 本地推理 CLI")
    parser.add_argument(
        "--model",
        required=True,
        help="模型名称或本地目录，例如 deepseek-ai/deepseek-coder-6.7b-instruct",
    )
    parser.add_argument("--device", default="cuda", help="推理设备，如 cpu、cuda、cuda:0（默认 cuda）")
    parser.add_argument(
        "--dtype",
        default="bfloat16",
        help="加载模型所用精度，可选 float16/bfloat16/float32/auto，默认 bfloat16",
    )
    parser.add_argument("--max-new-tokens", type=int, default=512, help="最大生成 token 数，默认 512")
    parser.add_argument("--temperature", type=float, default=0.7, help="采样温度，默认 0.7")
    parser.add_argument("--top-k", type=int, default=40, help="top-k 采样阈值，默认 40")
    parser.add_argument("--top-p", type=float, default=0.9, help="top-p 采样阈值，默认 0.9")
    parser.add_argument(
        "--no-chat-template",
        action="store_true",
        help="禁用 tokenizer.apply_chat_template，改用简单拼接 system 和 user 文本",
    )
    return parser.parse_args()


def resolve_dtype(dtype_str: str):
    mapping = {
        "float16": torch.float16,
        "fp16": torch.float16,
        "half": torch.float16,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
        "float32": torch.float32,
        "fp32": torch.float32,
    }
    return mapping.get((dtype_str or "").lower())


def load_model_and_tokenizer(args: argparse.Namespace):
    dtype = resolve_dtype(args.dtype)

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

    if args.device:
        model = model.to(args.device)

    model.eval()
    return tokenizer, model


def build_inputs(
    tokenizer: AutoTokenizer,
    system_msg: str,
    user_msg: str,
    disable_template: bool,
    device: torch.device | str | None,
):
    if disable_template:
        prompt = f"{system_msg.strip()}\n\n{user_msg.strip()}".strip()
        encoded = tokenizer(prompt, return_tensors="pt")
    else:
        messages: List[Dict[str, str]] = []
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": user_msg})
        encoded = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        )

    if isinstance(encoded, torch.Tensor):
        encoded = {"input_ids": encoded}

    if device:
        encoded = {k: v.to(device) for k, v in encoded.items()}
    return encoded


def main() -> None:
    args = parse_args()
    tokenizer, model = load_model_and_tokenizer(args)
    model_device = next(model.parameters()).device

    payload_raw = sys.stdin.read()
    if not payload_raw:
        print("[deepseek_cli] 未收到输入 payload", file=sys.stderr)
        raise SystemExit(1)

    payload = json.loads(payload_raw)
    system_prompt = payload.get("system", "") or ""
    user_prompt = payload.get("user", "") or ""

    inputs = build_inputs(
        tokenizer=tokenizer,
        system_msg=system_prompt,
        user_msg=user_prompt,
        disable_template=args.no_chat_template,
        device=model_device,
    )

    gen_kwargs = {
        "max_new_tokens": args.max_new_tokens,
        "do_sample": True,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "eos_token_id": tokenizer.eos_token_id,
    }

    with torch.no_grad():
        output_ids = model.generate(**inputs, **gen_kwargs)

    input_length = inputs["input_ids"].shape[-1]
    generated = output_ids[0][input_length:]
    text = tokenizer.decode(generated, skip_special_tokens=True)

    sys.stdout.write(text.strip())


if __name__ == "__main__":
    main()
