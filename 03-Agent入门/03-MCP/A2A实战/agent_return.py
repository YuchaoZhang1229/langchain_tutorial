"""
================================================================================
A2A 协议服务端实现（python-a2a 版）— 退货处理专员
================================================================================

【角色定位】
专门处理退货/退款问题的垂直领域专家，作为 A2A 协议服务端对外暴露标准接口。

【本文件是官方 a2a SDK 版 agent_return.py 的等价改写】
功能一致，但把官方 SDK 的「三大核心」换成 python-a2a 的写法。
对照关系如下（右侧是本文件实际用到的东西）：

  官方 a2a SDK                         python-a2a                  本文件位置
  ─────────────────────────────────    ──────────────────────      ──────────────
  AgentCard + AgentInterface           AgentCard(url=...)          【名片】第四部分
  AgentCapabilities(...)               capabilities={"...": ...}   【名片】第四部分
  AgentSkill(id=..., tags=[...])       AgentSkill(name, tags=[...])【名片】第四部分
  AgentExecutor.execute(ctx, queue)    message_handler(msg)->msg   【任务】第三部分
  RequestContext.get_user_input()      message.content.text        【任务】第三部分
  EventQueue.enqueue_event(...)        直接 return Message(...)     【任务】第三部分
  InMemoryTaskStore()                  A2AServer 内置 self.tasks    【任务】第二部分
  DefaultRequestHandler(...)           A2AServer(agent_card, ...)  【任务】第二部分
  create_agent_card_routes(card)       框架内置，无需注册          【传输】第五部分
  create_jsonrpc_routes(handler, "/")  框架内置 /a2a               【传输】第五部分
  create_rest_routes(handler)          框架内置 /a2a/tasks/*       【传输】第五部分
  uvicorn.run(app, port=8003)          run_server(server, port=)   【传输】第五部分

【运行】
    D:\\llmsvirtulenv\\a2a_customer\\Scripts\\python.exe agent_return.py
================================================================================
"""
import logging

