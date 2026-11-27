# results/qwen3.8-27b_g6e

Raw output of the 2026-11-27 run (see [`docs/results/qwen3.8-27b_g6e.md`](../../docs/results/qwen3.8-27b_g6e.md)).

**Data loss notice:** the run's raw JSON files, server logs and VRAM traces were on the instance and were lost:
the copy-back `scp` and `scripts/teardown.py` were started at the same time, so the instance terminated mid-copy,
and the earlier local copy had been deleted to make room for the final one. What is here was transcribed from the
console output captured during the run:

| File | Content |
|---|---|
| `vllm/w1_1024_256.md`, `vllm/w2_8192_1024.md` | full markdown tables the harness printed for vLLM (all columns) |
| `sglang/console_summary.txt` | per-level summary lines for SGLang (output tok/s, TTFT p50, TPOT p50 only) |
| `versions.txt` | AMI, driver, images, framework/torch/CUDA versions, weight revision, peak VRAM |

No `.json` files exist for this run.
