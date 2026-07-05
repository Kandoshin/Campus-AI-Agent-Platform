# Campus AI Agent Platform

当前版本：`v0.9.0`

Campus AI Agent Platform 是一个面向高校场景的 AI Agent 平台，目标是把校园知识检索、工具调用、权限控制和自然语言问答统一到一个对话入口中。项目定位不是 ChatGPT 套壳，而是围绕校园知识库、校园服务流程和多角色访问控制构建的 Agent 应用原型。

## 当前能力

- 前后端分离：`FastAPI` + `React` + `TypeScript` + `Vite`
- SSE 流式聊天接口
- LangGraph Agent 工作流
- Function Calling 工具调用
- 校园知识库 RAG
- 支持上传 `PDF`、`DOCX`、`Markdown`、`TXT`
- 使用智谱官方 `embedding-3` 生成 1024 维向量
- 使用 Milvus 存储和检索文档 chunk 向量
- 使用 PostgreSQL 存储平台用户和角色信息
- 支持用户登录、JWT 登录态和角色识别
- 支持 `guest`、`student`、`admin` 三类访问角色
- 支持知识库元数据：标题、分类、页码、访问级别
- RAG 检索时按角色过滤 `public`、`student`、`admin` 数据
- 知识库上传接口限制为管理员可用
- 前端支持管理员添加用户
- 前端支持 Markdown 渲染 AI 回答，包括加粗、列表、表格和代码块
- 前端支持局域网访问，Vite 代理 `/api` 到后端服务

## 版本变更

### v0.1

- 搭建 FastAPI 后端和 React 前端基础结构
- 实现基础 AI Chat 接口
- 支持 SSE 流式输出

### v0.2

- 引入 LangChain 和 LangGraph
- 增加基础 Function Calling 工具
- 支持当前时间、简单计算等工具调用
- 初步形成 Agent 工作流：模型判断是否需要调用工具，再返回最终回答

### v0.3

- 项目定位调整为 `Campus AI Agent Platform`
- 后端应用名称和版本更新为 `Campus AI Agent Platform API v0.3.0`
- 新增校园知识库上传接口：`POST /api/knowledge/upload`
- 上传文档时支持填写 `title`、`category`、`access_level`
- 文档处理流程完整接入：解析、chunk 切分、embedding、Milvus 入库
- chunk 切分使用 `RecursiveCharacterTextSplitter`
- 当前 chunk 参数：`chunk_size=800`，`chunk_overlap=100`
- 每个 chunk 写入 Milvus 时保存来源元数据
- 新增校园知识库检索工具：`query_campus_knowledge_base`
- RAG 检索支持按角色过滤访问范围：
  - `guest`：只能检索 `public`
  - `student`：可以检索 `public`、`student`
  - `admin`：可以检索 `public`、`student`、`admin`
- 前端标题更新为 `Campus AI Agent Platform - v0.3`

### v0.9

- 后端版本更新为 `Campus AI Agent Platform API v0.9.0`
- 新增 PostgreSQL 数据库接入
- 新增 JWT 登录态
- 前端新增登录弹窗
- 前端新增当前身份显示
- 前端新增管理员“添加用户”功能
- 用户角色分为：
  - `guest`：未登录访客，只能访问公开知识
  - `student`：普通用户，可访问公开和学生级知识
  - `admin`：管理员，可访问全部知识并管理知识库上传
- 聊天接口接入当前用户上下文
- 知识库检索工具在服务端强制使用当前用户角色进行权限过滤
- 知识库上传接口限制为管理员可用
- 新增固定 AI 身份提示词，避免助手自称 ChatGPT 或通用机器人
- 前端聊天页面重构为校园服务工作台风格
- 前端支持 Markdown 渲染 AI 回答：
- 前端请求统一使用相对路径 `/api/chat`
- Vite 开发服务器支持局域网访问，并代理 `/api` 到后端

## 环境变量

后端环境变量位于：

```text
backend/.env
```

示例结构：

```env
OPENAI_API_KEY=你的 OpenAI-compatible API key
OPENAI_API_BASE=https://api.littlecold.cn/v1
OPENAI_DEFAULT_MODEL=gpt-5.5

ZHIPU_API_KEY=你的智谱 API key
EMBEDDING_MODEL=embedding-3
EMBEDDING_DIMENSIONS=1024
EMBEDDING_BATCH_SIZE=16

MILVUS_URI=http://127.0.0.1:19530
MILVUS_COLLECTION=campus_knowledge

DATABASE_URL=postgresql+psycopg://campus_ai:campus_ai_dev_password@127.0.0.1:5432/campus_ai

AUTH_SECRET_KEY=请替换为一串足够长的随机字符串
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=请替换为你自己的管理员密码
DEFAULT_ADMIN_DISPLAY_NAME=系统管理员
```

说明：

- `DATABASE_URL` 用于后端连接 PostgreSQL
- `AUTH_SECRET_KEY` 用于签发和校验登录 token
- `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` 用于首次初始化默认管理员
- 如果 `users` 表中已经存在默认管理员，修改 `DEFAULT_ADMIN_PASSWORD` 不会自动更新已有管理员密码

## 运行方式

### 1. 启动 Milvus

在 WSL 中运行：

```bash
cd ~/milvus-docker
docker compose up -d
```

确认 Milvus 容器正在运行：

```bash
docker ps
```

### 2. 启动 PostgreSQL

如果 PostgreSQL 使用 Docker Compose 部署，进入你的 PostgreSQL compose 目录后运行：

```bash
docker compose up -d
```

确认 PostgreSQL 容器正在运行：

```bash
docker ps
```

使用 DBeaver 或 `psql` 确认可以连接：

```text
Host: 127.0.0.1
Port: 5432
Database: campus_ai
Username: campus_ai
Password: campus_ai_dev_password
```

### 3. 启动后端

在 Windows PowerShell 中运行：

```powershell
cd G:\work\project\uni\Campus-AI-Agent-Platform\backend
conda activate ai_dev
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

后端启动时会自动执行数据库初始化，并在 `users` 表中创建默认管理员。

Swagger 文档：

```text
http://127.0.0.1:8000/docs
```

### 4. 启动前端

在另一个 Windows PowerShell 窗口中运行：

```powershell
cd G:\work\project\uni\Campus-AI-Agent-Platform\frontend
npm.cmd run dev
```

前端地址：

```text
http://localhost:5173
```

手机或其他局域网设备访问：

```text
http://电脑局域网IP:5173
```

## 常用接口

### 聊天

```text
POST /api/chat
```

用于和 LangGraph Agent 对话，支持工具调用和知识库检索。未登录时按 `guest` 权限处理；登录后按当前用户角色处理。

### 登录

```text
POST /api/auth/login
```

用于登录平台账号，成功后返回 `access_token`。

### 当前用户

```text
GET /api/auth/me
```

用于获取当前登录用户。未登录时返回 `guest` 身份。

### 添加用户

```text
POST /api/auth/users
```

仅管理员可用，用于创建普通用户或管理员。

### 上传知识库文档

```text
POST /api/knowledge/upload
```

用于上传校园知识库文档，并写入 Milvus。当前版本仅管理员可调用。

## 默认管理员

首次启动后端时，如果数据库中不存在默认管理员，系统会自动创建：

```text
username: admin
password: backend/.env 中的 DEFAULT_ADMIN_PASSWORD
role: admin
```

开发阶段如果未配置 `.env` 中的 `DEFAULT_ADMIN_PASSWORD`，代码默认值为：

```text
admin123456
```

正式使用前请务必修改默认管理员密码和 `AUTH_SECRET_KEY`。
