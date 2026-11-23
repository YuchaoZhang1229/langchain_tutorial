# 导入LangChain DeepAgent核心方法
import os
from deepagents import create_deep_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI


# ===================== 模拟私有数据库（演示，生产替换MySQL/PostgreSQL）=====================
class MockPrivateDB:
    def __init__(self):
        # 模拟销售业务表 sale_table
        self.sale_table = [
            {"dept": "销售一部", "month": "上个月", "sale_money": 1280},
            {"dept": "销售二部", "month": "上个月", "sale_money": 960},
            {"dept": "销售一部", "month": "本月", "sale_money": 500},
        ]

    def query(self, sql: str, dept_name: str):
        """模拟数据库查询接口"""
        total = 0
        for row in self.sale_table:
            if row["dept"] == dept_name and row["month"] == "上个月":
                total += row["sale_money"]
        return total

private_db = MockPrivateDB()


# ===================== 【自定义工具：查询部门上月销售总额】@tool装饰器 =====================
@tool(parse_docstring=True)
def get_last_month_sale(dept_name: str) -> str:
    """从私有业务数据库查询部门上月销售总额。

    Args:
        dept_name: 部门名称，例如"销售一部"

    Returns:
        该部门上月销售总额的文本描述
    """
    sql = "SELECT sum(sale_money) FROM sale_table WHERE month='上个月' and dept=%s"
    result = private_db.query(sql, dept_name)
    return f"{dept_name}上月销售总额：{result}万元"

model = ChatOpenAI(
    model="qwen3.7-flash",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
# ===================== 创建Deep Agent，注册自定义工具 create_deep_agent =====================
agent = create_deep_agent(
    # 模型，支持openai、anthropic、ollama本地私有化大模型，演示用ollama可本地跑
    model=model,
    # 挂载我们写好的自定义工具
    tools=[get_last_month_sale],
    system_prompt="你是企业业务数据分析助手，可以调用工具查询内部销售数据。"
)


# ===================== 调用Agent，自然语言提问 =====================
if __name__ == "__main__":
    # invoke 执行Agent
    res = agent.invoke({
        "messages": [
            {"role": "user", "content": "帮我查询销售一部上个月的销售总额"}
        ]
    })
    print("==== Agent返回完整消息 ====")
    print(res["messages"][-1].content)

    for message in res["messages"]:
        message.pretty_print()
