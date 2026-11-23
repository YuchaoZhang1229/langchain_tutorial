import os
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI


"""
演示 DeepAgents 根据自然语言调用全部内置 harness 工具。

涉及的工具：
    ls、read_file、write_file、edit_file、delete、glob、grep、execute、task

LocalShellBackend 会把文件操作限制在专用演示目录，但 execute 工具是在本机
直接执行命令，不是真正的隔离沙盒。本示例只让 execute 执行无副作用的 pwd。

    工具                  描述
    ls	            列出目录中的文件。
    read_file	    读取文件内容（支持分页和多模式）。
    write_file	    创建一个新文件，或覆盖一个现有文件。
    edit_file	    在文件中执行精确的字符串替换。
    delete	        删除一个文件，或一个目录及其内容递归地。【delete工具需要 deepagents>=0.7】
    glob	        查找匹配 glob 模式的文件。
    grep	        搜索文件内容。
    execute	        运行 shell 命令（仅限沙盒后端）。
    task	        启动一个子代理来处理一个委托的任务。
"""


# ======================== 配置区域 ========================

# 工作区根目录：所有文件操作都被限制在此目录下（安全沙盒）
ROOT_DIR = Path(__file__).with_name("harness_workspace")
print(ROOT_DIR)
# 系统提示词：指导 Agent 的行为模式
SYSTEM_PROMPT = """你是一个文件整理助手。
你需要根据用户的自然语言需求自主选择 DeepAgents 内置工具完成工作，而不是只描述操作步骤。
所有文件操作只能在当前演示工作区内进行。
execute 只能执行用户明确指定的无副作用命令，不得访问工作区外的文件。
**重要：无论任务多简单，完成后你都必须用一句完整的中文自然语言总结你的操作结果，禁止留空回复。**
"""

# 预定义的测试查询，每种工具对应一个自然语言任务
EXAMPLE_QUERIES = {
    "ls": "请查看当前工作区中有哪些文件。",
    "read_file": "请读取 /sample_notes.txt 的内容。",
    "write_file": "请创建 /created_by_agent.txt，内容为：由 write_file 工具创建。",
    "edit_file": "请把 /editable.txt 中的 status: draft 精确修改为 status: complete。",
    "delete": "请删除 /delete_me.txt。",
    "glob": "请查找当前工作区中所有扩展名为 .txt 的文件。",
    "grep": "请搜索当前工作区中哪些 .txt 文件包含 MCP。",
    "execute": "请通过 shell 执行 pwd，告诉我当前工作目录。不要执行其他命令。",
    "task": "请启动一个子代理，让它用一句话解释什么是 DeepAgents。",
}


# ======================== 核心函数 ========================