# ====================================================================
# 第一部分：导入 python-a2a 的「三大核心」类型
# ====================================================================
from python_a2a import (
    # 【名片】智能体名片：描述「我是谁、我能做什么、怎么联系我」
    AgentCard,
    # 【名片】单个技能：name / description / tags / examples
    AgentSkill,
    # 【任务】消息与角色：handler 的入参和出参都是 Message
    Message,
    # 【任务】回复消息的角色标记（官方 SDK 里是 Role.ROLE_AGENT）
    MessageRole,
    # 【任务】文本内容载体（官方 SDK 里是 new_text_message() 的 parts）
    TextContent,
    # 【任务】+【传输】服务器本体：内置了请求处理与任务存储
    A2AServer,
    # 【传输】启动 HTTP 服务（Flask/WSGI）
    run_server,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================================================================
# 第二部分：业务层 — 退货专员的系统提示词
# ====================================================================
# 这段提示词不属于 A2A 协议，只用于指导大模型以「退货专员」的身份回复。
# 与官方 SDK 版完全一致（业务逻辑不因换协议库而改变）。
RETURN_SYSTEM_PROMPT = """你是一个专业的电商退货处理专员。你的职责是帮助用户处理退货和退款问题。
要求：
1. 热情、耐心、专业地回复用户
2. 引导用户提供必要信息：订单号、退货原因、商品名称等
3. 如果用户情绪激动，先安抚再处理问题
4. 回复简洁有条理，不超过200字
5. 在回复中体现你的角色身份：退货处理专员"""


# ====================================================================
# 第三部分：【任务】核心 — message_handler（对应官方的 AgentExecutor）
# ====================================================================
# 官方 SDK 里你要继承 AgentExecutor 并实现 execute(context, event_queue)；
# python-a2a 里你只写一个普通函数，接收 Message、返回 Message。
#
# 三处关键差异：
#   1. 入参不是 RequestContext，而是 Message 本身
#      用户输入 = message.content.text（官方是 context.get_user_input()）
#   2. 没有 EventQueue — 直接把结果 return 出去，框架负责归档
#   3. 是**同步函数**（Flask 线程模型），不是 async def
#
# 少掉的那些样板代码（Task 创建、事件入队、结果归档）python-a2a 的
# A2AServer 在内部都做了，所以这里的代码比官方版短得多。
# ====================================================================
def return_message_handler(message: Message) -> Message:
    """退货专员的业务逻辑：把用户问题交给 DeepSeek，返回专员回复。"""
    # 延迟导入，避免与 llm_client 形成循环依赖（与官方版做法一致）
    from llm_client import chat

    # ---- 3.1 从【任务】消息中提取用户输入 ----
    # 对应官方的 context.get_user_input()
    query = message.content.text if message.content.type == "text" else ""
    logger.info(f"退货专员收到问题: {query}")

    if not query:
        return Message(
            content=TextContent(text="您好，我没有收到具体的问题描述，请再说一次～"),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )

    # ---- 3.2 调用大模型生成回复（业务处理）----
    reply_text = chat(RETURN_SYSTEM_PROMPT, query)
    logger.info(f"退货专员 AI 回复: {reply_text[:50]}...")

    # ---- 3.3 返回标准 A2A 消息 ----
    # 对应官方的 event_queue.enqueue_event(new_text_message(...))：
    # 官方要手动传 context_id / task_id，python-a2a 通过 parent_message_id 和
    # conversation_id 关联上下文，框架据此把回复归到同一条会话/任务下。
    return Message(
        content=TextContent(text=reply_text),
        role=MessageRole.AGENT,
        parent_message_id=message.message_id,     # 【任务】回应的是哪条消息
        conversation_id=message.conversation_id,  # 【任务】同一条会话串起来（多轮）
    )


# ====================================================================
# 第四部分：【名片】定义 Agent Card
# ====================================================================
# 名片的作用与会话官方版相同：让调用方（Supervisor）能「发现」我。
# 差别在于字段的组织方式：
#   - 官方版把地址放在 supported_interfaces=[AgentInterface(url=..., protocol_binding="JSONRPC")]
#   - python-a2a 直接把 url 放在 AgentCard 上，协议绑定固定为 A2A over HTTP
#   - capabilities 用普通 dict 表达（官方版是 AgentCapabilities 消息体）
# ====================================================================
agent_card = AgentCard(
    # ---- 4.1 基本身份信息 ----
    name="退货处理专员",
    description="专门处理商品退货咨询的AI助手，由 DeepSeek 大模型驱动",
    version="1.1.0",

    # ---- 4.2 【名片】【传输】服务地址 ----
    # 注意这里是「裸地址」，**不要**写成 http://localhost:8003/a2a
    # 原因（实测踩过的坑）：
    #   A2AClient 发现名片时会按顺序试这三个地址：
    #     {url}/.well-known/agent.json
    #     {url}/agent.json
    #     {url}/a2a/agent.json
    #   而 python-a2a 的 A2AServer 把「人类可读的 HTML 说明页」挂在了
    #   /a2a 与 /a2a/.well-known/agent.json 上，只有
    #   /.well-known/agent.json 和 /agent.json 才返回干净的名片 JSON。
    #   所以一旦 url 带上 /a2a，客户端第一个探测到的就是 HTML 页面，
    #   它只能从 HTML 里勉强抠出一个残缺的名片 —— 表现为
    #   「name/description 正常，但 skills 是空的」。
    url="http://localhost:8003",

    # ---- 4.3 【名片】技术能力标签 ----
    # 官方版用 AgentCapabilities(streaming=..., push_notifications=...)；
    # 这里用等价 dict。
    # 注意：python-a2a 的 A2AServer 在构造时会强行把 streaming 置为 True
    # （因为它确实提供了 /a2a/tasks/stream 这个 SSE 端点），
    # 所以最终对外公布的名片里 streaming 是 true，这里写 false 会被覆盖。
    capabilities={
        "streaming": False,           # → 会被 A2AServer 覆盖为 True
        "push_notifications": False,  # 不支持推送（这个会保留）
    },

    # ---- 4.4 【名片】输入输出格式声明 ----
    default_input_modes=["text"],   # 只接受文本输入
    default_output_modes=["text"],  # 只输出文本结果

    # ---- 4.5 【名片】技能列表（核心竞争力）----
    # 客户端可以据此做更精细的路由。
    # 注意：官方版的 AgentSkill 有 id 字段，python-a2a 用 name 作为标识。
    skills=[
        AgentSkill(
            name="处理退货",                              # 技能名称（兼作标识）
            description="回答所有关于退货退款的问题",
            tags=["退货", "退款"],                        # 标签，便于关键词匹配
            examples=["我要退货", "这件商品怎么退款？"],   # 示例问题（python-a2a 特有）
        )
    ],
)


# ====================================================================
# 第五部分：【任务】+【传输】组装并启动服务

# python-a2a 把这些全部收进 A2AServer 内部，一行构造、一行启动：
#   A2AServer 自带【任务】存储（self.tasks）与请求处理（handle_task），
#   并自动注册【传输】路由：
#     GET  /.well-known/agent.json   【名片】发现端点
#     POST /a2a                      发送消息（主入口）
#     POST /a2a/tasks/send           创建任务
#     GET  /a2a/tasks/{id}           查询任务
#     POST /a2a/tasks/cancel         取消任务
#     POST /a2a/tasks/stream         流式（SSE）
# ====================================================================
server = A2AServer(
    agent_card=agent_card,
    message_handler=return_message_handler,   # 【任务】注入业务逻辑
)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("退货处理专员服务已启动（python-a2a 版）")
    logger.info("  - 服务地址: http://0.0.0.0:8003")
    logger.info("  - 名片发现: http://localhost:8003/.well-known/agent.json  ← 客户端用这个")
    logger.info("  - 消息入口: http://localhost:8003/ (POST)")
    logger.info("  - HTML 说明页: http://localhost:8003/a2a")
    logger.info("=" * 60)

    # 【传输】启动 Flask 服务；port 必须与 AgentCard.url 里的端口一致
    run_server(server, host="0.0.0.0", port=8003)


"""
================================================================================
完整的请求-响应流程（从 HTTP 到业务逻辑）

1. 客户端（Supervisor）发起请求：POST http://localhost:8003/a2a

2. Flask 接收到 HTTP 请求，路由分发

3. A2AServer.handle_task() 解析请求
   a. 从请求中取出 Message
   b. 生成/复用 task_id、conversation_id，存入内置的任务存储（self.tasks）
   c. 调用我们注入的 message_handler(message)

4. return_message_handler() 执行业务逻辑
   a. message.content.text 取出用户输入
   b. 调用 llm_client.chat() 生成回复
   c. return Message(...) 返回结果

5. A2AServer 把回复包装成响应，写回 HTTP 连接

6. 客户端的 client.ask() 拿到文本，展示给用户

【三大核心的协作关系】

【名片】Agent Card：
   客户端通过 GET /.well-known/agent.json 发现服务。
   （注意：路径与官方 SDK 的 /.well-known/agent-card 不同，这是两个库各自的约定。
     另外 /a2a/.well-known/agent.json 返回的是 HTML 说明页而不是 JSON，
     所以 AgentCard.url 里不要带 /a2a）

【任务】Task：
   A2AServer 内置 Task 存储与 /a2a/tasks/* 端点，
   通过 task_id / conversation_id 关联多轮会话。
   官方 SDK 需要你显式注入 InMemoryTaskStore。

【传输】Transport：
   HTTP 承载全部通信，但底层框架不同：
     官方 SDK → Starlette + uvicorn（ASGI，异步，JSON-RPC）
     python-a2a → Flask + werkzeug（WSGI，线程，REST 风格）
================================================================================
"""
