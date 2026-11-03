
安装 MinerU
```
uv add mineru[core]==2.7.5
```

设置系统环境变量
```
# 方法一：更换 Hugging Face 镜像和缓存路径
HF_ENDPOINT = https://hf-mirror.com                        # Hugging Face 镜像
HF_HOME = E:\Development_Tool\huggingface_cache            # Hugging Face 缓存路径
# 方法二：用 ModelScope 【推荐】
MINERU_MODEL_SOURCE = modelscope                           # MinerU 改用 ModelScope 源
MODELSCOPE_CACHE = E:\Development_Tool\modelscope_cache    # ModelScope 缓存路径
```
或者在代码中添加
```
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"                        # Hugging Face 镜像
os.environ["HF_HOME"] = r"E:\Development_Tool\huggingface_cache"           # Hugging Face 缓存路径
os.environ["MINERU_MODEL_SOURCE"] = "modelscope"                           # MinerU 改用 ModelScope 源
os.environ["MODELSCOPE_CACHE"] = r"E:\Development_Tool\modelscope_cache"   # ModelScope 缓存路径
```


这个项目的意义
1. 针对不同 PDF 文档或不同的数据类型我们使用什么方式去解析
2. 解析之后我们怎么样去对这些文档进行分块处理

当别人来问你，你可以说，我们公司有很多pdf，pdf中也有很多标题、标题、表格，然后你用什么方式把这些内容解析出来，然后进行比较好的分块呢

