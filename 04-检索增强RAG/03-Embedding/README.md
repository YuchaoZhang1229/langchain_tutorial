## 文档向量化

### 一、为什么要文档向量化？
Embedding 模型将原始文本转换为一个固定长度的向量，使**语义相近的文本在向量空间中距离更近**

### 二、向量化方法
LangChain支持多种 Embedding 模型平台，你可以自由选择：

|模型| 提供方 |
|---|-----|
|OpenAIEmbeddings|OpenAI|
|DashScopeEmbeddings|阿里云百炼|
|HuggingFaceEmbeddings|本地开源模型|
|OllamaEmbeddings|本地开源模型|

更多LangChain支持的向量模型参考官方文档：https://docs.langchain.com/oss/python/integrations/embeddings


#### 1. 向量化模型的统一接口 `class Embeddings(ABC)`
为了便于开发，降低学习成本，LangChain提供了向量化模型的统一接口 `Embeddings`，并且提供了向量化的两个核心方法
- `embed_query`：str -> list[float], 一次处理一个字符串
- `embed_documents`：list[str] -> list[list[float]]， 一次处理多个字符串

#### 2. OllamaEmbeddings
```
uv add langchain-ollama
```

#### 3. DashScopeEmbeddings
```
uv add langchain-community dashscope
```


### 注意事项
- 生产中本地模型通常采用vLLM部署，不过由于vLLM只支持Linux系统，所以我们就不用了，本地暂时用Ollama代替
- langchain-community不再被langchain官方维护，也不再推荐使用，这里只做演示，不做推荐。