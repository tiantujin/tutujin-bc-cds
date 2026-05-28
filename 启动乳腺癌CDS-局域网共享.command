#!/bin/zsh
cd "$(dirname "$0")/backend" || exit 1
if [ ! -d ".venv" ]; then
  echo "首次运行：正在创建 Python 环境..."
  python -m venv .venv || exit 1
  .venv/bin/pip install -r requirements.txt || exit 1
fi
IP=$(ifconfig en0 | awk '/inet / {print $2; exit}')
if [ -z "$IP" ]; then
  IP="127.0.0.1"
fi
echo "正在启动乳腺癌 CDS 局域网共享版..."
echo "本机访问：http://127.0.0.1:8000/cds"
echo "同一 Wi-Fi 访问：http://$IP:8000/cds"
echo "请只分享给可信试用者，避免录入真实患者身份信息。"
(sleep 2 && open "http://127.0.0.1:8000/cds") &
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
