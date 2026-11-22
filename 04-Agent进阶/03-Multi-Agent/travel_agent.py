"""
旅行agent要查询机票信息，需要Time和Kiwi两个MCP服务。

"""

import asyncio
import logging
import os

import httpx
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

# ⭐ 代理开关：httpx 默认 trust_env=True，会自动读 HTTP_PROXY / HTTPS_PROXY。
# 一旦这些环境变量指向失效端口（Clash 换端口、残留的临时端口），请求就会在
# TLS 握手阶段抛 httpx.ConnectError。这里显式接管连接方式：
#   - 默认直连（trust_env=False，彻底不看环境变量）
#   - 需要走代理时先设环境变量，例：$env:MCP_PROXY = "http://127.0.0.1:7890"
MCP_PROXY = os.getenv("MCP_PROXY", "").strip()


def mcp_http_client(headers=None, timeout=None, auth=None) -> httpx.AsyncClient:
    """streamable-http 传输用的 httpx 客户端工厂，MCP 适配器建连时会回调它。"""
    return httpx.AsyncClient(
        headers=headers,
        timeout=timeout,
        auth=auth,
        trust_env=False,           # ⭐ 不读 HTTP_PROXY/HTTPS_PROXY，避免代理污染
        proxy=MCP_PROXY or None,   # ⭐ 只有显式设置 MCP_PROXY 才走代理
        follow_redirects=True,
    )


# 连接Kiwi MCP服务器
client = MultiServerMCPClient(
    {
        "time": {
            "transport": "stdio",  # 通信方式，可选值有stdio、http或者streamable_http
            "command": "uvx",  # 基于uv(python的uv工具)的包管理工具，用于下载和运行MCP服务
            "args": [  # 运行MCP服务的参数
                "mcp-server-time",
                "--local-timezone=Asia/Shanghai"
            ]
        },
        "kiwi-com-flight-search": {
            "transport": "http",
            "url": "https://mcp.kiwi.com",
            "httpx_client_factory": mcp_http_client,  # ⭐ 用上面的工厂接管连接
            "timeout": 30,                            # ⭐ 跨境请求，超时放宽到 30s
        }
    }
)

_agent = None


async def _load_tools(server_name: str):
    """按 server 单独加载工具。

    client.get_tools() 默认用 asyncio.gather 并发加载所有 server，任何一个失败都会
    连带取消另一个（stdio 的 time 子进程被打断，冒出一堆 OSError: [Errno 22] 噪音），
    真正的原因被淹没。拆开逐个加载，才能看清到底是谁挂了。
    """
    try:
        tools = await client.get_tools(server_name=server_name)
    except Exception as e:  # noqa: BLE001
        # ⚠️ 适配器 0.3.2 的连接失败会把真正的 httpx 异常吞掉，只抛
        # UnboundLocalError: cannot access local variable 'tools'
        # 所以这里把原始异常链和排查提示一起带上。
        logger.error("MCP server %r 加载失败: %s: %s", server_name, type(e).__name__, e)
        raise RuntimeError(
            f"MCP server {server_name!r} 连接失败（通常是网络或代理问题）。"
            f"直连不通时先设环境变量 MCP_PROXY='http://127.0.0.1:7890' 再跑。"
        ) from e
    logger.warning("MCP server %r 已加载 %d 个工具", server_name, len(tools))
    return tools


async def get_travel_agent():             # 惰性初始化，在真实运行的循环里建连
    global _agent
    if _agent is None:
        tools = [
            *await _load_tools("time"),
            *await _load_tools("kiwi-com-flight-search"),
        ]
        _agent = create_agent(
            model="deepseek-v4-flash",
            tools=tools,
            system_prompt="""
            你是一个旅行助手Agent。你为用户搜索到达婚礼地点的理想航班，您不能再追问任何后续问题。
            您必须根据以下标准找到最佳航班选择：
            - 价格（最低，经济舱）
            - 持续时间（最短）
            - 日期（您认为在该地点举行婚礼的最佳时间）
            为了使事情变得简单，只寻找一张票，单程。
            你不会得到额外的信息，只有出发地和目的地。你的工作是批判性地思考最佳选择。
            一旦你找到了最好的选项，让用户知道你的候选列表。
            调用搜索航班工具时，如果是地点在中国，需要使用zh-cn作为Locale参数。
            """
        )
    return _agent


if __name__ == "__main__":
    async def run_agent():
        travel_agent = await get_travel_agent()
        print("🚀 Starting agent...")
        response = await travel_agent.ainvoke({
            "messages": [HumanMessage("查一下2026年11月10日晚上从上海飞成都的航班?")]
        })
        for message in response["messages"]:
            message.pretty_print()
    asyncio.run(run_agent())