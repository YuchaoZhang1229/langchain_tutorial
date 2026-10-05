from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import  JsonOutputParser

# 调试模式
from langchain_core.globals import set_debug
set_debug(True)

model = init_chat_model(model="deepseek-flash")
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是翻译助手, 返回JSON格式，包含原文和译文"),
    ("human", "请把一下内容翻译成{language}：{text}")
])
output_parser = JsonOutputParser()
chain = prompt | model | output_parser

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
app = FastAPI(title="基于LangChain的服务",version="V1.5",description="翻译服务")

# 允许跨域请求（解决 Apifox/浏览器调用时的 CORS 拦截问题）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 允许所有来源（学习阶段先放开，生产环境建议指定域名）
    allow_credentials=True,
    allow_methods=["*"],      # 允许所有 HTTP 方法
    allow_headers=["*"],      # 允许所有请求头
)

# 函数和访问路径一一对应
add_routes(app, chain, path="/langchainServer")

# 本地调用
# res = chain.invoke({"language":"英语","text": "你好"})
# print(res)

if __name__ == "__main__":
    import uvicorn # 服务器
    uvicorn.run(app, host="localhost", port=8000)

# 使用 LangChain 编写客户端访问我们基于 LangServer 的 WEB 服务
'''
    from langserve import RemoteRunnable

    if __name__ == "__main__":
        client = RemoteRunnable("http://localhost:8000/lanchainServer")
        print(client.invoke({'language': '意大利文', 'text': '我喜欢编程'}))
'''
# 对于其他编程语言来说，可以使用 RESTful API 来调用我们的服务
'''
    比如在postman或者apifox中访问http://localhost:8000/langchainServer/invoke
    在body中选择json，然后输入
    {
        "input":
        {
            "language":"意大利文",
            "text":"为了部落！"
        }
    }
'''