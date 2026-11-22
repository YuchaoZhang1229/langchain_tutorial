"""
================================================================================
A2A 协议服务端实现（python-a2a 版）— 物流查询专员
================================================================================

【角色定位】
专门处理物流/快递查询的 AI 智能体，作为 A2A 协议服务端对外暴露标准接口。

【与 agent_return.py 的关系】
本模块是 agent_return.py 的对称实现，二者结构完全一致，
仅在业务提示词（SHIPPING_SYSTEM_PROMPT）和名片信息（name / skills / 端口）上有所区分。
这种设计体现了 A2A 协议的核心理念：同一套框架支撑不同的业务能力。

关于「官方 a2a SDK ↔ python-a2a」的完整概念对照表、以及
【名片】【任务】【传输】三大核心的详细讲解，请直接看 agent_return.py 的注释，
本文件不再重复，只保留关键节点标记。

【端口分配】
    退货专员 agent_return.py   → 8003
    物流专员 agent_shipping.py → 8004
    Supervisor 不监听端口，它只是客户端。

【运行】
    D:\\llmsvirtulenv\\a2a_customer\\Scripts\\python.exe agent_shipping.py
================================================================================
"""
import logging

# 【名片】AgentCard / AgentSkill  【任务】Message / MessageRole / TextContent
# 【任务】【传输】A2AServer        【传输】run_server
from python_a2a import (
    AgentCard,
    AgentSkill,
    A2AServer,
    Message,
    MessageRole,
    TextContent,
    run_server,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================================================================
# 第一部分：业务层 — 物流查询专员的系统提示词
# ====================================================================
# 不属于 A2A 协议，只用于指导大模型以「物流查询专员」的身份回复。
SHIPPING_SYSTEM_PROMPT = """你是一个专业的物流查询专员。你的职责是帮助用户查询快递物流信息。
要求：
1. 热情、耐心、专业地回复用户
2. 引导用户提供必要信息：快递单号、收件人姓名、发货时间等
3. 根据用户描述给出物流查询指引或预估时效
4. 如果用户催件或抱怨物流慢，先安抚再帮助解决
5. 回复简洁有条理，不超过200字
6. 在回复中体现你的角色身份：物流查询专员"""


# ====================================================================
# 第二部分：【任务】核心 — message_handler（对应官方的 AgentExecutor）
# ====================================================================
# 同步函数，收 Message 返 Message；Task 管理由 A2AServer 内部完成。
# ====================================================================
def shipping_message_handler(message: Message) -> Message:
    """物流专员的业务逻辑：把用户问题交给 DeepSeek，返回专员回复。"""
    from llm_client import chat

    # 【任务】取出用户输入（官方 SDK 是 context.get_user_input()）
    query = message.content.text if message.content.type == "text" else ""
    logger.info(f"物流专员收到问题: {query}")

    if not query:
        return Message(
            content=TextContent(text="您好，请问您想查询哪一单快递呢？"),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id,
        )

    reply_text = chat(SHIPPING_SYSTEM_PROMPT, query)
    logger.info(f"物流专员 AI 回复: {reply_text[:50]}...")

    # 直接 return 结果（官方 SDK 是 event_queue.enqueue_event(...)）
    return Message(
        content=TextContent(text=reply_text),
        role=MessageRole.AGENT,
        parent_message_id=message.message_id,     # 【任务】回应哪条消息
        conversation_id=message.conversation_id,  # 【任务】会话串联（多轮）
    )


# ====================================================================
# 第三部分：【名片】定义 Agent Card
# ====================================================================
# 注意 url 用裸地址，不要带 /a2a —— 否则客户端发现到的是 HTML 说明页，
# 抠出来的名片会缺 skills。详见 agent_return.py 第 4.2 节。
agent_card = AgentCard(
    # ---- 基本身份信息 ----
    name="物流查询专员",
    description="专门处理物流信息查询的AI助手，由 DeepSeek 大模型驱动",
    version="1.1.0",

    # ---- 【名片】【传输】服务地址（裸地址！）----
    url="http://localhost:8004",

    # ---- 【名片】技术能力标签 ----
    capabilities={
        "streaming": False,           # → 会被 A2AServer 覆盖为 True
        "push_notifications": False,
    },

    # ---- 【名片】输入输出格式声明 ----
    default_input_modes=["text"],
    default_output_modes=["text"],

    # ---- 【名片】技能列表 ----
    # 客户端可以据此做更精细的路由：比如 Supervisor 也可以不看 LLM，
    # 直接靠这里的 tags 做关键词匹配 —— 这正是 tags 存在的意义。
    skills=[
        AgentSkill(
            name="查询物流",
            description="回答所有关于物流查询的问题",
            tags=["物流", "快递", "运送"],
            examples=["我的包裹到哪了", "快递什么时候能到"],
        )
    ],
)


# ====================================================================
# 第四部分：【任务】+【传输】组装并启动服务
# ====================================================================
# A2AServer 自带任务存储与请求处理，并自动注册这些【传输】路由：
#   GET  /.well-known/agent.json   名片发现（返回 JSON）
#   GET  /a2a                      人类可读的 HTML 说明页
#   POST /                         发送消息（主入口）
#   POST /a2a/tasks/send           创建任务    GET /a2a/tasks/{id}  查询任务
#   POST /a2a/tasks/cancel         取消任务    POST /a2a/tasks/stream 流式(SSE)
server = A2AServer(
    agent_card=agent_card,
    message_handler=shipping_message_handler,   # 【任务】注入业务逻辑
)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("物流查询专员服务已启动（python-a2a 版）")
    logger.info("  - 服务地址: http://0.0.0.0:8004")
    logger.info("  - 名片发现: http://localhost:8004/.well-known/agent.json  ← 客户端用这个")
    logger.info("  - 消息入口: http://localhost:8004/ (POST)")
    logger.info("  - HTML 说明页: http://localhost:8004/a2a")
    logger.info("=" * 60)

    # 【传输】启动 Flask 服务；port 必须与 AgentCard.url 里的端口一致
    run_server(server, host="0.0.0.0", port=8004)
