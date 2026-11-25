#!/usr/bin/env bash
set -euo pipefail
source_dir=${1:?Pass the patched llama.cpp directory}
build_dir=${2:?Pass the build directory}
cmake -S "$source_dir" -B "$build_dir" -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DGGML_CUDA=ON -DGGML_NATIVE=OFF -DCMAKE_CUDA_ARCHITECTURES='80-real;120-real' -DLLAMA_BUILD_TESTS=ON
cmake --build "$build_dir" --parallel 5 --target llama-completion llama-bench llama-perplexity llama-mtmd-cli llama-quantize llama-server inkling-logits
