# AutoClip 安装与使用说明

本文档基于当前仓库实际代码结构整理，适用于本地开发和联调环境。当前工作区下存在多个目录副本，主项目目录为 `autoclip-runcheck/`。

## 1. 项目概览

AutoClip 是一个 AI 视频智能切片系统，当前仓库主要由以下部分组成：

- 后端：`FastAPI + Celery + Redis + SQLite`
- 前端：`React 18 + TypeScript + Vite + Ant Design`
- 核心能力：本地视频上传、B 站/YouTube 链接导入、AI 切片、合集生成、任务进度跟踪、设置页多模型配置

主要访问地址：

- 前端：`http://localhost:3000`
- 后端：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/v1/health/`

## 2. 推荐安装方式

推荐优先使用“本地开发方式”，原因如下：

- 启动脚本和前后端代理配置更完整
- 便于调试日志、查看数据库和任务队列
- 当前生产版 `docker-compose.yml` 暴露了 `3000` 端口，但实际没有启动独立前端服务

如果只想尽快跑起来，建议使用下面这条路径：

1. 安装系统依赖
2. 创建 `venv/` 虚拟环境
3. 安装 Python 和前端依赖
4. 启动 Redis
5. 执行 `./start_autoclip.sh`

## 3. 环境要求

### 3.1 基础依赖

- 操作系统：Linux / macOS / Windows（建议 WSL）
- Python：`3.9+` 更稳妥
- Node.js：`18+` 更合适
- npm：随 Node 安装
- Redis：`6+`
- FFmpeg：视频处理必需

### 3.2 可选 AI 依赖

基础 `requirements.txt` 只覆盖后端框架和任务系统，不包含所有模型 SDK。

如果你要实际执行 AI 处理，建议额外运行：

```bash
python install_llm_dependencies.py
```

这个脚本会补装：

- `dashscope`
- `openai`
- `google-generativeai`
- `requests`

## 4. 本地安装步骤

以下命令均在项目根目录 `autoclip-runcheck/` 下执行。

### 4.1 创建虚拟环境

注意：项目脚本写死依赖 `venv/` 目录，不要只创建 `.venv/`。

```bash
cd autoclip-runcheck
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

### 4.2 安装 Python 依赖

```bash
pip install -U pip
pip install -r requirements.txt
```

如果需要 AI 模型能力，再执行：

```bash
python install_llm_dependencies.py
```

### 4.3 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 4.4 安装 Redis

macOS:

```bash
brew install redis
brew services start redis
```

Ubuntu / Debian:

```bash
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 4.5 安装 FFmpeg

macOS:

```bash
brew install ffmpeg
```

Ubuntu / Debian:

```bash
sudo apt install -y ffmpeg
```

### 4.6 配置环境变量

```bash
cp env.example .env
```

最小可用配置示例：

```env
DATABASE_URL=sqlite:///./data/autoclip.db
REDIS_URL=redis://localhost:6379/0
API_DASHSCOPE_API_KEY=
API_MODEL_NAME=qwen-plus
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG=true
```

说明：

- 不填 `API_DASHSCOPE_API_KEY` 也能启动系统
- 但不配置模型提供商 API Key 时，AI 处理流程无法真正执行
- API Key 也可以在 Web 设置页里填写并保存到 `data/settings.json`

## 5. 启动方式

### 5.1 一键启动

推荐：

```bash
./start_autoclip.sh
```

更快但检查更少：

```bash
./quick_start.sh
```

相关命令：

```bash
./status_autoclip.sh
./stop_autoclip.sh
```

### 5.2 手动启动

当一键脚本排查问题不方便时，可以手动分别启动服务。

先激活环境并设置 Python 路径：

```bash
source venv/bin/activate
export PYTHONPATH="$PWD:$PYTHONPATH"
```

初始化数据库：

```bash
python init_database.py
```

启动后端：

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

启动 Celery Worker：

```bash
celery -A backend.core.celery_app worker --loglevel=info --concurrency=2 -Q processing,upload,notification,maintenance
```

启动前端：

```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

## 6. 第一次使用流程

### 6.1 打开页面

浏览器访问：

- `http://localhost:3000`

### 6.2 配置模型提供商

进入设置页：

- `http://localhost:3000/settings`

当前前端支持在设置页配置：

- DashScope
- OpenAI
- Gemini
- SiliconFlow

