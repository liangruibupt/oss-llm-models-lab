#!/usr/bin/env bash
# RUN ON THE GPU BOX. Pull framework images + official FP8 weights, record versions.
set -uo pipefail
OUT=$HOME/run; mkdir -p $OUT /opt/dlami/nvme 2>/dev/null || true
HF=$HOME/hf; mkdir -p $HF
VLLM_IMG=vllm/vllm-openai:qwen38
SGL_IMG=lmsysorg/sglang:latest
MODEL=Qwen/Qwen3.8-27B-FP8
REV=c3a462cc3d38cf351f3b26cbd763469eeb74ef81
{
  echo "date: $(date -u +%FT%TZ)"
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  nvidia-smi | grep -o 'CUDA UMD Version: [0-9.]*'
  docker --version
  uname -r; lsb_release -ds
} > $OUT/host_versions.txt 2>&1
echo "pull start $(date -u +%T)" >> $OUT/setup.log
docker pull -q $VLLM_IMG >> $OUT/setup.log 2>&1 &
docker pull -q $SGL_IMG  >> $OUT/setup.log 2>&1 &
wait
echo "pull done $(date -u +%T)" >> $OUT/setup.log
docker run --rm --entrypoint python3 -v $HF:/root/.cache/huggingface $VLLM_IMG -c \
  "from huggingface_hub import snapshot_download; print(snapshot_download('$MODEL', revision='$REV', max_workers=16))" >> $OUT/setup.log 2>&1
echo "weights done $(date -u +%T) rc=$?" >> $OUT/setup.log
# snapshot_download(revision=<sha>) does not write refs/main; servers started with
# HF_HUB_OFFLINE=1 then fail with LocalEntryNotFoundError. Point main at the pinned sha.
sudo mkdir -p $HF/hub/models--Qwen--Qwen3.8-27B-FP8/refs
echo -n $REV | sudo tee $HF/hub/models--Qwen--Qwen3.8-27B-FP8/refs/main >/dev/null
for img in $VLLM_IMG $SGL_IMG; do
  echo "== $img $(docker image inspect --format '{{index .RepoDigests 0}}' $img)"
  docker run --rm --gpus all --entrypoint python3 $img -c "import torch,importlib;print('torch',torch.__version__,'cuda',torch.version.cuda);
for m in ('vllm','sglang','flashinfer','transformers'):
  try: print(m, importlib.import_module(m).__version__)
  except Exception as e: pass
import sys;print('python',sys.version.split()[0])"
done > $OUT/image_versions.txt 2>&1
echo SETUP_DONE >> $OUT/setup.log
