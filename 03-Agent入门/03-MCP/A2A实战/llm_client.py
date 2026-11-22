"""
共享 LLM 客户端 — 通过 DeepSeek API（兼容 OpenAI SDK）调用大模型

环境变量 DEEPSEEK_API_KEY 需要在系统中配置。

--------------------------------------------------------------------------------
【与官方 SDK 版 llm_client.py 的唯一区别：同步 vs 异步】

原版用的是 AsyncOpenAI + async def chat()，因为官方 a2a SDK 跑在
Starlette/uvicorn 上（ASGI，全异步），异步客户端能自然融入它的执行链。

本版改用同步 OpenAI + def chat()，因为 python-a2a 的 A2AServer 跑在
Flask 上（WSGI，线程模型）：它调用 message_handler 是**同步**调用，
没有运行中的事件循环。在同步 handler 里硬用异步客户端要么报错、
要么得 asyncio.run() 包一层，反而绕。

结论：换 SDK 不只是换 API 名字，整个并发模型也从「异步」变成了「线程」。
--------------------------------------------------------------------------------
"""

import os
from openai import OpenAI

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-flash"  # DeepSeek 通用对话模型


def get_client() -> OpenAI:
    """获取 DeepSeek 同步客户端"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 环境变量未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL, timeout=60)


def chat(system_prompt: str, user_message: str, model: str = DEEPSEEK_MODEL) -> str:
    """发送一次对话请求，返回模型回复文本"""
    client = get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""
