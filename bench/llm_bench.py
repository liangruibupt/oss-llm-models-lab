#!/usr/bin/env python3
"""Framework-agnostic load test for any OpenAI-compatible LLM endpoint.

Measures, per concurrency level:
  * TTFT  - time to first streamed token (ms)
  * TPOT  - (end-to-end latency - TTFT) / (output tokens - 1)  (ms)
  * ITL   - gap between consecutive streamed chunks (ms)
  * output token throughput (tok/s, whole run) and request throughput (req/s)

Works against SGLang, vLLM, vLLM-Omni (text modality), TrnRT or any server that
implements ``/v1/chat/completions`` or ``/v1/completions`` with SSE streaming.
Standard library only (Python 3.10+), so it runs on a fresh instance.

Example:
    python bench/llm_bench.py --base-url http://127.0.0.1:8000/v1 \
        --model openai/gpt-oss-120b --input-len 1024 --output-len 256 \
        --concurrency 1,8,32,64 --out results/gpt-oss-120b_vllm_p5
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import os
import platform
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from typing import Iterable

# A fixed, deterministic word pool. Common English words are usually one token
# each in modern BPE vocabularies, so N words ~= N tokens. The real prompt
# length is read back from the server's `usage` block when it reports one.
_WORDS = (
    "time person year way day thing man world life hand part child eye woman "
    "place work week case point number group problem fact water room mother "
    "area money story month lot right study book job word business issue side "
    "kind head house service friend father power hour game line end member law "
    "car city name team minute idea kid body back parent face others level "
    "office door health art war history party result change morning reason"
).split()


def build_prompt(n_tokens: int, seed: int, tokenizer=None) -> str:
    """Return a prompt of roughly ``n_tokens`` tokens (exact if a tokenizer is given)."""
    if n_tokens <= 0:
        raise ValueError("input length must be positive")
    words = [_WORDS[(seed * 7 + i * 13) % len(_WORDS)] for i in range(n_tokens)]
    text = " ".join(words)
    if tokenizer is None:
        return text
    ids = tokenizer.encode(text, add_special_tokens=False)
    while len(ids) < n_tokens:  # pad if the tokenizer merged words
        ids = ids + ids[: n_tokens - len(ids)]
    return tokenizer.decode(ids[:n_tokens])


@dataclass
class RequestResult:
    ok: bool
    ttft_ms: float | None = None
    e2e_ms: float | None = None
    output_tokens: int = 0
    prompt_tokens: int | None = None
    itl_ms: list[float] = field(default_factory=list)
    error: str | None = None

    @property
    def tpot_ms(self) -> float | None:
        if not self.ok or self.ttft_ms is None or self.e2e_ms is None or self.output_tokens < 2:
            return None
        return (self.e2e_ms - self.ttft_ms) / (self.output_tokens - 1)


def percentile(values: Iterable[float], pct: float) -> float | None:
    """Linear-interpolated percentile (same convention as numpy's default)."""
    data = sorted(values)
    if not data:
        return None
    if len(data) == 1:
        return data[0]
    k = (len(data) - 1) * pct / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return data[int(k)]
    return data[lo] + (data[hi] - data[lo]) * (k - lo)


def _summary(values: list[float]) -> dict:
    if not values:
        return {"mean": None, "p50": None, "p90": None, "p99": None}
    return {
        "mean": statistics.fmean(values),
        "p50": percentile(values, 50),
        "p90": percentile(values, 90),
        "p99": percentile(values, 99),
    }


def _iter_sse(resp) -> Iterable[str]:
    """Yield the data payload of each SSE event from an HTTP response."""
    for raw in resp:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue
        yield line[len("data:"):].strip()


def send_request(cfg: argparse.Namespace, prompt: str) -> RequestResult:
    """Send one streaming request and time it."""
    url = cfg.base_url.rstrip("/") + ("/chat/completions" if cfg.endpoint == "chat" else "/completions")
    body: dict = {
        "model": cfg.model,
        "max_tokens": cfg.output_len,
        "temperature": cfg.temperature,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if cfg.endpoint == "chat":
        body["messages"] = [{"role": "user", "content": prompt}]
    else:
        body["prompt"] = prompt
    if cfg.ignore_eos:
        # vLLM and SGLang extensions: force exactly output_len tokens.
        body["ignore_eos"] = True
        body["min_tokens"] = cfg.output_len
    if cfg.extra_body:
        body.update(json.loads(cfg.extra_body))

    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
    api_key = os.environ.get(cfg.api_key_env, "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")

    start = time.perf_counter()
    first = last = None
    chunks = 0
    usage_completion = usage_prompt = None
    itl: list[float] = []
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout) as resp:
            for data in _iter_sse(resp):
                if data == "[DONE]":
                    break
                event = json.loads(data)
                if event.get("usage"):
                    usage_completion = event["usage"].get("completion_tokens", usage_completion)
                    usage_prompt = event["usage"].get("prompt_tokens", usage_prompt)
                has_text = False
                for ch in event.get("choices") or []:
                    delta = ch.get("delta") or {}
                    piece = (
                        delta.get("content")
                        or delta.get("reasoning_content")
                        or delta.get("reasoning")
                        or ch.get("text")
                    )
                    if piece:
                        has_text = True
                if not has_text:
                    continue
                now = time.perf_counter()
                if first is None:
                    first = now
                else:
                    itl.append((now - last) * 1000.0)
                last = now
                chunks += 1
    except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError, OSError) as exc:
        return RequestResult(ok=False, error=f"{type(exc).__name__}: {exc}")
    end = time.perf_counter()
    if first is None:
        return RequestResult(ok=False, error="no tokens streamed")
    out_tokens = usage_completion if usage_completion is not None else chunks
    return RequestResult(
        ok=True,
        ttft_ms=(first - start) * 1000.0,
        e2e_ms=(end - start) * 1000.0,
        output_tokens=int(out_tokens),
        prompt_tokens=usage_prompt,
        itl_ms=itl,
    )


