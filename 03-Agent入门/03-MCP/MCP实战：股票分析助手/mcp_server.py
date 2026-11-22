# ==============================================================================
# 下面是「底层 API 版」—— 手写 list_tools / call_tool，保留作对照，已停用。
# 新版（FastMCP 版）在本文件下半部分。
# ==============================================================================
#
# import asyncio
# from mcp.server import Server
# from mcp.server.models import InitializationOptions
# import mcp.server.stdio
# import mcp.types as types
#
# server = Server("stock-analysis-mcp")
#
# # ---------- 模拟数据库 ----------
# FAKE_DATA = {
#     "NVDA": {
#         "price": 128.34,
#         "change": "+2.3%",
#         "pe": 68.2,
#         "sma20": 125.10,
#         "sma50": 118.60,
#         "rsi": 62.5,
#         "company": "NVIDIA Corporation",
#         "industry": "Semiconductors",
#         "market_cap": 3150000000000,
#         "week52_high": 140.50,
#         "week52_low": 95.20,
#         "recent": [
#             {"date": "2026-08-14", "open": 127.00, "high": 129.50, "low": 126.50, "close": 128.34, "volume": 85000000},
#             {"date": "2026-08-13", "open": 125.80, "high": 127.20, "low": 125.20, "close": 126.90, "volume": 72000000},
#             {"date": "2026-08-12", "open": 124.50, "high": 126.00, "low": 124.00, "close": 125.50, "volume": 68000000},
#             {"date": "2026-08-11", "open": 123.20, "high": 125.00, "low": 122.80, "close": 124.70, "volume": 65000000},
#             {"date": "2026-08-10", "open": 122.00, "high": 123.50, "low": 121.80, "close": 123.10, "volume": 61000000}
#         ]
#     },
#     "AAPL": {
#         "price": 175.50,
#         "change": "+1.2%",
#         "pe": 28.5,
#         "sma20": 172.30,
#         "sma50": 168.90,
#         "rsi": 58.0,
#         "company": "Apple Inc.",
#         "industry": "Consumer Electronics",
#         "market_cap": 2800000000000,
#         "week52_high": 180.00,
#         "week52_low": 145.00,
#         "recent": [
#             {"date": "2026-08-14", "open": 174.80, "high": 176.50, "low": 174.20, "close": 175.50, "volume": 55000000},
#             {"date": "2026-08-13", "open": 173.50, "high": 175.00, "low": 173.00, "close": 174.60, "volume": 48000000},
#         ]
#     }
# }
#
# @server.list_tools()
# async def handle_list_tools() -> list[types.Tool]:
#     return [
#         types.Tool(
#             name="fetch_stock",
#             description="获取指定股票（如 AAPL、NVDA）最近5天的OHLCV行情数据",
#             inputSchema={
#                 "type": "object",
#                 "properties": {
#                     "symbol": {"type": "string", "description": "股票代码，如 AAPL"}
#                 },
#                 "required": ["symbol"]
#             }
#         ),
#         types.Tool(
#             name="technical_analysis",
#             description="计算指定股票的RSI、SMA(20)、SMA(50)技术指标",
#             inputSchema={
#                 "type": "object",
#                 "properties": {
#                     "symbol": {"type": "string", "description": "股票代码，如 NVDA"}
#                 },
#                 "required": ["symbol"]
#             }
#         ),
#         types.Tool(
#             name="get_company_info",
#             description="获取公司名称、行业、市值、市盈率(PE)、52周高低点",
#             inputSchema={
#                 "type": "object",
#                 "properties": {
#                     "symbol": {"type": "string", "description": "股票代码，如 MSFT"}
#                 },
#                 "required": ["symbol"]
#             }
#         )
#     ]
#
# @server.call_tool()
# async def handle_call_tool(
#     name: str, arguments: dict | None
# ) -> list[types.TextContent]:
#     if not arguments:
#         arguments = {}
#
#     symbol = arguments.get("symbol", "").upper()
#     if symbol not in FAKE_DATA:
#         return [types.TextContent(type="text", text=f"未找到 {symbol} 的数据（模拟数据中暂无此股票）")]
#
#     data = FAKE_DATA[symbol]
#
#     if name == "fetch_stock":
#         # 格式化最近5日行情
#         lines = [f"{symbol} 最近5日行情:"]
#         for row in data["recent"][:5]:
#             lines.append(
#                 f"{row['date']}  O:{row['open']:.2f}  H:{row['high']:.2f}  L:{row['low']:.2f}  C:{row['close']:.2f}  V:{row['volume']:,}"
#             )
#         return [types.TextContent(type="text", text="\n".join(lines))]
#
#     elif name == "technical_analysis":
#         return [types.TextContent(
#             type="text",
#             text=(
#                 f"{symbol} 技术指标:\n"
#                 f"• 当前价格: ${data['price']:.2f}\n"
#                 f"• RSI(14): {data['rsi']:.1f}\n"
#                 f"• SMA(20): ${data['sma20']:.2f}\n"
#                 f"• SMA(50): ${data['sma50']:.2f}\n"
#                 f"• 价格 vs SMA20: {' 高于' if data['price'] > data['sma20'] else '📉 低于'}"
#             )
#         )]
#
#     elif name == "get_company_info":
#         return [types.TextContent(
#             type="text",
#             text=(
#                 f"{symbol} 公司信息:\n"
#                 f"• 名称: {data['company']}\n"
#                 f"• 行业: {data['industry']}\n"
#                 f"• 市值: ${data['market_cap']:,}\n"
#                 f"• 市盈率(PE): {data['pe']}\n"
#                 f"• 52周高: ${data['week52_high']:.2f}\n"
#                 f"• 52周低: ${data['week52_low']:.2f}"
#             )
#         )]
#
#     else:
#         return [types.TextContent(type="text", text=f"❌ 未知工具: {name}")]
#
# async def main():
#     async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
#         await server.run(
#             read_stream,
#             write_stream,
#             InitializationOptions(
#                 server_name="stock-analysis-mcp",
#                 server_version="1.0.0",
#                 capabilities=types.ServerCapabilities(
#                     tools=types.ToolsCapability(listChanged=False)
#                 )
#             )
#         )
#
# if __name__ == "__main__":
#     asyncio.run(main())


