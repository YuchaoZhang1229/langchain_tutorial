"""
婚礼场地的agent，这里我们简化实现方案，直接基于tavily搜索场地。
"""
import os
print(os.getenv("TAVILY_API_KEY"))
# if os.getenv("TAVILY_API_KEY") is None:
#     os.environ["TAVILY_API_KEY"] = "YOUR_API_KEY"
from langchain.agents import create_agent
from langchain_tavily import TavilySearch

# 定义Tavily web_search工具
web_search = TavilySearch(
    api_key=os.getenv("TAVILY_API_KEY"),
    max_results=5,
    topic="general",
)

# 创建 Venue agent
venue_agent = create_agent(
    model="deepseek-flash",
    tools=[web_search],
    system_prompt="""
    你是场地专家，你在指定的位置搜索满足要求的场地。
    你不能再追问任何后续问题，你必须根据以下标准找到最佳的场地选择：
    - 价格（最低）
    - 容量（完全匹配）
    - 评价（最高）
    您可能需要进行多次搜索以迭代地找到最佳选项。
    """
)
