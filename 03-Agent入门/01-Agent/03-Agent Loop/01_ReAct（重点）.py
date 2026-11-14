from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model

# ---------- 1. 定义工具 ----------
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。"""
    weather_db = {"北京": "晴 5-15℃", "上海": "阴 8-18℃"}
    return weather_db.get(city, "未知城市")

@tool
def calculate(expression: str) -> str:
    """计算数学表达式，如 '2+3*4'。"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"{expression} = {result}"
    except:
        return "计算错误"

@tool
def search_wiki(query: str) -> str:
    """搜索维基百科获取信息。"""
    wiki_db = {"北京": "北京是中国的首都", "上海": "上海是中国的经济中心"}
    return wiki_db.get(query, "未找到相关信息")

# ---------- 2. Agent 运行函数 ----------
def run_langchain_react(user_input: str):
    model = init_chat_model(
        model="deepseek-v4-flash",
        extra_body={"thinking": {"type": "enabled"}}  # 是否开启思考模式 "enabled"、"disabled"
    )
    tools = [get_weather, calculate, search_wiki]

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="你是一个有用的AI助手，可以使用工具来帮助用户解决问题。"
    )

    print(f"用户输入：{user_input}")
    print("=" * 60)

    step_count = 0
    final_answer = None   # 用于存储最终答案
    # stream--- 可以把中间的调用过程和思考过程进行查看
    for event in agent.stream(
        {"messages": [{"role": "user", "content": user_input}]}
    ):
        # 如果你还想看原始事件结构，可以取消下面两行的注释
        print("\n 原始事件（raw event）:")
        print(event)

        # model节点产生的事件, 包含模型输出的消息
        if "model" in event:
            print("================== model节点产生的事件, 包含模型输出的消息 ==================")
            step_count += 1
            message = event["model"]["messages"][0]  # AIMessage 对象

            # message.content # 模型输出
            thought = message.content if message.content else "(模型未输出文本思考)"
            print(f"\n第 {step_count} 轮循环")
            print(f" 思考：{thought}")

            # message.tool_calls 工具调用
            # hasattr(message, "tool_calls"), 判断obj是否有tool_calls属性， 防止 message.tool_calls 报错
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("args", {})
                    print(f" 行动：调用 {tool_name}，参数 {tool_args}")
            else:
                # 没有 tool_calls，说明模型给出了最终答案
                final_answer = thought

        # tools节点产生的事件，包含工具执行结果
        elif "tools" in event:
            print("""================== tools节点产生的事件，包含工具执行结果 ==================""")
            # 处理工具执行结果（“观察”）
            for msg in event["tools"]["messages"]:
                if hasattr(msg, "content"):
                    print(f" 观察：{msg.content}")

    # 循环结束后打印最终结果
    print("\n" + "=" * 60)
    print(" 最终结果：")
    print(final_answer if final_answer else "（未获取到最终答案）")

# ---------- 3. 测试 ----------
if __name__ == "__main__":
    run_langchain_react("查一下上海的信息，北京天气怎么样，帮我计算一下2*3")