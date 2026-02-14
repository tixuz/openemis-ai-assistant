#!/bin/bash
SERVER_BIN="$HOME/ai_tools/llama.cpp/build/bin/llama-server"
MODEL_PATH="$HOME/ai_tools/deepseek-coder-1.3b-instruct.Q4_K_M.gguf"

# Оптимизация для скорости на CPU:
# Increased context size to 4096 to handle system prompt + examples + user input
$SERVER_BIN -m $MODEL_PATH --port 8080 -t 2 -ngl 0 --ctx-size 4096 -n 512 --mlock