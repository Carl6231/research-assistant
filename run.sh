#!/bin/bash

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
else
    echo "虚拟环境不存在，使用系统Python..."
fi

# 检查是否安装了依赖
if ! python -c "import streamlit" 2>/dev/null; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

# 运行Streamlit应用
echo "启动Streamlit应用..."
streamlit run main.py --server.port 8501 --server.headless false