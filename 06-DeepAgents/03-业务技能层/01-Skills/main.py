"""
langchain和skills整合实战  --DeepAgent模块
create_agent()  ---create_deep_agent
1.DeepAgent模块--create_deep_agent--- skills
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends import FilesystemBackend

# 加载环境变量
load_dotenv()
BASE = Path(__file__).parent
print(f"项目根目录: {BASE}")

# ==========改用importlib动态导入，不再依赖sys.path==========
import importlib.util

scripts_path = BASE / "skill_packages" / "contract-review" / "scripts"
file_path = scripts_path / "contract_check.py"
print(f"contract_check 文件完整路径: {file_path}")
# 动态加载一个外部 .py 文件当模块用
spec = importlib.util.spec_from_file_location("contract_check", file_path) # 找到contract_check.py，并且给他一个描述（contract_check）
contract_check_module = importlib.util.module_from_spec(spec) # 装执行的结果 module_from_spec
spec.loader.exec_module(contract_check_module) # exec_module  执行里面的结果
contract_check = contract_check_module.contract_check # 获取里面的内容--合同的基本信息，风险
print("contract_check 导入成功！")
# =========================================================

def build_llm():
    """构建大模型实例，temperature=0 强约束指令"""
    return ChatOpenAI(
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        temperature=0.0
    )


async def run_agent():
    llm = build_llm()

    # 虚拟文件系统，根目录锁定到当前contract_review_skill文件夹
    backend = FilesystemBackend(root_dir=str(BASE), virtual_mode=True)

    # 权限配置：允许读取skill包全部内容、合同文件；禁止写
    permissions = [
        FilesystemPermission(operations=["read"], paths=["/skill_packages/**"], mode="allow"),
        FilesystemPermission(operations=["read"], paths=["/skill_packages/contract-review/references/**"], mode="allow"),
        FilesystemPermission(operations=["read"], paths=["/skill_packages/contract-review/assets/**"], mode="allow"),
        FilesystemPermission(operations=["read"], paths=["/skill_packages/contract-review/scripts/**"], mode="allow"),
        FilesystemPermission(operations=["read", "write"], paths=["/**"], mode="deny")
    ]

    agent = create_deep_agent(
        model=llm,
        skills=["/skill_packages/"],   # 扫描该目录下子文件夹作为Skill包
        tools=[contract_check],        # Python自定义工具手动注册
        backend=backend,   #
        permissions=permissions
    )

    print("\n==== Agent启动完成（标准Skill包加载模式）====")
    user_input = input(">>> 请输入指令：")

    # 调用Agent
    response = await agent.ainvoke({"messages": [{"role": "user", "content": user_input}]})
    last_msg = response["messages"][-1]
    content = getattr(last_msg, "content", str(last_msg))
    print("\n==== Agent输出 ====")
    print(content)


async def interactive_loop():
    """交互式循环，可以多次提问"""
    while True:
        try:
            await run_agent()
        except Exception as err:
            print(f"\n[异常捕获] {err}")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(interactive_loop())


""" 
>>请输入指令：帮我核验 /skill_packages/contract-review/references/contract_sample.txt
【开始合同初审，请等待关键信息提取】
### 合同基础信息
甲方：XX科技有限公司
乙方：XX供应链公司
合同金额：200万元
有效期：2026-01-01 ~ 2026-12-31
请回复【继续查看风险】，查看合同风险项

>>>请输入指令：继续查看风险
### 合同初审风险提示
1. 付款周期条款模糊，缺少具体时间节点
2. 缺少明确违约追责细则
结论：本合同存在2项待确认风险，建议法务人工复核。


"""