# Enterprise AI Agent Platform

企业级 AI Agent 平台。

## Features

- FastAPI
- React
- SSE
- LangGraph
- RAG
- SQL Agent

## Note
采用one-api统一管理接口标准，运行在本地的3000端口

## v0.1  Completed
Chat + SSE + FastAPI + React
完成项目基础框架搭建，实现前后端分离；
支持用户与 LLM 对话；
使用 SSE 实现流式输出

## v0.2 Completed
LangChain + LangGraph + Agent Router + Function Calling 
引入 LangChain 与 LangGraph 重构聊天流程；
使用 PromptTemplate、ChatModel 等 LangChain 组件；
搭建 Agent Router，实现请求路由；
支持 Function Calling，并接入简单工具，
验证 Agent 调用 Tool 的完整流程。

## v0.3 In Progress
RAG（Retriever Tool）
集成企业知识库；
支持 PDF、Word、Markdown、TXT 等文档上传
；完成文档解析、Chunk 切分、Embedding、向量存储与检索；
将 Retriever 封装为 Tool，
由 Agent 自动调用，实现企业知识问答，
并支持引用来源。

