"""
Deep Agents 架构使用工具实战


使用工具可视化工具LangSmith配置

"""
import os
os.environ["NO_PROXY"] = "localhost,127.0.0.1,0.0.0.0"
os.environ["no_proxy"] = "localhost,127.0.0.1,0.0.0.0"

import asyncio
import sys

from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent

"""
Deep Agents
    完全支持模型上下文协议（MCP），这是连接Agent到外部服务的开放标准。从任何 MCP 服务器加载工具，并直接传递给 create_deep_agent 。

MCP 是一个开放协议，它允许Agent通过标准接口连接到一个不断增长的生态系统 ———— 数据库、API、文件系统、浏览器等。
    与其为每个服务编写自定义集成代码，你只需将 Deep Agents 指向一个 MCP 服务器，它就会获取该服务器暴露的所有工具。

安装 langchain-mcp-adapters 以连接到 MCP 服务器：
    pip install "mcp>=1.24,<2" langchain-mcp-adapters
"""
# os.environ["LANGSMITH_TRACING"] = "true"
# os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
# os.environ["LANGSMITH_API_KEY"] = "your-langsmith_api_key"
# os.environ["LANGSMITH_PROJECT"] = "my-research-agent"

model = init_chat_model("deepseek-chat")
# 获取当前脚本所在目录
base_dir = os.path.dirname(os.path.abspath(__file__))
math_server_path = os.path.join(base_dir, "mcp_server", "math_server.py")
print(math_server_path)

async def main():
    client = MultiServerMCPClient(
        {
            "math": {
                "transport": "stdio",  # 本地访问
                "command": sys.executable,
                # "args": ["./mcp_server/math_server.py"],  # 填写绝对路径
                "args": [math_server_path],  # 填写绝对路径
            },
            "weather": {
                "transport": "http",  # 远程访问
                "url": "http://localhost:8001/mcp",  # mcp远程地址
            }
        }

    )
    tools = await client.get_tools()

    agent = create_deep_agent(
        model=model,
        tools=tools,
    )

    math_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "(3 + 5) * 12 等于多少？"}]}
    )
    weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "北京的天气怎么样?"}]}
    )
    print("数学题：", math_response["messages"][-1].content)
    print("天气：", weather_response["messages"][-1].content)


if __name__ == '__main__':
    asyncio.run(main())

