
import os
from pathlib import Path
from langchain_openai import ChatOpenAI


"""
    权限控制案例共用的模型和运行辅助函数。
"""

ROOT = Path(__file__).resolve().parent

def workspace_path(name):
    """创建并返回案例独立使用的工作目录。"""
    path = ROOT / "运行数据" / name
    path.mkdir(parents=True, exist_ok=True)
    return path

def build_model():
    """创建 qwen 的 OpenAI 兼容客户端。"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置环境变量 DASHSCOPE_API_KEY")

    return ChatOpenAI(
        model="qwen3.7-flash",
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=60,
        max_retries=1,
    )

def build_model_deepseek():
    """创建 DeepSeek 的 OpenAI 兼容客户端。"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置环境变量 DEEPSEEK_API_KEY")

    return ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        timeout=120,  # 推理模型建议较长超时
        max_retries=1,
    )

def invoke_agent(agent, query, config=None):
    """用统一消息格式调用 Agent。"""
    invoke_kwargs = {}
    if config is not None:
        invoke_kwargs["config"] = config
    return agent.invoke(
        {"messages": [{"role": "user", "content": query}]},
        **invoke_kwargs,
    )


def final_answer(result):
    """提取 Agent 最后一条消息的文本。"""
    return str(result["messages"][-1].content)
