# langchain_tutorial

基于 **LangChain 1.x** 的大模型应用开发学习教程（L2 阶段）。从直接调用大模型开始，逐步掌握 LangChain 的模型、提示词、输出解析三大核心模块，再到 Agent 智能体开发，最终用 LangServe 将应用部署为 Web 服务。

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
├── 1. OpenAI调用大模型.ipynb     # 直接调用大模型
├── 2. LangChain-Agent.ipynb      # Agent 智能体
├── 3. LangChain-Models.ipynb     # 模型
├── 4. LangChain-Promts.ipynb     # 提示词模板
├── 5. LangChain-Output.ipynb     # 输出解析
├── 6. LangChain-deploy.ipynb     # 部署
├── deploy_service.py             # 翻译服务部署实战
├── src/langchain_tutorial/       # 包入口
├── pyproject.toml                # 项目配置与依赖
└── uv.lock                       # 依赖锁定文件
```

## 内容大纲

| 序号 | 文件 | 主题 | 核心知识点 |
|------|------|------|-----------|
| 1 | OpenAI调用大模型.ipynb | 直接调用大模型 | 分别用 DeepSeek / Qwen / LangChain 三种方式调用 |
| 2 | LangChain-Agent.ipynb | Agent 智能体 | 环境准备、加载环境变量、定义工具、定义并调用 Agent |
| 3 | LangChain-Models.ipynb | 模型 | `init_chat_model`、invoke / stream / batch、参数配置、连接韧性、工具调用、结构化输出 |
| 4 | LangChain-Promts.ipynb | 提示词模板 | `PromptTemplate`、`ChatPromptTemplate`、`FewShotPromptTemplate`、Partial 部分变量 |
| 5 | LangChain-Output.ipynb | 输出解析 | `StrOutputParser`、`JsonOutputParser`、`CommaSeparatedListOutputParser`、`DatetimeOutputParser`、自定义解析器 |
| 6 | LangChain-deploy.ipynb | 部署 | LangServe + FastAPI 部署 Web 服务 |

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

## 学习路线建议

按 **1 → 3 → 4 → 5 → 2 → 6** 的顺序学习更顺畅：先了解如何直接调用模型，再掌握 LangChain 的「模型 → 提示词 → 输出解析」三大件，然后进阶到 Agent，最后完成部署。