def build_agent():
    """
    创建 Deep Agent，注入所有内置 harness 工具。

    关键点：
    - 使用 ChatOpenAI 连接通义千问模型（通过 DashScope 兼容接口）。
    - backend=LocalShellBackend 提供了文件系统操作能力（ls, read, write, ...），
      并且将操作限制在 root_dir 目录内，起到安全隔离作用。
    - 传入 system_prompt 让 Agent 知道自己的角色和约束。
    """
    model = ChatOpenAI(
        model="qwen3.7-flash",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 安全沙盒机制：所有文件读写删除操作都被限制在 ROOT_DIR 目录下，
    # 防止 Agent 误操作到系统其他位置。
    backend = LocalShellBackend(
        root_dir=ROOT_DIR,
        virtual_mode=True,          # 开启虚拟模式，支持相对路径处理
        inherit_env=False,          # 不继承系统环境变量（增强安全性）
    )

    # create_deep_agent 会自动识别 backend，并注入全部内置工具
    return create_deep_agent(
        model=model,
        backend=backend,
        system_prompt=SYSTEM_PROMPT,
    )


def prepare_workspace():
    """
    准备测试用的文件。
    在 ROOT_DIR 下创建三个样例文件，供后续工具演示使用。
    """
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = {
        "sample_notes.txt": "DeepAgents 内置工具演示\nkeyword: MCP\n",
        "editable.txt": "project: harness\nstatus: draft\n",
        "delete_me.txt": "这个文件用于演示 delete 工具。\n",
    }
    for file_name, content in fixtures.items():
        # write_text写入文件
        (ROOT_DIR / file_name).write_text(content, encoding="utf-8") # Path.write_text


def _shorten(value: Any, limit: int = 300):
    """
    辅助函数：将任意值转为字符串并截断，防止打印过长内容。
    用于工具调用轨迹的日志输出。
    """
    text = str(value).replace("\n", " ")
    return text if len(text) <= limit else f"{text[:limit]}..."


def print_tool_trace(messages: list[Any]):
    """
    打印工具调用轨迹，方便调试和观察 Agent 的行为。

    遍历消息列表：
    - 如果是 AIMessage，提取其中的 tool_calls（模型发起的工具调用请求）。
    - 如果是 ToolMessage，提取工具执行后的返回结果。
    """
    print("\n===== 工具调用轨迹 =====")
    for message in messages:
        if isinstance(message, AIMessage):
            for tool_call in message.tool_calls:
                print(f"调用 {tool_call['name']}: {_shorten(tool_call['args'])}")
        elif isinstance(message, ToolMessage):
            print(f"结果 {message.name}: {_shorten(message.content)}")


def main():
    """
    主流程：
    1. 检查 API Key 是否存在。
    2. 准备测试文件。
    3. 构建 Agent。
    4. 设定用户查询（此处直接写死为 '请查看当前工作区中有哪些文件。'）。
    5. 执行 agent.invoke，得到包含完整消息历史的 result。
    6. 打印用户查询、工具调用轨迹、最终回答。
    """
    if not os.getenv("DASHSCOPE_API_KEY"):
        raise RuntimeError("请先设置环境变量 DASHSCOPE_API_KEY")

    prepare_workspace()
    agent = build_agent()

    # 当前演示固定为 "ls" 任务，也可以从 EXAMPLE_QUERIES 中选取
    # query = EXAMPLE_QUERIES["ls"]
    # query = '请查看当前工作区中有哪些文件。然后删除editable.txt'
    query = '请查看当前工作区中有哪些文件。然后删除editable.txt，并告诉我当前工作目录'

    # invoke 是同步调用，返回包含所有消息的字典
    result = agent.invoke(
        {"messages": [{"role": "user", "content": query}]},
    )

    print(f"\n===== 用户 Query =====\n{query}")

    # 打印工具调用中间过程
    print_tool_trace(result["messages"])

    # 注意：直接取最后一条消息可能为空（当模型仅调用工具而不生成文字时），
    # 更稳健的做法是找到最后一条有内容的 AIMessage，但此处为了简洁保持原样。
    print("\n===== 最终回答 =====")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()

"""
1. 关于 [stderr] 'pwd' 不是内部或外部命令... Exit code: 1
stderr（标准错误）：这是程序运行过程中专门用来输出错误信息的通道。当命令执行失败时，系统会把报错提示塞进这个通道。

Exit code: 1（退出码 1）：任何一个程序/命令执行完后，都会给操作系统返回一个数字。0 代表“任务圆满完成，一切正常”，任何非 0 的数字（比如 1）都代表“执行过程中出了某种差错”。

为什么这里会报错？
因为 pwd 是 Linux/Mac 系统（Unix-like）用来显示当前路径的命令。而你的电脑是 Windows 系统，Windows 的 CMD 命令行里根本没有 pwd 这个程序，所以系统找不到它，于是返回了退出码 1，并通过 stderr 告诉你“’pwd‘ 不是内部或外部命令”。

2. 关于 [Command succeeded with exit code 0]
succeeded 和 Exit code 0：这代表 “命令顺利执行，没有发生任何错误”。

为什么这次成功了？
聪明的 Agent 在第一次执行 pwd 失败后，没有放弃。它识别出当前是 Windows 环境，立刻换用了 Windows 系统自带的命令 echo %cd%（这也是用来显示当前目录的）。这次命令执行非常顺利，操作系统找到了它，于是返回了退出码 0，并通过 stdout（标准输出）返回了你的实际路径。

3. 这段日志还揭示了一个更深层的亮点（AI 的智能适应）
整个执行过程：

Agent 先查了文件（ls 成功）。

Agent 第一次尝试查路径（pwd）—— 失败（退出码 1）。

Agent 继续执行删除（delete 成功）。

Agent 没有停，也没有报错给用户，而是主动换了个命令（echo %cd%）—— 成功（退出码 0）。

这完美地体现了 DeepAgents 的自主决策能力：它在面对跨平台兼容性问题时，通过“试错——分析报错——更换方案”的闭环，最终圆满完成了你“告诉我当前工作目录”的任务。

"""