import os
import sys
import asyncio
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


# ---------- 环境校验 ----------
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("请在 .env 中设置 DASHSCOPE_API_KEY")

# ---------- MCP 客户端封装 ----------
async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """异步调用 MCP Server"""
    # server_params = StdioServerParameters(
    #     command=sys.executable,
    #     args=["server.py"]
    # )
    server_params = StdioTransport(
        command=sys.executable,
        args=["mcp_server.py"]
    )
    # async with stdio_client(server_params) as (read, write):
    #     async with ClientSession(read, write) as session:
    #         await session.initialize()
    # result = await session.call_tool(tool_name, arguments=arguments)
    async with Client(server_params) as client:
        result = await client.call_tool(tool_name, arguments=arguments)
        if result.content and hasattr(result.content[0], "text"):
            return result.content[0].text
        return str(result.content)

def sync_call_mcp(tool_name: str, arguments: dict) -> str:
    """同步包装器，供 LangChain 工具调用（每次调用启动新子进程）"""
    return asyncio.run(call_mcp_tool(tool_name, arguments))

# ---------- 定义 LangChain 工具 ----------
@tool
def fetch_stock(symbol: str) -> str:
    """获取指定股票的最近5日行情，参数 symbol 为股票代码（如 AAPL）"""
    return sync_call_mcp("fetch_stock", {"symbol": symbol})

@tool
def technical_analysis(symbol: str) -> str:
    """计算指定股票的 RSI、SMA 等技术指标，参数 symbol 为股票代码"""
    return sync_call_mcp("technical_analysis", {"symbol": symbol})

@tool
def get_company_info(symbol: str) -> str:
    """获取公司基本面信息（市值、PE、行业等），参数 symbol 为股票代码"""
    return sync_call_mcp("get_company_info", {"symbol": symbol})

tools = [fetch_stock, technical_analysis, get_company_info]

# ---------- 创建 LLM ----------
llm = ChatOpenAI(
    model="qwen3.7-plus",          # 可换 gpt-4o / deepseek-chat
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0
)

# ---------- 使用 create_agent 直接创建智能体 ----------
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="你是一位专业的股票分析助手。请根据用户需求，精准调用对应的工具来获取股票数据，并给出清晰的分析结论。"
)

# ---------- 主入口 ----------
if __name__ == "__main__":
    query = "帮我分析一下 NVDA 的近期走势和技术指标，另外告诉我它的市盈率"
    print(f"用户提问: {query}\n" + "="*50)

    # 调用 agent.invoke，输入格式为 {"messages": [...]}
    result = agent.invoke({
        "messages": [
            {"role": "user", "content": query}
        ]
    })

    print("\n" + "="*50)
    # 最终回答在 messages 列表的最后一条中
    print("最终回答:\n", result["messages"][-1].content)