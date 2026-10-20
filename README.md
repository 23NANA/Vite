# 智能实验室预约系统

一个基于 Agent 的实验室 / 设备预约系统：学生在网页端浏览实验室、提交预约，管理员审核；AI 助手可以对话式地查库、检索规则并完成预约。

## 功能

- **预约业务**：实验室与设备浏览、提交预约、我的预约、取消预约
- **审核管理**：预约审核、实验室 / 设备 / 用户管理
- **AI 助手**：基于 LangGraph 的 Tool Calling Agent，SSE 流式输出，过程（工具调用）实时可见
- **知识库问答**：RAG 检索预约规则、开放时间、安全规范等文档

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Vite + Element Plus + Vue Router + Axios |
| 后端 | FastAPI + SQLAlchemy 2 + MySQL + PyJWT |
| AI | LangChain / LangGraph + OpenAI 兼容接口 + Chroma + sentence-transformers |

## 目录结构

```
backend/
  app/
    api/          # 路由
    models/       # SQLAlchemy 模型
    schemas/      # Pydantic 模型
    services/     # 业务逻辑、Agent、知识库
    utils/        # JWT、密码加密
    config.py     # 配置（读取 .env）
    main.py       # FastAPI 入口
  data/kb/        # RAG 知识库原始文档
frontend/
  src/
    views/        # 页面
    components/   # 通用组件
    api/          # 接口封装
    layouts/      # 布局
    stores/       # 全局状态
```

## 本地运行

### 1. 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # 然后按注释填写数据库与模型配置
uvicorn app.main:app --reload --port 8000
```

首次启动会用 `Base.metadata.create_all` 自动建表；同时加载嵌入模型并预热向量库（把 `data/kb` 下的文档建索引），因此第一次启动会慢十几秒。

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

默认请求 `http://127.0.0.1:8000`（见 `frontend/.env.development` 里的 `VITE_API_BASE_URL`）。

## 环境变量

后端配置放在 `backend/.env`，字段说明见 [backend/.env.example](backend/.env.example)：

- `DATABASE_URL`：MySQL 连接串
- `JWT_SECRET_KEY` / `JWT_ALGORITHM` / `JWT_EXPIRE_HOURS`：登录令牌配置
- `LLM_API_KEY` / `LLM_MODEL` / `LLM_BASE_URL`：兼容 OpenAI 接口的大模型服务

> `backend/.env` 已被 `.gitignore` 忽略，请勿提交自己的密钥。