# ==============================================================================
# MCP Server（FastMCP 版）—— 股票分析助手，通过 stdio 与客户端通信
# ==============================================================================
"""
对外提供三个工具：
    1. fetch_stock          获取最近5日 OHLCV 行情
    2. technical_analysis   计算 RSI / SMA(20) / SMA(50)
    3. get_company_info     公司名称、行业、市值、PE、52周高低

与底层 API 版的差异：
    - 工具定义从手写 types.Tool + JSON Schema → @mcp.tool 装饰器自动生成
    - 调用分发从手写 if/elif 按 name 分支 → 装饰器自动按函数名路由
    - 返回值从手写 [types.TextContent(type="text", ...)] 包装 → 直接 return 字符串
    - 启动代码从手写 InitializationOptions + stdio_server() → mcp.run() 一行
    - 未找到股票的处理从「在每个分支前统一拦截」→ 下沉到各工具内部（见 _lookup）

【参数说明为什么要用 Annotated + Field】
底层 API 版的 inputSchema 是手写的，"symbol" 上带着 description：
    {"symbol": {"type": "string", "description": "股票代码，如 AAPL"}}

换成 FastMCP 后，如果只在 docstring 里写一段 "Args: symbol: ..."，
**这个版本的 FastMCP 并不会去解析 Args 段**（实测 mcp 1.30 的行为）：
它会把整段 docstring 原样当作工具描述塞进去，而参数上的 description 反而丢了。
表现为工具描述里混着 "\n\n    Args:\n        symbol: ..." 这种噪音。

正确做法是用 Annotated + pydantic Field 显式写参数说明：
    symbol: Annotated[str, Field(description="股票代码，如 AAPL")]
这样既能得到干净的单行工具描述，又能把 description 正确写进 inputSchema。

客户端完全不用改：agent_langchain.py 里的 MCP 客户端代码一行都没动，
因为换掉的只是服务端的写法，协议层（stdio + MCP）是同一套。
"""

from typing import Annotated # 给类型附加元数据
from pydantic import Field
# from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP

"""
1. 股票分析 ——> 工具调用 ——> MCP协议来提供统一服务
- 描述--能力--
- 具体的视线
- 访问到服务，并且拿到结果
"""


# 创建 MCP Server 实例
mcp = FastMCP("stock-analysis-mcp")

