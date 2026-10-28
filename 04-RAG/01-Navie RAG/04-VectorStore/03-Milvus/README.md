## Milvus

### Milvus 概述

### Milvus 部署
Milvus 提供三种部署模式，覆盖广泛的数据规模——从 Jupyter Notebook 中的本地原型设计，到管理数百亿向量的大型 Kubernetes 集群：

- `Milvus Lite` 是一个 Python 库，可轻松集成到您的应用程序中。作为 Milvus 的轻量级版本，它非常适合在 Jupyter Notebook 中进行快速原型设计，或在资源有限的边缘设备上运行。
- `Milvus Standalone` 是一种单服务器部署方案，所有组件打包到单个 Docker 镜像中，便于部署。了解更多。
- `Milvus Distributed` 可部署在 Kubernetes 集群上，采用专为数十亿量级甚至更大规模场景设计的云原生架构。该架构确保了关键组件的冗余性。

#### Milvus Standalone 部署
使用 `docker compose` 命令即可一键部署：
```
# /deploy/docker-compose.yml
docker compose up -d
```

Milvus有一个web控制台叫attu，端口是3000，在浏览器输入地址：http://locahost:3000 即可访问：
![Milvus.png](../../../material/png/Milvus.png)

首次访问，需要注册一个管理员的用户名和密码，密码必须8位以上，且必须有大写、小写、数字、下划线中的3个类型。例如：admin/admin_123
![img.png](../../../material/png/Milvus2.png)