def run_level(cfg: argparse.Namespace, concurrency: int, tokenizer=None) -> dict:
    """Run ``num_requests`` requests with at most ``concurrency`` in flight."""
    n = cfg.num_requests or max(concurrency * cfg.requests_per_concurrency, cfg.min_requests)
    prompts = [build_prompt(cfg.input_len, seed=i + concurrency * 1000, tokenizer=tokenizer) for i in range(n)]

    if cfg.warmup:
        with cf.ThreadPoolExecutor(max_workers=min(concurrency, cfg.warmup)) as pool:
            list(pool.map(lambda p: send_request(cfg, p), prompts[: cfg.warmup]))

    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(lambda p: send_request(cfg, p), prompts))
    duration = time.perf_counter() - t0

    ok = [r for r in results if r.ok]
    total_out = sum(r.output_tokens for r in ok)
    prompt_lens = [r.prompt_tokens for r in ok if r.prompt_tokens is not None]
    itl_all = [x for r in ok for x in r.itl_ms]
    return {
        "concurrency": concurrency,
        "num_requests": n,
        "completed": len(ok),
        "failed": len(results) - len(ok),
        "errors": sorted({r.error for r in results if r.error})[:5],
        "duration_s": duration,
        "request_throughput_rps": len(ok) / duration if duration > 0 else None,
        "output_throughput_tok_s": total_out / duration if duration > 0 else None,
        "mean_prompt_tokens": statistics.fmean(prompt_lens) if prompt_lens else None,
        "mean_output_tokens": statistics.fmean([r.output_tokens for r in ok]) if ok else None,
        "ttft_ms": _summary([r.ttft_ms for r in ok]),
        "tpot_ms": _summary([r.tpot_ms for r in ok if r.tpot_ms is not None]),
        "itl_ms": _summary(itl_all),
        "e2e_ms": _summary([r.e2e_ms for r in ok]),
    }


def _fmt(v, nd=1):
    return "-" if v is None else f"{v:.{nd}f}"


