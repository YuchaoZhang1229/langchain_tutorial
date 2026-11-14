from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition


# ====== 公共部分：准备工具 ======
@tool
def get_weather(city: str) -> str:
    """获取城市天气"""
    weather_data = {
        "北京": "晴天 25度",
        "上海": "多云 28度",
        "杭州": "小雨 22度",
    }
    return weather_data.get(city, f"未找到{city}的天气信息")


# 组成工具数组
tools = [get_weather]

# ====== 公共部分：准备模型 ======
model = init_chat_model(
    'deepseek-v4-flash',
    extra_body={'thinking': {'type': 'disabled'}}
)


def run_create_agent():
    """
    方法一：使用 LangChain 的 create_agent 快速构建
    """
    print("\n--- 正在运行 create_agent ---")
    # create_agent 会自动创建一个包含 LLM 节点和 ToolNode 的图
    agent_graph = create_agent(model=model, tools=tools)

    result = agent_graph.invoke({
        "messages": [HumanMessage(content="北京和杭州今天天气怎么样？")]
    })

    for m in result['messages']:
        m.pretty_print()


def run_langgraph():
    """
    方法二：使用 LangGraph 手动构建图
    """
    print("\n--- 正在运行 LangGraph ---")
    # 绑定工具到模型
    model_with_tools = model.bind_tools(tools)

    # 定义 Node
    def llm_node(state: MessagesState):
        """LLM节点：调用模型，可以选择调用工具"""
        response = model_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    # 构建图
    builder = StateGraph(MessagesState)
    builder.add_node("llm", llm_node)
    builder.add_node("tools", ToolNode(tools))

    # 定义 Edge (流转逻辑)
    builder.add_edge(START, "llm")
    builder.add_conditional_edges("llm", tools_condition)
    builder.add_edge("tools", "llm")  # 工具执行后回到LLM，形成循环

    agent_graph = builder.compile()

    result = agent_graph.invoke({
        "messages": [HumanMessage(content="北京和杭州今天天气怎么样？")]
    })

    for m in result['messages']:
        m.pretty_print()


if __name__ == "__main__":
    run_create_agent()
    run_langgraph()