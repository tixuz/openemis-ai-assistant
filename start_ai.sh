#!/bin/bash
SERVER_BIN="$HOME/ai_tools/llama.cpp/build/bin/llama-server"
MODEL_PATH="$HOME/ai_tools/deepseek-coder-1.3b-instruct.Q4_K_M.gguf"

# Оптимизация для скорости на CPU:
# --parallel removed to get full 2048 context per request
$SERVER_BIN -m $MODEL_PATH --port 8080 -t 2 -ngl 0 --ctx-size 2048 -n 512 --mlock