"""
主 Agent，也是整个Agent的核心协调者。它负责
- 与用户交互
- 收集婚礼信息，
- 调用各个Subagent
- 筹备婚礼计划。
"""
import asyncio

from langchain.agents import AgentState
from langgraph.types import Command
from langchain.tools import tool
from langchain.tools import ToolRuntime
from langchain.messages import HumanMessage, ToolMessage, AIMessage
from langchain.agents import create_agent
from playlist_agent import playlist_agent
from venue_agent import venue_agent
from travel_agent import get_travel_agent

"""
1. 定义 state，记录婚礼风格有关的信息，包括：婚礼人数、音乐风格、出发地、婚礼举办地
"""
class WeddingState(AgentState):
    origin: str         # 起点
    destination: str    # 目的地
    guest_count: str    # 宾客数量
    genre: str          # 婚礼风格


"""
1. 定义一个tool，用于更新state信息
首先，要执行婚礼规划任务必须知道婚礼信息，也就是state中要记录的数据。
AI通过与用户沟通可以获得这些信息，但是必须有一个tool负责更新state信息，当AI通过与用户聊天获取这些信息后，调用该tool更新到state中。
"""

@tool
def update_state(origin: str, destination: str, guest_count: str, genre: str, runtime: ToolRuntime) -> str:
    """当你询问用户，知道下列所有值时更新State：origin、destination、guest_count、genre"""
    return Command(update={
        "origin": origin,
        "destination": destination,
        "guest_count": guest_count,
        "genre": genre,
        "messages": [ToolMessage("Successfully updated state", tool_call_id=runtime.tool_call_id)]}
        )

"""
3. 定义3个Tool，分别对应3个Subagent
接下来，按照Subagent模式，主Agent需要把Subagents当做一个个Tool来协调使用。所以，我们接下来就先定义3个Tool，分别对应3个Subagent.
这些tool读取state中的婚礼信息，然后调用对应的subagent，分别完成自己的任务。
"""

@tool
async def search_flights(runtime: ToolRuntime) -> str:
    """旅行Agent搜索飞往理想婚礼地点的航班."""
    origin = runtime.state["origin"]
    destination = runtime.state["destination"]

    content = f"查询从{origin}到{destination}的航班"
    travel_agent = await get_travel_agent()
    response = await travel_agent.ainvoke({"messages": [HumanMessage(content)]})
    return response['messages'][-1].content

@tool
def search_venues(runtime: ToolRuntime) -> str:
    """场地Agent根据给定的地点和宾客数量寻找最佳的婚礼场地."""
    destination = runtime.state["destination"]
    capacity = runtime.state["guest_count"]

    content = f"在{destination}寻找适合{capacity}宾客的婚礼场地"
    response = venue_agent.invoke({"messages": [HumanMessage(content)]})
    return response['messages'][-1].content

@tool
def suggest_playlist(runtime: ToolRuntime) -> str:
    """播放列表Agent根据类型风格策划完美的播放列表."""
    genre = runtime.state["genre"]

    content = f"策划符合{genre}风格的婚礼播放列表的曲目"
    response = playlist_agent.invoke({"messages": [HumanMessage(content)]})
    return response['messages'][-1].content

"""
# 4. 创建主Agent
创建主Agent了，把刚刚的4个Tools都注册给它，并给它设定核心协调者的任务。
"""

coordinator = create_agent(
    model="deepseek-v4-flash",
    tools=[search_flights, search_venues, suggest_playlist, update_state],
    state_schema=WeddingState,
    system_prompt="""
    你是婚礼协调员。你负责与用户沟通，找到更新状态所需的所有信息，并更新到state。
    一旦完成，你就可以委派任务了。将查找航班、搜索场地和策划播放列表的任务委派给您的专家Agent。
    当你收到他们的答案，为我设计一场完美的婚礼方案。
    """
)

if __name__=="__main__":
    async def run_agent():
        print("🚀 Starting agent...")
        response = await coordinator.ainvoke({
            "messages": [HumanMessage("我来自北京，我想在昆山举办一场100人的婚礼，爵士风格的！")]
        })
        for message in response["messages"]:
            message.pretty_print()

    asyncio.run(run_agent())