def to_markdown(report: dict) -> str:
    m = report["meta"]
    lines = [
        f"# Benchmark: `{m['model']}` @ {m['base_url']}",
        "",
        f"- label: {m.get('label') or '-'}",
        f"- endpoint: {m['endpoint']}, input_len: {m['input_len']}, output_len: {m['output_len']}, "
        f"ignore_eos: {m['ignore_eos']}, started: {m['started_utc']}",
        "",
        "| Concurrency | OK/Total | Req/s | Output tok/s | TTFT p50 (ms) | TTFT p99 (ms) | "
        "TPOT p50 (ms) | TPOT p99 (ms) | ITL p50 (ms) | ITL p99 (ms) | Mean in/out tok |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in report["results"]:
        lines.append(
            f"| {r['concurrency']} | {r['completed']}/{r['num_requests']} | {_fmt(r['request_throughput_rps'], 2)} | "
            f"{_fmt(r['output_throughput_tok_s'])} | {_fmt(r['ttft_ms']['p50'])} | {_fmt(r['ttft_ms']['p99'])} | "
            f"{_fmt(r['tpot_ms']['p50'], 2)} | {_fmt(r['tpot_ms']['p99'], 2)} | {_fmt(r['itl_ms']['p50'], 2)} | "
            f"{_fmt(r['itl_ms']['p99'], 2)} | {_fmt(r['mean_prompt_tokens'], 0)}/{_fmt(r['mean_output_tokens'], 0)} |"
        )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-url", required=True, help="e.g. http://127.0.0.1:8000/v1")
    p.add_argument("--model", required=True, help="model name the server expects")
    p.add_argument("--endpoint", choices=["chat", "completions"], default="chat")
    p.add_argument("--input-len", type=int, default=1024, help="prompt length in tokens (approximate without --tokenizer)")
    p.add_argument("--output-len", type=int, default=256, help="max_tokens per request")
    p.add_argument("--concurrency", default="1,8,32,64", help="comma-separated concurrency levels")
    p.add_argument("--num-requests", type=int, default=0, help="requests per level (0 = auto)")
    p.add_argument("--requests-per-concurrency", type=int, default=4, help="auto mode: requests = concurrency x this")
    p.add_argument("--min-requests", type=int, default=16, help="auto mode lower bound")
    p.add_argument("--warmup", type=int, default=2, help="warm-up requests per level (not timed)")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--no-ignore-eos", dest="ignore_eos", action="store_false",
                   help="do not send ignore_eos/min_tokens (use for servers that reject them)")
    p.add_argument("--extra-body", default="", help="JSON merged into every request body")
    p.add_argument("--api-key-env", default="OPENAI_API_KEY", help="env var holding the bearer token (optional)")
    p.add_argument("--tokenizer", default="", help="HF tokenizer id for exact prompt length (needs transformers)")
    p.add_argument("--timeout", type=float, default=600.0)
    p.add_argument("--label", default="", help="free text, e.g. 'vLLM 0.34 / p5.48xlarge / FP8 / TP8'")
    p.add_argument("--out", default="", help="output path prefix; writes <out>.json and <out>.md")
    args = p.parse_args(argv)
    args.concurrency_levels = [int(x) for x in str(args.concurrency).split(",") if x.strip()]
    if not args.concurrency_levels or min(args.concurrency_levels) < 1:
        p.error("--concurrency needs positive integers")
    return args


def main(argv: list[str] | None = None) -> int:
    cfg = parse_args(argv)
    tokenizer = None
    if cfg.tokenizer:
        from transformers import AutoTokenizer  # optional dependency

        tokenizer = AutoTokenizer.from_pretrained(cfg.tokenizer)
    report = {
        "meta": {
            "base_url": cfg.base_url,
            "model": cfg.model,
            "endpoint": cfg.endpoint,
            "input_len": cfg.input_len,
            "output_len": cfg.output_len,
            "ignore_eos": cfg.ignore_eos,
            "label": cfg.label,
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "client": {"python": platform.python_version()},
        },
        "results": [],
    }
    for c in cfg.concurrency_levels:
        res = run_level(cfg, c, tokenizer)
        report["results"].append(res)
        print(
            f"[c={c}] ok={res['completed']}/{res['num_requests']} out_tok/s={_fmt(res['output_throughput_tok_s'])} "
            f"ttft_p50={_fmt(res['ttft_ms']['p50'])}ms tpot_p50={_fmt(res['tpot_ms']['p50'], 2)}ms",
            file=sys.stderr,
        )
    md = to_markdown(report)
    if cfg.out:
        os.makedirs(os.path.dirname(os.path.abspath(cfg.out)), exist_ok=True)
        with open(cfg.out + ".json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        with open(cfg.out + ".md", "w", encoding="utf-8") as f:
            f.write(md)
    print(md)
    failed = sum(r["failed"] for r in report["results"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
