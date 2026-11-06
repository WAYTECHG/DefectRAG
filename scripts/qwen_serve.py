"""Serve Qwen (with or without the fine-tuned adapter) through an Ollama-compatible endpoint.

Run in the training environment (defectrag-ft):

    python -m scripts.qwen_serve --adapter experiments/qwen_lora_v1/adapter      # fine-tuned
    python -m scripts.qwen_serve --adapter none --port 11501                     # same base, no adapter

It implements only POST /api/generate, which is all the assistant's workflow uses, so
`python -m scripts.qwen_eval --url http://127.0.0.1:11500` measures it with the same
questions, retrieval and checks as before. Decoding is greedy (temperature 0), and the output is
forced to follow the same JSON schema the assistant sends, as Ollama does.
"""

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import torch
from lmformatenforcer import JsonSchemaParser
from lmformatenforcer.integrations.transformers import build_transformers_prefix_allowed_tokens_fn
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

BASE = "Qwen/Qwen2.5-3B-Instruct"


def load(adapter, base=BASE):
    tokenizer = AutoTokenizer.from_pretrained(base)
    quant = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        base, quantization_config=quant, device_map={"": 0}, dtype=torch.bfloat16
    )
    if adapter != "none":
        model = PeftModel.from_pretrained(model, adapter)
    return tokenizer, model.eval()


def make_handler(tokenizer, model, label):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the terminal readable
            pass

        def _send(self, status, payload):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self._send(200, {"status": "ok", "model": label})

        def do_POST(self):
            if self.path != "/api/generate":
                return self._send(404, {"error": "only /api/generate is implemented"})
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            chat = [{"role": "user", "content": body["prompt"]}]
            text = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(text, return_tensors="pt", add_special_tokens=False).to(model.device)
            kwargs = {}
            if isinstance(body.get("format"), dict):
                parser = JsonSchemaParser(body["format"])
                kwargs["prefix_allowed_tokens_fn"] = build_transformers_prefix_allowed_tokens_fn(tokenizer, parser)
            start = time.perf_counter()
            with torch.no_grad():
                out = model.generate(
                    **inputs, max_new_tokens=400, do_sample=False, pad_token_id=tokenizer.eos_token_id, **kwargs
                )
            answer = tokenizer.decode(out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
            print(f"{time.perf_counter() - start:5.1f}s  {answer[:110]!r}", flush=True)
            self._send(200, {"model": label, "response": answer, "done": True})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--adapter", default="experiments/qwen_lora_v1/adapter", help="folder, or 'none' for the base model"
    )
    parser.add_argument("--port", type=int, default=11500)
    parser.add_argument("--base", default=BASE, help="base model: Hugging Face id or a local folder")
    args = parser.parse_args()
    print("loading model ...", flush=True)
    tokenizer, model = load(args.adapter, args.base)
    label = "base" if args.adapter == "none" else "fine-tuned"
    print(f"ready: {label} model at http://127.0.0.1:{args.port}", flush=True)
    HTTPServer(("127.0.0.1", args.port), make_handler(tokenizer, model, label)).serve_forever()


if __name__ == "__main__":
    main()
