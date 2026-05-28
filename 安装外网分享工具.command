#!/bin/zsh
cd "$(dirname "$0")" || exit 1
mkdir -p bin
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
  URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
else
  URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
fi
echo "正在下载 Cloudflare Tunnel 工具..."
curl -L "$URL" -o /tmp/cloudflared.tgz || exit 1
tar -xzf /tmp/cloudflared.tgz -C bin || exit 1
chmod +x bin/cloudflared
echo "安装完成。现在可以双击：启动乳腺癌CDS-外网临时分享.command"
