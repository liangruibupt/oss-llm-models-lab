#!/usr/bin/env python3
"""Print a vLLM-vs-SGLang markdown table from bench/llm_bench.py JSON files.

Usage: python scripts/render_results.py results/qwen3.8-27b_g6e
Expects <dir>/<framework>/w1_1024_256.json and w2_8192_1024.json.
"""
import json
import os
import sys

d = sys.argv[1]
fws = [f for f in ("vllm", "sglang") if os.path.isdir(os.path.join(d, f))]
names = {"vllm": "vLLM", "sglang": "SGLang"}
print("| 负载 | 并发 | 框架 | 成功/总数 | TTFT p50 (ms) | TTFT p99 (ms) | TPOT p50 (ms) | TPOT p99 (ms) | 输出 tok/s | 请求/s |")
print("|---|---:|---|---:|---:|---:|---:|---:|---:|---:|")
for w, label in (("w1_1024_256", "W1 1024/256"), ("w2_8192_1024", "W2 8192/1024")):
    data = {}
    for f in fws:
        p = os.path.join(d, f, w + ".json")
        if os.path.exists(p):
            data[f] = {r["concurrency"]: r for r in json.load(open(p))["results"]}
    for c in (1, 8, 32, 64):
        for f in fws:
            r = data.get(f, {}).get(c)
            if not r:
                print(f"| {label} | {c} | {names[f]} | - | - | - | - | - | - | - |")
                continue
            fmt = lambda v, n=1: "-" if v is None else f"{v:,.{n}f}"
            print(f"| {label} | {c} | {names[f]} | {r['completed']}/{r['num_requests']} | {fmt(r['ttft_ms']['p50'])} | "
                  f"{fmt(r['ttft_ms']['p99'])} | {fmt(r['tpot_ms']['p50'], 2)} | {fmt(r['tpot_ms']['p99'], 2)} | "
                  f"{fmt(r['output_throughput_tok_s'])} | {fmt(r['request_throughput_rps'], 3)} |")
