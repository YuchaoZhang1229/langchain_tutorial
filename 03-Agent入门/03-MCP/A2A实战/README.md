# A2A

## 一、A2A是什么？
A2A（Agent-to-Agent）是一种开放协议，**旨在解决不同厂商、不同框架构建的、运行在不同服务器上的Agent之间能够直接通信与协作**

## 二、为什么需要A2A？
单个 Agent 能力有限，复杂任务往往需要多个 Agent：
- 一个负责检索，一个负责分析，一个负责写代码，一个负责审核；
- 不同 Agent 可能由不同公司、不同框架、不同语言实现；
- 传统做法是定制 API，成本高、难复用。

A2A 要提供统一方式：
- **发现能力**：知道对方 Agent 能做什么；
- **发起任务**：把任务交给远程 Agent；
- **交换消息/文件/结构化数据**；
- **跟踪任务状态**；
- **获取最终产物**；
- **支持流式和异步通知**；
- **安全认证与授权**

## 三、核心工作流程
1. **能力发现**：获取远程 agent 的 `Agent Card`，了解其能力
2. **任务委派**：客户端 agent 根据需求给远程 agent 发送 `Message`，创建 `Task`
3. **任务执行**：远程 agent 接收任务并执行，期间可通过 SSE 实时推送任务状态信息
4. **结果返回**：任务完成后，远程 agent 返回包含 `Artifact` 的结构化结果

### 3.1 总体流程图
```text
客户端 Agent / 宿主应用
        │
        │ 1. 获取 Agent Card
        ▼
远程 Agent 的 /.well-known/agent.json
        │
        │ 2. 解析技能、能力、认证方案
        ▼
客户端选择远程 Agent 并完成认证
        │
        │ 3. 发送 Message，创建 Task
        ▼
远程 Agent 接收任务
        │
        ├─ 4a. 直接执行 → working
        ├─ 4b. 需要补充输入 → input-required
        ├─ 4c. 需要认证 → auth-required
        └─ 4d. 拒绝/失败 → rejected / failed
        │
        │ 5. 通过同步响应 / SSE / 推送 / 轮询获取状态
        ▼
任务完成 completed
        │
        │ 6. 返回 Artifact
        ▼
客户端整合结果；或取消、重试、延续上下文
```
### 3.2 最小典型时序
```text
客户端 Agent                     远程 Agent
     │                               │
     │ 1. GET Agent Card             │
     │──────────────────────────────►│
     │◄──────────────────────────────│
     │                               │
     │ 2. 认证                        │
     │──────────────────────────────►│
     │                               │
     │ 3. message/send 创建 Task      │
     │──────────────────────────────►│
     │◄── Task: submitted/working ───│
     │                               │
     │ 4. 流式/推送/轮询获取进度       │
     │◄─────────────────────────────►│
     │                               │
     │ 5. 若 input-required           │
     │── 后续 Message，同 taskId ────►│
     │◄── working → completed ───────│
     │                               │
     │ 6. 获取 Artifact               │
     │◄──────────────────────────────│
     │                               │
```


## 四、核心概念与对象
A2A 的核心对象可以记成：

> `Agent Card` 是名片，`Skill` 是能力项，`Task` 是协作单元，`Message` 是过程交流，`Part` 是内容片段，`Artifact` 是最终交付物，`contextId` 串联上下文。

A2A 不是 Agent 开发框架，而是 Agent 与 Agent 之间的通信与任务协作协议。

### 4.1 核心对象关系图
```text
Agent Card
  ├── skills[]             能力声明
  ├── capabilities         是否支持流式、推送等
  └── securitySchemes      认证方案
          │
          │ 客户端发现并选择 Agent
          ▼
Task  ←── contextId 关联多个 Task / 多轮消息
  ├── id
  ├── status               任务状态
  ├── history[]            消息历史
  └── artifacts[]          最终产物
          │
          ├── Message      过程交流
          │     └── parts[]：Text / File / Data
          │
          └── Artifact     最终交付物
                └── parts[]：Text / File / Data
```

### 4.1 Agent Card：Agent的名片
Agent Card 是描述远程 Agent 的 JSON 元数据，描述能力、技能、联系方式等

📝 Agent Card 核心参数详解表

