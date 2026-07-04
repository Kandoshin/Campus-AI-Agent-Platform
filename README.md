# Campus AI Agent Platform

当前版本：`v0.3.0`

Campus AI Agent Platform 是一个面向高校场景的 AI Agent 平台，目标是把校园知识检索、工具调用和自然语言问答统一到一个对话入口中。


## 当前能力

- 前后端分离：`FastAPI` + `React` + `TypeScript` + `Vite`
- SSE 流式聊天接口
- LangGraph Agent 工作流
- Function Calling 工具调用
- 校园知识库 RAG
- 支持上传 `PDF`、`DOCX`、`Markdown`、`TXT`
- 使用智谱官方 `embedding-3` 生成向量
- 使用 Milvus 存储和检索文档 chunk 向量
- 支持知识库元数据：标题、分类、页码、访问级别
- RAG 检索时支持按角色过滤 `public`、`student`、`admin` 数据

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

相较于 v0.2，v0.3 的主要变化是把项目从基础 Agent Demo 推进到校园知识库 RAG 场景：

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

### 2. 启动后端

在 Windows PowerShell 中运行：

```powershell
uvicorn app.main:app --port 8000
```

Swagger 文档：

```text
http://127.0.0.1:8000/docs
```

### 3. 启动前端

在另一个 Windows PowerShell 窗口中运行：

```powershell
npm run dev
```

前端地址：

```text
http://localhost:5173
```

## 常用接口

### 聊天

```text
POST /api/chat
```

用于和 LangGraph Agent 对话，支持工具调用和知识库检索。

### 上传知识库文档

```text
POST /api/knowledge/upload
```

用于上传校园知识库文档，并写入 Milvus。