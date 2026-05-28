#!/bin/zsh
cd "$(dirname "$0")" || exit 1
BIN="./bin/cloudflared"
if [ ! -x "$BIN" ]; then
  echo "未找到 cloudflared。请先运行：安装外网分享工具.command"
  exit 1
fi
if [ ! -d "backend/.venv" ]; then
  echo "首次运行：正在创建 Python 环境..."
  cd backend || exit 1
  python -m venv .venv || exit 1
  .venv/bin/pip install -r requirements.txt || exit 1
  cd ..
fi
PASSWORD=$(LC_ALL=C tr -dc 'A-HJ-NP-Za-km-z2-9' </dev/urandom | head -c 10)
echo "正在启动乳腺癌 CDS 外网临时分享版..."
echo "访问用户名：doctor"
echo "访问密码：$PASSWORD"
echo "请只分享给可信试用者，避免录入真实患者身份信息。"
cd backend || exit 1
CDS_SHARE_PASSWORD="$PASSWORD" .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!
cd ..
sleep 2
echo "正在生成临时 HTTPS 链接，请等待下方 trycloudflare.com 地址..."
"$BIN" tunnel --url http://127.0.0.1:8000
kill "$SERVER_PID" 2>/dev/null
