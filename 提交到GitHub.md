# 将项目提交到 GitHub

仓库地址：https://github.com/13371/-ip.git

## 一、安装 Git（若未安装）

从 https://git-scm.com/download/win 下载并安装，安装时勾选 “Add Git to PATH”。

## 二、在项目目录执行以下命令

在 **命令提示符** 或 **PowerShell** 中进入项目目录，依次执行：

```bash
cd /d "d:\配置ip"

:: 若尚未初始化
git init

:: 添加远程仓库（若已添加可跳过）
git remote add origin https://github.com/13371/-ip.git
:: 若已存在 origin 且地址不对，可先删除再加：
:: git remote remove origin
:: git remote add origin https://github.com/13371/-ip.git

:: 添加所有文件（.gitignore 已排除 build、dist、.yanbai_ip_config 等）
git add .

:: 提交
git commit -m "砚白配置IP 完整项目：托盘一键切换 IP/DHCP、多模板、TCP 监测、开机启动"

:: 推送到 GitHub（首次推送主分支）
git branch -M main
git push -u origin main
```

若 GitHub 要求登录，按提示在浏览器中完成认证，或使用 Personal Access Token 作为密码。

## 三、日后更新

修改代码后，在同一目录执行：

```bash
cd /d "d:\配置ip"
git add .
git commit -m "简要说明本次修改"
git push
```

## 四、.gitignore 说明

以下内容不会提交（已写在 `.gitignore` 中）：

- `build/`、`build2/`、`dist/`、`dist2/`：打包缓存与 exe 输出
- `.yanbai_ip_config/`：本机模板与配置（每台电脑各自保留）
- `*.spec`：PyInstaller 生成的 spec，可随时重新打包生成
- `__pycache__/`：Python 缓存

如需把打包好的 exe 也放进仓库，可删除 `.gitignore` 里 `dist/` 一行后再 `git add` 并提交。
