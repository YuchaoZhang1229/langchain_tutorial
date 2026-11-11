"""
婚礼歌单的agent，为了方便查询，我提供好了一些模拟数据，保存在Sqlite中
"""
from langchain_community.utilities import SQLDatabase
from langchain.agents import create_agent
from langchain_core.tools import tool

db = SQLDatabase.from_uri("sqlite:///Chinook.db")

@tool
def query_playlist_db(query: str) -> str:
    """Query the database for playlist information"""
    try:
        return db.run(query)
    except Exception as e:
        return f"Error querying database: {e}"

# Playlist agent
playlist_agent = create_agent(
    model="deepseek-v4-flash",
    tools=[query_playlist_db],
    system_prompt="""
    你是播放列表专家。查询sql数据库并为给定类型的婚礼策划完美的播放列表。
    一旦你有了你的播放列表，计算播放列表的总时长和成本，每首歌都有一个相关的价格。
    如果在查询数据库时遇到错误，请尝试通过更改查询来修复它们。
    不要空手而归，继续尝试查询数据库，直到你找到一个歌曲列表。
    您可能需要进行多个查询以迭代地找到最佳选项。
    """
)

if __name__ == "__main__":
    # 测试，查询歌单数据
    res = query_playlist_db.invoke({"query": "SELECT * FROM Playlist"})
    print(res)