建议步骤：

1. 选择模型提供商
2. 填入 API Key
3. 选择模型
4. 点击“测试连接”
5. 保存配置

### 6.3 导入视频

首页当前提供两类导入方式：

- 文件导入：上传本地视频，可附带 `.srt` 字幕文件
- 链接导入：支持 B 站和 YouTube 链接

导入时建议填写：

- 项目名称
- 视频分类

### 6.4 开始处理

项目创建成功后：

1. 在首页项目卡片点击开始处理
2. 等待后台任务完成
3. 进入项目详情页查看切片和合集

### 6.5 查看结果

处理完成后可查看：

- 切片列表
- AI 推荐合集
- 手动创建合集
- 合集预览与下载

## 7. 目录与数据说明

常见目录如下：

```text
autoclip-runcheck/
├── backend/                 后端代码
├── frontend/                前端代码
├── data/                    数据目录
├── logs/                    运行日志
├── prompt/                  AI 提示词模板
├── start_autoclip.sh        一键启动脚本
├── quick_start.sh           快速启动脚本
├── stop_autoclip.sh         停止脚本
└── status_autoclip.sh       状态查看脚本
```

运行过程中重点关注：

- 数据库：`data/autoclip.db`
- 项目数据：`data/projects/<project_id>/`
- 后端日志：`logs/backend.log`
- 前端日志：`logs/frontend.log`
- Celery 日志：`logs/celery.log`

## 8. Docker 说明

### 8.1 开发环境

开发版 compose 会同时启动后端、前端和 Redis：

```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 8.2 当前限制

当前 `docker-compose.yml` 存在一个实际限制：

- 镜像中会构建前端 `dist`
- 但容器入口默认只启动 `uvicorn`
- `3000` 端口虽然暴露了，生产 compose 中并没有独立前端进程

因此当前仓库状态下：

- 开发联调优先用本地方式或 `docker-compose.dev.yml`
- 如果要正式使用生产 compose，需要额外补上前端静态托管或前端服务进程

## 9. 常见问题

### 9.1 启动脚本提示找不到虚拟环境

原因：

- 脚本检查的是 `venv/`
- 当前工作区里还可能存在一个 Windows 风格的 `.venv/`

解决：

```bash
python3 -m venv venv
source venv/bin/activate
```

### 9.2 `init_database.py` 或后端启动时报缺少依赖

例如：

- `No module named 'fastapi'`
- `No module named 'sqlalchemy'`

解决：

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 9.3 前端构建时报 `tsc: Permission denied`

这通常说明当前 `frontend/node_modules` 不是在当前系统环境下正确安装出来的，常见于跨平台拷贝。

建议：

```bash
cd frontend
npm install
```

如果仍有问题，再清理后重装前端依赖。

### 9.4 前端构建时报缺少 `@rollup/rollup-linux-x64-gnu`

这是 `rollup` 可选依赖未正确安装的典型现象。

解决思路：

```bash
cd frontend
npm install
```

必要时清理现有 `node_modules` 后重新安装。

### 9.5 Redis 没启动

检查：

```bash
redis-cli ping
```

返回 `PONG` 才表示正常。

## 10. 可选能力

### 10.1 无字幕视频的语音识别

如果视频没有字幕，可按需安装语音识别能力：

- 本地 Whisper
- `bcut-asr`

相关文档：

- `docs/SPEECH_RECOGNITION_SETUP.md`

相关脚本：

```bash
python scripts/install_bcut_asr.py
```

## 11. 启动成功检查清单

满足以下条件，说明系统基本可用：

1. `redis-cli ping` 返回 `PONG`
2. 打开 `http://localhost:8000/api/v1/health/` 返回健康状态
3. 打开 `http://localhost:8000/docs` 能看到 Swagger
4. 打开 `http://localhost:3000` 能看到首页
5. 在设置页保存 API Key 后，测试连接通过

## 12. 当前分析结论

基于当前仓库代码状态，建议这样理解项目：

- `autoclip-runcheck/` 是当前可分析和可维护的主目录
- 本地脚本启动链路比生产 Docker 链路更完整
- 一键脚本依赖 `venv/` 目录命名
- 前端依赖目录如果来自其他平台，容易出现权限和可选依赖问题
- AI 配置更适合通过设置页维护，实际会落到 `data/settings.json`

