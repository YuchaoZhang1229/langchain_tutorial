import asyncio
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

# 连接自定义MCP服务
client = MultiServerMCPClient(
    {
        "math": {
            "transport": "stdio",
            "command": "python",
            "args": ["03-math_mcp_server.py"] # 这里是脚本所在的路径，此处是相对路径
        }
    }
)

model = init_chat_model(
    model = "deepseek-v4-flash",
    extra_body={"thinking": {"type": "disabled"}}
)

async def main():
    tools = await client.get_tools()
    print("获取到的工具：")
    for tool in tools:
        print(f"tool.name: {tool.name}")
        print(f"tool.description: {tool.description}")
        print(f"tool.args_schema: {tool.args_schema}")
        print(f"tool.args: {tool.args}")
        print("-------------------")
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="You are a helpful agent. You must use tools to answer math question."
    )
    response = await agent.ainvoke({
        "messages": [HumanMessage("467和529的平方根之和是多少?")]
    })
    for message in response["messages"]:
        message.pretty_print()

if __name__ == "__main__":
    # 在顶层通过 asyncio.run() 启动异步函数
    asyncio.run(main())