| 参数层级 | 字段名称 | 数据类型 | 核心作用与说明 |
| :--- | :--- | :--- | :--- |
| **基础信息** | `name` | String | 智能体的人类可读名称（如 "Travel Booking Agent"） |
| | `description` | String | 智能体功能的详细描述，帮助其他 Agent 理解其用途 |
| | `version` | String | 智能体自身的版本号（非 A2A 协议版本） |
| | `provider` | Object | 服务提供方信息，包含 `organization`（组织名）和 `url` |
| | `documentationUrl`| String | 智能体的官方文档链接（选填） |
| **接口与传输** | `url` | String | 智能体提供 A2A 服务的主端点 URL |
| | `supportedInterfaces`| Array | 支持的传输协议列表（如 JSON-RPC, gRPC），包含协议绑定和版本 |
| **能力声明** | `capabilities` | Object | 声明支持的 A2A 高级特性，如 `streaming`（流式输出）、`pushNotifications`（推送通知） |
| | `skills` | Array | **核心能力矩阵**：智能体可执行的具体技能列表（详见下方 Skill 拆解） |
| **输入/输出模式**| `defaultInputModes` | Array | 默认支持的输入 MIME 类型（如 `text/plain`, `application/json`） |
| | `defaultOutputModes`| Array | 默认支持的输出 MIME 类型（如 `image/png`, `text/plain`） |
| **安全与信任** | `securitySchemes` | Object | 安全认证方案定义（遵循 OpenAPI 规范，如 OAuth2, API Key） |
| | `security` | Array | 具体的安全要求，定义调用该 Agent 需要满足的权限或认证方式 |
| | `signatures` | Array | JWS（JSON Web Signature）签名，用于验证 Agent Card 的完整性和来源 |<websource>source_group_web_4</websource>


🛠️ 核心子结构：Skill (技能) 拆解

`skills` 是 Agent Card 中最关键的部分，它决定了其他 Agent 是否会将特定任务委派给它。每个 Skill 对象包含以下参数：

| 字段名称 | 数据类型 | 说明 |
| :--- | :--- | :--- |
| `id` | String | 技能的唯一标识符（如 "flight-search"） |
| `name` | String | 技能的人类可读名称 |
| `description` | String | 技能的具体功能描述 |
| `tags` | Array | 用于分类和检索的关键词标签（如 `["travel", "flight"]`） |
| `examples` | Array | 示例提示词或使用场景，帮助调用方理解如何触发该技能 |
| `inputModes` | Array | （选填）该技能特定的输入格式，若不同则覆盖 `defaultInputModes` |
| `outputModes`| Array | （选填）该技能特定的输出格式，若不同则覆盖 `defaultOutputModes` |<websource>source_group_web_6</websource>

### 4.2 Task：协作的基本单元
📝 Task 核心参数详解表

| 字段名称 | 数据类型 | 核心作用与说明 |
| :--- | :--- | :--- |
| `id` | String | 任务的唯一标识符（UUID），由服务端生成 |
| `contextId` | String | 上下文 ID，用于将多个相关的 Task 关联到同一个会话/上下文中 |
| `status` | Object | 任务的当前状态对象，包含 `state`（状态枚举）、`timestamp`（时间戳）和可选的 `message`（状态更新说明） |
| `history` | Array | 消息历史记录，包含客户端和 Agent 之间的多轮交互日志（Message 对象数组） |
| `artifacts` | Array | 任务产出物列表，Agent 执行任务后生成的最终结果（如文件、结构化数据） |
| `metadata` | Object | 扩展元数据，用于传递业务自定义的键值对信息 |<websource>source_group_web_4</websource>

🔄 Task 状态机 (TaskState)

| 状态枚举值 | 含义说明 | 状态类型 |
| :--- | :--- | :--- |
| `submitted` | 任务已提交，等待 Agent 处理 | 初始状态 |
| `working` | Agent 正在处理任务（核心执行阶段） | 进行中 |
| `input-required` | 任务中断，需要客户端/用户提供额外输入（如确认信息、补充参数） | 中断状态 |
| `auth-required` | 任务中断，需要客户端提供额外的认证或授权 | 中断状态 |
| `completed` | 任务成功完成，通常伴随 `artifacts` 产出 | 终态 |
| `failed` | 任务因错误执行失败 | 终态 |
| `canceled` | 任务被客户端主动取消 | 终态 |
| `rejected` | Agent 拒绝执行该任务（如超出能力范围） | 终态 |<websource>source_group_web_7</websource>



```text
submitted ──► working ──► completed
                 │
                 ├──► input-required ──(补消息)──► working
                 ├──► auth-required  ──(补认证)──► working
                 ├──► failed
                 ├──► canceled
                 └──► rejected

unknown：客户端无法识别的状态，按未知处理
```


### 4.3 Message、Part、Artifact
| 核心概念 | 角色定位 | 核心作用与说明 |
| :--- | :--- | :--- |
| **Message**<br>(消息) | 通信载体 | 代表客户端与 Agent 之间的**单次通信轮次**。主要用于传递指令、上下文、提问或状态更新，包含发送者角色（`user` 或 `agent`）<websource>source_group_web_2</websource>。 |
| **Part**<br>(片段) | 原子内容单元 | 构成 Message 或 Artifact 的**最小内容载体**。支持多模态，可以是文本（TextPart）、文件（FilePart）或结构化 JSON 数据（DataPart）<websource>source_group_web_3</websource>。 |
| **Artifact**<br>(工件) | 最终交付物 | 代表 Agent 执行任务后产生的**实质性成果**（如生成的文件、代码、报告）。它同样由多个 Part 组成，是任务产出的具体体现<websource>source_group_web_4</websource>。 |



