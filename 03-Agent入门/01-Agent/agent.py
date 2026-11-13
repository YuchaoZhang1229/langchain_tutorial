import os
import random
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
"""
1.create_agent---- 准备模型，工具

"""
# 指定模型：
model = ChatOpenAI(
            model="deepseek-v4-flash",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
	        openai_api_base="https://api.deepseek.com/v1",
            temperature=0,
)

# ---------- 1. 定义工具（具体的实现某个功能） ----------
def get_weather(city: str) -> str:
    """查询指定城市的当前天气情况。城市名称应为中文或英文，例如 '北京' 或 'Beijing'。"""
    weather_conditions = ["晴", "多云", "阴", "小雨", "中雨", "大雨", "雪", "雾"]
    temp = random.randint(10, 38)
    condition = random.choice(weather_conditions)
    return f"{city} 的天气：{condition}，温度 {temp}°C"

# ---------- 2. 创建 Agent ----------
# 使用模型标识字符串 "provider:model" 来指定模型[reference:5]
agent = create_agent(
    model=model, # 或其他模型，
    tools=[get_weather],
    system_prompt="你是一个乐于助人的助手，可以使用提供的工具来回答问题。"
)

# ---------- 3. 运行 Agent ----------
# Agent 的输入和输出都遵循特定的消息格式[reference:8]
# 测试1：计算
result1 = agent.invoke(
    {"messages": [{"role": "user", "content": "北京的天气怎么样"}]}
)
print("结果:", result1["messages"][-1].content)

print("\n" + "-" * 50 + "\n")
result1 = agent.invoke(
    {"messages": [{"role": "user", "content": "我刚刚问了什么"}]}
)
print("结果2:", result1["messages"][-1].content)

print("\n" + "-" * 50 + "\n")
