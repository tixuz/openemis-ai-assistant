#!/bin/bash
SERVER_BIN="$HOME/ai_tools/llama.cpp/build/bin/llama-server"
MODEL_PATH="$HOME/ai_tools/deepseek-v2-lite.gguf"

# -t 8: использовать 8 ядер процессора
# --ctx-size 4096: уменьшим контекст до 4к для скорости (этого хватит для кода)
$SERVER_BIN -m $MODEL_PATH --port 8080 -t 8 --ctx-size 4096 --parallel 1