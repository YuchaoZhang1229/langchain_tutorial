"""
================================================================================
A2A 协议客户端实现（python-a2a 版）— 客服主管（中央调度器）
================================================================================

【角色定位】
整个多智能体系统的「大脑」和「调度中心」。作为 A2A 协议的客户端，它负责：
  1. 接收用户的自然语言输入
  2. 用大模型（DeepSeek）做意图分类
  3. 根据意图发现并调用对应的专员服务（退货专员 / 物流专员）
  4. 把专员的回复返回给用户

【运行前】
先把两个专员起来（各占一个终端）：
    python agent_return.py      # 8003
    python agent_shipping.py    # 8004
再运行本文件：
    python supervisor.py
================================================================================
"""
# ====================================================================
# 第一部分：导入依赖
# ====================================================================
from python_a2a import (
    # 【名片】+【传输】客户端：构造时自动完成名片发现
    A2AClient,
    # 【传输】Agent 注册表：批量管理多个专员端点
    AgentNetwork,
)

# ---- 本地大模型客户端 ----
# 封装 DeepSeek 调用，用于意图分类（智能路由）
from llm_client import chat

# ====================================================================
# 第二部分：配置 — 各个专员的访问地址
# ====================================================================
# 【传输】目标端点配置
# 这些地址必须与各专员 AgentCard.url 以及服务启动端口完全一致。
# 注意用「裸地址」（不带 /a2a），否则名片发现会拿到 HTML 说明页，
# 导致 skills 解析为空 —— 详见 agent_return.py 第 4.2 节。
AGENTS = {
    "return": "http://localhost:8003",    # 【传输】退货专员地址
    "shipping": "http://localhost:8004",  # 【传输】物流专员地址
}

# ====================================================================
# 第三部分：业务层 — LLM 意图分类
# ====================================================================
# 为什么用 LLM 而不是关键词匹配？
#   - 关键词匹配只能处理「退货」「物流」等固定词汇
#   - 「我想把东西退掉」不含「退货」二字，关键词会漏判
#   - 「我的包裹到哪了」不含「物流」「快递」，同样会漏判
#   - LLM 能理解语义，更接近真实生产环境
# 对照实验：把 CLASSIFY_WITH_LLM 改成 False，就能看到关键词版的差距。
CLASSIFY_WITH_LLM = True

ROUTING_SYSTEM_PROMPT = """你是一个客服主管，负责判断用户的问题应该分配给哪个专员处理。

请根据用户问题，只回复一个词：
- "return" — 用户想退货、退款、换货
- "shipping" — 用户想查物流、快递进度、包裹位置
- "unknown" — 无法判断

只回复一个词，不要解释。"""

# 关键词回退表（仅用于对照演示 LLM 路由的优势）
# 故意只放最直白的词，和原版 supervisor.py 附录里的例子保持一致：
#   if "退货" in query or "退款" in query: → return
#   elif "物流" in query or "快递" in query: → shipping
# 不要「贴心地」往这里加「退掉」「包裹」「到哪了」——那会让对照实验失去意义。
KEYWORDS = {
    "return": ("退货", "退款"),
    "shipping": ("物流", "快递"),
}

# 意图识别
def classify_intent(query: str) -> str:
    """判断用户问题该交给哪个专员，返回 'return' / 'shipping' / 'unknown'。"""
    if CLASSIFY_WITH_LLM:
        result = chat(ROUTING_SYSTEM_PROMPT, query, model="deepseek-chat")
        return result.strip().lower()

    # 关键词版：只为对照，说明为什么真实项目要上 LLM
    for intent, words in KEYWORDS.items():
        if any(w in query for w in words):
            return intent
    return "unknown"


