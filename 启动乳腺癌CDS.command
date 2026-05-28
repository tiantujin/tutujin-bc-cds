#!/bin/zsh
cd "$(dirname "$0")/backend" || exit 1
if [ ! -d ".venv" ]; then
  echo "首次运行：正在创建 Python 环境..."
  python -m venv .venv || exit 1
  .venv/bin/pip install -r requirements.txt || exit 1
fi
echo "正在启动乳腺癌 CDS 本地版..."
echo "页面地址：http://127.0.0.1:8000/cds"
(sleep 2 && open "http://127.0.0.1:8000/cds") &
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
