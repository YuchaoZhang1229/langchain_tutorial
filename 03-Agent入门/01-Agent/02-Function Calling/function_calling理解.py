import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

# ⭐ 步骤1：定义工具说明（告诉模型「你有哪些手」）
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "查询指定城市的天气情况",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市"}
            },
            "required": ["city"]
        }
    }
}]

def get_weather(city):  # 真正干活的函数，运行在本地，不在模型里
    return {"city": city, "weather": "晴天"}

messages = [{"role": "user", "content": "查一下今天昆山的天气情况"}]
print("="*20, f"第一次发送给模型的messages:\n {messages}")
# ⭐ 步骤2：把问题 + 工具说明一起发给模型
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools
)
msg = resp.choices[0].message
messages.append(msg)  # 必须把 assistant 的 tool_calls 消息存回上下文
print("="*20, f"第一次模型的完整响应:{msg}")

# ⭐ 步骤3：本地执行函数，并把结果回传给模型
if msg.tool_calls:
    for call in msg.tool_calls:
        # print(f"工具调用: {call}")
        print("="*20, f"工具的名称: {call.function.name}, 工具的参数: {call.function.arguments}")

        args = json.loads(call.function.arguments)  # 参数是 JSON 字符串，要解析
        result = get_weather(**args)
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,  # 必须和模型给的 id 对上
            "content": json.dumps(result, ensure_ascii=False)
        })

# ⭐ 步骤4：再请求一次，让模型基于结果生成自然语言答案
print("="*20, f"第二次发送给模型的messages:{messages}")
final = client.chat.completions.create(model="deepseek-chat", messages=messages)
print("="*20, f"第二次模型的完整响应:{final}")
print("模型的最终答案是：")
print(final.choices[0].message.content)
