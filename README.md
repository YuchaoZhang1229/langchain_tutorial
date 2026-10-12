# langchain_tutorial

基于 **LangChain 1.x** 的大模型应用开发学习教程（L2 阶段）。按「由浅入深」组织：从直接调用大模型开始，掌握模型、消息、提示词、输出解析四大核心概念，再进阶 Runnable 链式协议、记忆、检索增强（RAG），最后到 Agent / LangGraph 智能体开发，落地一个完整 RAG 实战项目并用 LangServe 部署为 Web 服务。

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | LangChain 1.x（`langchain` + `langchain-classic`） |
| 模型 | DeepSeek、通义千问（Qwen）、OpenAI、Anthropic |
| Web 服务 | FastAPI + LangServe |
| 服务器 | Uvicorn |
| 包管理 | uv（`pyproject.toml` + `uv.lock`） |
| 交互 | Jupyter Notebook |
| Python | >= 3.12 |

## 目录结构

```
langchain_tutorial/
├── 01-核心概念/
│   ├── 00-OpenAI调用大模型.ipynb       # 直接调用大模型
│   ├── 01-Models模型.ipynb             # 模型
│   ├── 02-Messages消息.ipynb           # 消息
│   ├── 03-Prompts提示词模版.ipynb      # 提示词模板
│   ├── 04-OutputParsers输出解析器.ipynb # 输出解析
│   ├── 05-Deploy部署.ipynb             # 部署
│   └── deploy_service.py               # 翻译服务部署实战
├── 02-Runnable协议/
│   └── 01-Chain链式调用.ipynb          # LCEL 链式调用
├── 03-记忆与历史/
│   ├── 01-Memory.ipynb                 # 消息历史（内存）
├── 04-检索增强RAG/
│   └── 01-RAG.ipynb                    # 文档加载/切分/向量/检索
├── 05-智能体Agent/
│   ├── 01-Agent.ipynb                  # Agent 核心
│   ├── 02-Tool.ipynb                   # 工具
│   ├── 03-MiddleWare.ipynb             # 中间件
│   ├── 04-LangGraph入门.ipynb          # State / Node / Edge
│   └── data/                           # 测试数据（人事管理流程.docx）
├── 06-实战项目/
│   └── 01-完整RAG问答应用.ipynb        # 毕业项目：串联全部知识
├── 07-面试与进阶/
│   └── 01-高频面试题.md                # 考点对照表 + 面试话术
├── src/langchain_tutorial/             # 包入口
├── pyproject.toml                      # 项目配置与依赖
└── uv.lock                             # 依赖锁定文件
```

## 内容大纲

| 阶段 | 目录 | 主题 | 核心知识点 |
|------|------|------|-----------|
| 01 | 核心概念 | 四大基石 | `init_chat_model`、四种消息类型、`PromptTemplate`/`ChatPromptTemplate`、`StrOutputParser`/`JsonOutputParser`、参数配置、连接韧性、部署 |
| 02 | Runnable 协议 | 链式调用 | `invoke`/`stream`/`batch`、LCEL（`\|` 管道符）、`prompt \| model \| parser` 链 |
| 03 | 记忆与历史 | 多轮对话 | `InMemoryChatMessageHistory`、`RedisChatMessageHistory`（session_id、持久化） |
| 04 | 检索增强 RAG | 私有知识问答 | `DocumentLoader`、`TextSplitter`、`Embeddings`、`VectorStore`、`Retriever` |
| 05 | 智能体 Agent | 自主决策 | Agent 循环、工具（内置/自定义）、中间件、LangGraph（State/Node/Edge） |
| 06 | 实战项目 | 综合落地 | 完整 RAG 链路（加载→切分→嵌入→入库→检索→生成）+ 记忆 + 部署 |
| 07 | 面试与进阶 | 复盘沉淀 | 高频面试题、30 秒话术、follow-up 准备 |

## 部署实战（deploy_service.py）

用一个「翻译服务」串联核心概念：通过 `prompt | model | output_parser` 组成 Chain（基于 DeepSeek 模型 + `JsonOutputParser`），再用 FastAPI + LangServe 部署成 Web 服务，支持：

- **LangServe 路由**：`/langchainServer`
- **客户端调用**：`RemoteRunnable` 远程调用
- **RESTful API**：用 Postman / Apifox 调用 `/langchainServer/invoke`
- **CORS 跨域**：已放开（学习阶段，生产环境建议指定域名）

## 快速开始

```bash
# 1. 安装依赖（自动按 pyproject.toml / uv.lock 安装）
uv sync

# 2. 配置模型 API Key 环境变量（例如）
#    DEEPSEEK_API_KEY=sk-xxx

# 3. 按顺序打开 notebook 学习，或直接启动翻译服务
python deploy_service.py
```

> 学习 03 阶段的 Redis 记忆前，需先启动本机 Redis 服务。

## 学习路线建议

按目录编号顺序学习即可（**01 → 02 → 03 → 04 → 05 → 06 → 07**），每一阶段都是下一阶段的地基：

1. **01 核心概念**：先了解如何直接调用模型，掌握「模型 → 消息 → 提示词 → 输出解析」四大件
2. **02 Runnable 协议**：把组件用 LCEL 串成链
3. **03 记忆与历史**：让模型"记得住"多轮对话
4. **04 检索增强 RAG**：让模型回答私有知识
5. **05 智能体 Agent**：进阶到 Agent + LangGraph 自主决策
6. **06 实战项目**：串起全部知识，完成 RAG 问答应用
7. **07 面试与进阶**：沉淀面试答案，复盘收尾