# ====================================================================
# 第四部分：核心路由函数 — A2A 客户端的完整调用流程
# ====================================================================
def route_query(query: str, network: AgentNetwork) -> None:
    """
    根据 LLM 判断的意图，把任务路由给对应的专员。

    这个方法展示了 A2A 客户端的标准使用模式，三个核心步骤：
        步骤1：【名片】服务发现 — A2AClient(url) 构造时自动拉取 Agent Card
        步骤2：【任务】发起请求 — client.ask(query) 内部创建/继续 Task
        步骤3：【传输】网络通信 — HTTP 把消息送到专员，再把回复取回来
    """
    # ---- 4.1 LLM 智能路由（业务决策，不属于 A2A 协议）----
    intent = classify_intent(query)
    print(f"🧑‍💼 主管意图判断（LLM）: {intent!r}")

    if intent not in AGENTS:
        print("🧑‍💼 主管: 抱歉，这个问题我暂时无法处理，已转人工客服。")
        return

    print(f"🧑‍💼 主管判断: 这是{'退货' if intent == 'return' else '物流'}问题，"
          f"分配给{'退货' if intent == 'return' else '物流'}专员。")

    # ---- 4.2 【名片】+【传输】创建 A2A 客户端 ----
    # 官方 SDK 要手写 create_client(url, ClientConfig(streaming=False))；
    # python-a2a 用 A2AClient(url) 一步到位，构造时内部就完成了：
    #   1. GET {url}/.well-known/agent.json 拉取名卡（【名片】服务发现）
    #   2. 把名片缓存到 client.agent_card，后续可读 skills / capabilities
    #   3. 准备好 HTTP 传输通道（【传输】）
    client = A2AClient(AGENTS[intent])

    # 读一下名卡，证明「动态发现」真的拿到了对方信息（而不是我们硬编码的）
    card = client.agent_card
    print(f"📇 已发现专员: {card.name} — {card.description}")
    if card.skills:
        s = card.skills[0]
        print(f"   技能: {s.name} / 标签 {s.tags}")

    # ---- 4.3 【任务】+【传输】发送消息并接收回复 ----
    # 官方 SDK 要自己构造 SendMessageRequest，再用
    #   async for resp in client.send_message(request): get_stream_response_text(resp)
    # 遍历流式响应；python-a2a 的 ask() 把这一整套收成一行，
    # 内部等价于「创建 Task → 发送消息 → 取出回复文本」。
    try:
        reply = client.ask(query)
        print(f"🤖 专员回复: {reply}")
    except Exception as e:
        print(f"❌ 调用专员失败: {type(e).__name__}: {e}")


# ====================================================================
# 第五部分：用 AgentNetwork 做「服务发现」（python-a2a 特有）
# ====================================================================
def discover_agents() -> AgentNetwork:
    """
    AgentNetwork 是 python-a2a 自带的专员注册表。

    官方 SDK 版的做法是自己维护一个 AGENTS = {"return": url, ...} 字典，
    地址是**硬编码**的。AgentNetwork 则提供了一层注册/发现抽象：
    添加后可以列出每个专员的 name / description / skills，
    真实项目里就可以据此做「按能力路由」，而不是写死 if-else。

    注意：专员必须先启动，否则注册时会连不上（日志里会有警告）。
    """
    network = AgentNetwork(name="客服专员网络")
    for name, url in AGENTS.items():
        network.add(name, url)   # 内部同样会去拉一次名片
    return network


# ====================================================================
# 第六部分：主函数 — 持续对话循环
# ====================================================================
def main() -> None:
    print("=" * 56)
    print("🧑‍💼 客服主管系统已启动（python-a2a 版）")
    print("📌 支持的问题类型：退货、退款、物流、快递、运送")
    print("📌 输入 'quit' 或 'exit' 退出")
    print("=" * 56)

    # ---- 6.1 先做一次服务发现，把专员能力亮出来 ----
    print("\n[服务发现] 通过 AgentNetwork 扫描专员…")
    network = discover_agents()
    for info in network.list_agents():
        print(f"  ✔ {info['name']:<10} {info.get('description', '')}")

    # ---- 6.2 对话循环 ----
    while True:
        try:
            user_input = input("\n您: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 再见！")
            break

        route_query(user_input, network)


