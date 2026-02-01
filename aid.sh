#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 在脚本所在目录中运行d2v.py
python "$SCRIPT_DIR/aid.py" "$@"