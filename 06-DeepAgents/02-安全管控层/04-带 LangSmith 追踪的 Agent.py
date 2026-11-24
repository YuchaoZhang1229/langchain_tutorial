"""
agent.py — 带 LangSmith 追踪的智能助手（DeepSeek 版）
"""
import os
from dotenv import load_dotenv

# 必须在导入 LangChain 之前加载环境变量
load_dotenv()
import os
# 让代码直接找到我们的配置
# os.environ["LANGSMITH_TRACING"] = "true"
# os.environ["LANGSMITH_API_KEY"] = "your_api_key"
# os.environ["LANGSMITH_ENDPOINT"] = "https://apac.api.smith.langchain.com"
# os.environ["LANGSMITH_PROJECT"] = "特殊"
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI   # 用 OpenAI 兼容协议接入 DeepSeek


# ============================================================
# 1. 定义自定义工具
# ============================================================

@tool
def calculate(expression: str) -> str:
    """计算数学表达式，例如 '2 + 3 * 4'"""
    try:
        result = eval(expression)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"


@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气信息（模拟数据）"""
    weather_data = {
        "北京": "晴，15°C，北风3级",
        "上海": "多云，20°C，东风2级",
        "深圳": "小雨，26°C，南风1级",
    }
    return weather_data.get(city, f"暂未收录 {city} 的天气数据")


# ============================================================
# 2. 先构造模型实例，再传给 create_agent
# ============================================================


model = ChatOpenAI(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.0,
)

agent = create_agent(
    model=model,
    tools=[calculate, get_weather],
    system_prompt=(
        "你是一个智能助手。用户问你数学问题时，使用 calculate 工具；"
        "问天气时，使用 get_weather 工具。回答简洁明了。"
    ),
)


# ============================================================
# 3. 运行 Agent
# ============================================================

def main():
    print("=" * 60)
    print("  智能研究助手（LangSmith 追踪已启用）")
    print("=" * 60)

    test_queries = [
        "帮我计算一下 128 * 3 + 56 等于多少",
        "北京今天天气怎么样？",
        "上海和深圳的天气分别是什么？",
    ]

    for query in test_queries:
        print(f"\n用户：{query}")
        response = agent.invoke(
            {"messages": [{"role": "user", "content": query}]}
        )
        # 提取最后一条 AI 消息
        last_message = response["messages"][-1]
        print(f"助手：{last_message.content}")

    print("\n" + "=" * 60)
    print("  所有运行已记录到 LangSmith")
    print("  请访问 https://smith.langchain.com 查看追踪详情")
    print("=" * 60)


if __name__ == "__main__":
    main()