# ====================================================================
# 第七部分：程序入口
# ====================================================================
if __name__ == "__main__":
    # 官方 SDK 版是 asyncio.run(main())，因为全链路异步；
    # python-a2a 是同步阻塞的 requests + Flask，所以直接调用即可。
    main()


"""
================================================================================
完整的客户端请求-响应流程

1. 用户在终端输入：「我想把东西退掉」

2. main() 收到输入，调用 route_query()

3. route_query() 内部：
   a. classify_intent("我想把东西退掉")
      → DeepSeek 做语义理解，返回 "return"
      （关键词版做不到这一点，因为句子里没有「退货」二字）

   b. 查 AGENTS["return"] → http://localhost:8003

   c. A2AClient("http://localhost:8003")
      → 内部 GET http://localhost:8003/.well-known/agent.json
      → 拿到名卡：发现对方叫「退货处理专员」，技能标签 ["退货","退款"]
      → 缓存到 client.agent_card（【名片】动态发现完成）

   d. client.ask(query)
      → 内部创建/继续一个 Task（分配 task_id）      【任务】
      → HTTP POST 到 http://localhost:8003/         【传输】
      → 专员侧 A2AServer.handle_task() 调用
        return_message_handler() 生成回复
      → 把回复文本取回来

4. 用户看到专员的回复


A2A 三大核心在客户端代码中的体现总结

┌─────────────┬──────────────────────────────────────────────────────────┐
│ 核心概念    │ 在代码中的具体体现                                        │
├─────────────┼──────────────────────────────────────────────────────────┤
│ 【名片】    │ A2AClient(url) 构造时自动 GET /.well-known/agent.json，    │
│ Agent Card  │ 结果缓存在 client.agent_card，可读 name/skills/tags。      │
│ 服务发现    │ AgentNetwork.add() 则把「发现到的专员」组织成注册表。      │
├─────────────┼──────────────────────────────────────────────────────────┤
│ 【任务】    │ client.ask() 内部完成 Task 的创建与结果归档；             │
│ Task        │ 服务端 A2AServer 也用 task_id / conversation_id 串多轮。  │
├─────────────┼──────────────────────────────────────────────────────────┤
│ 【传输】    │ HTTP 承载全部通信：客户端 requests，服务端 Flask。        │
│ Transport   │ 官方 SDK 版是 JSON-RPC + ASGI；                           │
│             │ python-a2a 是 REST 风格 + WSGI（线程）。                  │
└─────────────┴──────────────────────────────────────────────────────────┘


【附录】换库之后，哪些东西变了、哪些没变

没变的（协议层面的「契约」）：
    - 三大核心的概念划分：名片 / 任务 / 传输，两边都得有
    - 名片的作用：让客户端能动态发现专员，而不是靠硬编码
    - 端口的角色分工：专员是服务端（监听端口），主管是客户端
    - 业务逻辑与协议解耦：提示词、LLM 调用完全不因换库而改变

变了的（实现层面的「方言」）：
    - 名片发现路径：/.well-known/agent-card → /.well-known/agent.json
    - 传输风格：JSON-RPC（POST /）→ REST 风格（POST /）
    - Web 框架：Starlette + uvicorn（ASGI / async）→ Flask + werkzeug（WSGI / 线程）
    - 服务端扩展点：继承 AgentExecutor.execute() → 传一个 message_handler 函数
    - 任务存储：显式注入 InMemoryTaskStore → A2AServer 内置
    - 客户端调用：构造 SendMessageRequest + 遍历流 → client.ask() 一行

一句话总结：A2A 是「协议/契约」，它规定的是行为语义；具体某个 Python 库
只是这份契约的一种实现方言。换方言要改的是接线方式，不是系统架构。
================================================================================
"""
