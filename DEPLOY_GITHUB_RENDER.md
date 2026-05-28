# GitHub + Render 外网部署

这个项目包含 FastAPI 后端、SQLite 数据库和本地规则引擎，因此不能直接用 GitHub Pages 完整运行。推荐方式是：

1. GitHub 保存代码。
2. Render 从 GitHub 仓库自动部署 FastAPI。
3. SQLite 数据库放在 Render persistent disk。

## 准备 GitHub 仓库

在 GitHub 新建一个仓库，例如 `tutujin-bc-cds`，然后把本项目推送上去。

如果本机 `git` 可用：

```bash
cd /Users/chelseatian/Documents/Codex/2026-05-26/files-mentioned-by-the-user-finallized/breast-cancer-cds
git init
git add .
git commit -m "Deploy breast cancer CDS MVP"
git branch -M main
git remote add origin https://github.com/<你的用户名>/tutujin-bc-cds.git
git push -u origin main
```

## Render 部署

1. 打开 Render，选择 `New` -> `Blueprint`。
2. 连接上面的 GitHub 仓库。
3. Render 会读取根目录的 `render.yaml`。
4. 设置环境变量：
   - `CDS_SHARE_PASSWORD`: 外网访问密码。
   - `CDS_DATA_DIR`: 已在 `render.yaml` 中设置为 `/var/data`。
5. 部署完成后，Render 会给出一个 `https://...onrender.com/cds` 地址。

## 注意

- 这个系统仍只适合可信试用者，不建议录入真实患者身份信息。
- `CDS_SHARE_PASSWORD` 一定要设置，否则页面会直接公开。
- Render 免费实例可能会休眠，首次访问会慢一些。
- 如果需要多人长期使用，建议后续把 SQLite 换成 PostgreSQL，并加入正式账号权限。