# ---------- 模拟数据库 ----------
FAKE_DATA = {
    "NVDA": {
        "price": 128.34,
        "change": "+2.3%",
        "pe": 68.2,
        "sma20": 125.10,
        "sma50": 118.60,
        "rsi": 62.5,
        "company": "NVIDIA Corporation",
        "industry": "Semiconductors",
        "market_cap": 3150000000000,
        "week52_high": 140.50,
        "week52_low": 95.20,
        "recent": [
            {"date": "2026-08-14", "open": 127.00, "high": 129.50, "low": 126.50, "close": 128.34, "volume": 85000000},
            {"date": "2026-08-13", "open": 125.80, "high": 127.20, "low": 125.20, "close": 126.90, "volume": 72000000},
            {"date": "2026-08-12", "open": 124.50, "high": 126.00, "low": 124.00, "close": 125.50, "volume": 68000000},
            {"date": "2026-08-11", "open": 123.20, "high": 125.00, "low": 122.80, "close": 124.70, "volume": 65000000},
            {"date": "2026-08-10", "open": 122.00, "high": 123.50, "low": 121.80, "close": 123.10, "volume": 61000000},
        ],
    },
    "AAPL": {
        "price": 175.50,
        "change": "+1.2%",
        "pe": 28.5,
        "sma20": 172.30,
        "sma50": 168.90,
        "rsi": 58.0,
        "company": "Apple Inc.",
        "industry": "Consumer Electronics",
        "market_cap": 2800000000000,
        "week52_high": 180.00,
        "week52_low": 145.00,
        "recent": [
            {"date": "2026-08-14", "open": 174.80, "high": 176.50, "low": 174.20, "close": 175.50, "volume": 55000000},
            {"date": "2026-08-13", "open": 173.50, "high": 175.00, "low": 173.00, "close": 174.60, "volume": 48000000},
        ],
    },
}

NOT_FOUND_FMT = "未找到 {symbol} 的数据（模拟数据中暂无此股票）"


def _lookup(symbol: str) -> dict | None:
    """按代码取数据；调用方用 None 判断是否命中。"""
    return FAKE_DATA.get(symbol.strip().upper())


@mcp.tool()
def fetch_stock(
    symbol: Annotated[str, Field(description="股票代码，如 AAPL")],
) -> str:
    """获取指定股票（如 AAPL、NVDA）最近5天的OHLCV行情数据。"""
    data = _lookup(symbol)
    if data is None:
        return NOT_FOUND_FMT.format(symbol=symbol.strip().upper())

    lines = [f"{symbol.strip().upper()} 最近5日行情:"]
    for row in data["recent"][:5]:
        lines.append(
            f"{row['date']}  O:{row['open']:.2f}  H:{row['high']:.2f}  "
            f"L:{row['low']:.2f}  C:{row['close']:.2f}  V:{row['volume']:,}"
        )
    return "\n".join(lines)
"""
@mcp.tool() 装饰器自动做四件事：
- 从函数名 fetch_stock 生成工具名；
- 从 docstring 生成工具描述（这里就是"获取指定股票…最近5天的OHLCV行情数据。"这句）；
- 从 Annotated[str, Field(description=...)] 生成 inputSchema；
- 返回的 str 自动包装成 [types.TextContent(type="text", text=...)]，你只管 return 字符串。
"""


@mcp.tool()
def technical_analysis(
    symbol: Annotated[str, Field(description="股票代码，如 NVDA")],
) -> str:
    """计算指定股票的RSI、SMA(20)、SMA(50)技术指标。"""
    data = _lookup(symbol)
    if data is None:
        return NOT_FOUND_FMT.format(symbol=symbol.strip().upper())

    sym = symbol.strip().upper()
    above = "高于" if data["price"] > data["sma20"] else "低于"
    return (
        f"{sym} 技术指标:\n"
        f"• 当前价格: ${data['price']:.2f}\n"
        f"• RSI(14): {data['rsi']:.1f}\n"
        f"• SMA(20): ${data['sma20']:.2f}\n"
        f"• SMA(50): ${data['sma50']:.2f}\n"
        f"• 价格 vs SMA20: {above}"
    )


@mcp.tool()
def get_company_info(
    symbol: Annotated[str, Field(description="股票代码，如 MSFT")],
) -> str:
    """获取公司名称、行业、市值、市盈率(PE)、52周高低点。"""
    data = _lookup(symbol)
    if data is None:
        return NOT_FOUND_FMT.format(symbol=symbol.strip().upper())

    sym = symbol.strip().upper()
    return (
        f"{sym} 公司信息:\n"
        f"• 名称: {data['company']}\n"
        f"• 行业: {data['industry']}\n"
        f"• 市值: ${data['market_cap']:,}\n"
        f"• 市盈率(PE): {data['pe']}\n"
        f"• 52周高: ${data['week52_high']:.2f}\n"
        f"• 52周低: ${data['week52_low']:.2f}"
    )


if __name__ == "__main__":
    # 默认使用 stdio transport —— 与原来的 mcp.server.stdio.stdio_server() 等价
    mcp.run()
