#!/usr/bin/env python3
"""
DeepSeek Coder 本地推理 HTTP 服务。

特性：
- 启动时常驻加载模型，仅首次初始化较耗时。
- 暴露一个 /generate POST 接口，接受 system/user 文本，返回模型生成结果。
- 默认监听 0.0.0.0:8010，可通过参数自定义。

依赖：
    pip install modelscope fastapi uvicorn torch

启动示例：
    python auto_llm/scripts/deepseek_server.py \
        --model deepseek-ai/deepseek-coder-6.7b-instruct \
        --host 0.0.0.0 --port 8010

调用示例（HTTP）：
    curl -X POST http://localhost:8010/generate \
         -H "Content-Type: application/json" \
         -d '{"system": "你是资深测试工程师", "user": "请生成冒烟测试用例骨架"}'
"""
from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

import torch
from fastapi import FastAPI
from modelscope import AutoModelForCausalLM, AutoTokenizer
from pydantic import BaseModel
import uvicorn


class GenerateRequest(BaseModel):
    system: Optional[str] = ""
    user: str
    max_new_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_k: Optional[int] = 40
    top_p: Optional[float] = 0.9
    use_chat_template: Optional[bool] = True


class GenerateResponse(BaseModel):
    output: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DeepSeek 本地推理 HTTP 服务")
    parser.add_argument(
        "--model",
        default =  "/home/Newdisk2/aofanyu/deepseek-code-7b",
        help="模型名称或本地目录，例如 deepseek-ai/deepseek-coder-6.7b-instruct",
    )
    parser.add_argument("--host", default="0.0.0.0", help="HTTP 服务监听地址，默认 0.0.0.0")
    parser.add_argument("--port", type=int, default=8010, help="HTTP 服务监听端口，默认 8010")
    parser.add_argument("--device", default="cuda", help="推理设备，如 cpu、cuda、cuda:0；默认 cuda")
    parser.add_argument(
        "--dtype",
        default="bfloat16",
        help="加载模型所用精度，可选 float16/bfloat16/float32/auto，默认 bfloat16",
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


def load_model(model_name: str, device: Optional[str], dtype_str: Optional[str]):
    dtype = resolve_dtype(dtype_str)

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
    )

    model_kwargs: Dict[str, Any] = {
        "trust_remote_code": True,
    }
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype
    if not device:
        model_kwargs["device_map"] = "auto"

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        **model_kwargs,
    )

    if device:
        model = model.to(device)

    model.eval()
    return tokenizer, model


def build_inputs(
    tokenizer,
    system_text: str,
    user_text: str,
    use_chat_template: bool,
    device,
):
    if use_chat_template:
        messages: List[Dict[str, str]] = []
        if system_text:
            messages.append({"role": "system", "content": system_text})
        messages.append({"role": "user", "content": user_text})
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        )
        inputs = {"input_ids": inputs}
    else:
        prompt = f"{system_text.strip()}\n\n{user_text.strip()}".strip()
        inputs = tokenizer(prompt, return_tensors="pt")

    inputs = {k: v.to(device) for k, v in inputs.items()}
    return inputs


def create_app(tokenizer, model) -> FastAPI:
    app = FastAPI(title="DeepSeek Coder Service", version="1.0.0")
    model_device = next(model.parameters()).device

    @app.post("/generate", response_model=GenerateResponse)
    def generate(req: GenerateRequest) -> GenerateResponse:
        inputs = build_inputs(
            tokenizer=tokenizer,
            system_text=req.system or "",
            user_text=req.user,
            use_chat_template=req.use_chat_template,
            device=model_device,
        )

        gen_kwargs = {
            "max_new_tokens": req.max_new_tokens or 512,
            "do_sample": True,
            "temperature": req.temperature if req.temperature is not None else 0.7,
            "top_p": req.top_p if req.top_p is not None else 0.9,
            "top_k": req.top_k if req.top_k is not None else 40,
            "eos_token_id": tokenizer.eos_token_id,
        }

        with torch.no_grad():
            output_ids = model.generate(**inputs, **gen_kwargs)

        input_len = inputs["input_ids"].shape[-1]
        generated = output_ids[0][input_len:]
        text = tokenizer.decode(generated, skip_special_tokens=True)
        return GenerateResponse(output=text.strip())

    @app.get("/")
    def health() -> Dict[str, str]:
        return {"status": "ok", "model": str(model.name_or_path)}

    return app


def main() -> None:
    args = parse_args()
    tokenizer, model = load_model(args.model, args.device, args.dtype)
    app = create_app(tokenizer, model)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
