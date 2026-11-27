#!/usr/bin/env bash
# RUN ON THE GPU BOX: bash bench_qwen27b.sh vllm|sglang
# vLLM: Rust frontend off (chat-template render error), --max-num-seqs 64 (mamba blocks).
# Starts the server container, samples VRAM, runs W1 (1024/256) and W2 (8192/1024)
# at concurrency 1/8/32/64, stops the container.
# W1: 4 x concurrency requests (min 16). W2: 1 x concurrency (min 8) to fit the 3 h cap.
set -uo pipefail
FW=$1
OUT=$HOME/run/$FW; mkdir -p $OUT
HF=$HOME/hf
MODEL=Qwen/Qwen3.8-27B-FP8
RPC=${RPC:-4}
if [ "$FW" = vllm ]; then
  PORT=8000
  docker run -d --name srv --gpus all --ipc=host -p 8000:8000 \
    -v $HF:/root/.cache/huggingface -v $HOME/vllm-cache:/root/.cache/vllm -e HF_HUB_OFFLINE=1 -e VLLM_USE_RUST_FRONTEND=${VLLM_RUST:-0} \
    ${VLLM_IMG:-vllm/vllm-openai:qwen38} $MODEL \
      --tensor-parallel-size 1 \
      --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3 \
      --language-model-only \
      --max-model-len 16384 --gpu-memory-utilization 0.92 --max-num-seqs 64 > $OUT/container_id 2>&1
else
  PORT=30000
  docker run -d --name srv --gpus all --ipc=host --shm-size 32g -p 30000:30000 \
    -v $HF:/root/.cache/huggingface -e HF_HUB_OFFLINE=1 \
    lmsysorg/sglang:latest sglang serve \
      --trust-remote-code --model-path $MODEL \
      --kv-cache-dtype fp8_e4m3 --mem-fraction-static ${SGL_MEM:-0.88} --attention-backend flashinfer \
      --chunked-prefill-size 8192 --max-prefill-tokens 8192 --cuda-graph-backend-prefill disabled \
      --reasoning-parser qwen3 --tool-call-parser qwen3_coder \
      --host 0.0.0.0 --port 30000 \
      --mamba-ssm-dtype float32 --max-running-requests ${SGL_MAXREQ:-32} --disable-radix-cache \
      --context-length 16384 > $OUT/container_id 2>&1
  # Deviations from the H200 cookbook command (OOM, then a 4-request mamba-state cap on the
  # 48 GB L40S, see docs/results/qwen3.8-27b_g6e.md): chunked/max prefill 32768->8192,
  # prefill CUDA graph disabled, extra_buffer_lazy mamba strategy dropped, radix cache disabled
  # (one mamba state per request; the benchmark has no prefix reuse), max-running-requests 32
  # (64 leaves no memory for KV cache), mem-fraction 0.85->0.88.
fi
( while true; do nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits >> $OUT/vram_mib.txt; sleep 2; done ) &
SAMPLER=$!
echo "start $(date -u +%T)" > $OUT/status
ok=0
for i in $(seq 1 180); do   # up to 30 min to come up
  if curl -sf http://127.0.0.1:$PORT/v1/models > $OUT/models.json; then ok=1; break; fi
  if [ "$(docker inspect -f '{{.State.Running}}' srv 2>/dev/null)" != "true" ]; then break; fi
  sleep 10
done
docker logs srv > $OUT/server_boot.log 2>&1
if [ $ok != 1 ]; then
  echo "SERVER_FAILED $(date -u +%T)" >> $OUT/status
  docker rm -f srv >/dev/null 2>&1; kill $SAMPLER; exit 1
fi
echo "ready $(date -u +%T)" >> $OUT/status
B=$HOME/llm_bench.py
python3 $B --base-url http://127.0.0.1:$PORT/v1 --model $MODEL --input-len 1024 --output-len 256 \
  --concurrency 1,8,32,64 --requests-per-concurrency $RPC \
  --label "$FW / g6e.xlarge (1x L40S 48GB) / Qwen3.8-27B-FP8 / W1 1024-256" --out $OUT/w1_1024_256 > $OUT/w1.log 2>&1
echo "w1 rc=$? $(date -u +%T)" >> $OUT/status
python3 $B --base-url http://127.0.0.1:$PORT/v1 --model $MODEL --input-len 8192 --output-len 1024 \
  --concurrency 1,8,32,64 --requests-per-concurrency ${RPC_W2:-1} --min-requests ${MIN_W2:-8} \
  --label "$FW / g6e.xlarge (1x L40S 48GB) / Qwen3.8-27B-FP8 / W2 8192-1024" --out $OUT/w2_8192_1024 > $OUT/w2.log 2>&1
echo "w2 rc=$? $(date -u +%T)" >> $OUT/status
docker logs srv > $OUT/server.log 2>&1
docker rm -f srv >/dev/null 2>&1
kill $SAMPLER
sort -n $OUT/vram_mib.txt | tail -1 > $OUT/vram_peak_mib.txt
echo "BENCH_DONE $(date -u +%T)" >> $OUT/status
