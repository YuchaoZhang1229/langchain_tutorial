## LangGraph

### 1. AI 应用的发展过程

<img alt="img_4.png" height="" src="image/AI 应用的发展过程.png" width="600"/>



但是，Agent的自主控制能力与稳定程度之间是对立的两端，通常来说，LLM自主控制的越多，应用的稳定程度就会越小：

>LangGraph的作用就是在**保持Agent的自主控制程度不变的同时，提高Agent的稳定程度**

<img alt="img.png" src="image/LangGraph的作用.png" width="600"/>


### 2. 认识 LangGraph
简单来说，LangGraph允许你自己定义Agent的**工作流（WorkFlow）**中的每一个**节点（Node）**：
- 需要稳定性的节点，就用传统编程控制
- 需要LLM自主控制的，就交给LLM

并且，整个工作流不再是一条直线运行的**链（Chain）**，而是一个像真正工作流那样有分支、有循环的**图（Graph）**。

在LangGraph中，工作流由3个基本的要素组成：
- **节点（Node）**：即工作流中的关键工作代码，可以是工具调用、知识检索、LLM调用
- **边（Edge）**：也可以理解为线，就是把各个节点连接起来的路径，是控制工作流走向的关键
- **状态（State）**：整个工作流中流转的数据

<img alt="img.png" src="image/LangGraph三要素.png" width="600"/>

为了提高应用的运行的稳定程度，LangGraph为节点运行提供了Checkpointer功能，应用运行到每个节点（Node）都会形成**检查点（Checkpoint）**，我们可以方便的跳转到任意checkpoint，这样一来应用就具备了三大功能：
- **故障恢复**：即便是程序异常中止，也可以随时恢复到失败节点继续执行。
- **人机交互**：在程序运行中可以暂停工作流，在关键节点允许人工介入，得到人工确认后恢复执行，进一步提高程序的可靠性。
- **持久记忆**：由于Checkpointer可以持久化存储，能方便的拿到历史信息，因此应用还具备了记忆功能。

如果是**模型（Model）**是一匹能力卓越但跳脱的野马，那LangGraph就为你提供了一套控马的**鞍具（Harness）**，让模型在发挥自身智能的同时，还能被有效地控制。

正如LangChain官网所说，Agent = Model + Harness，有了LangGraph这套鞍具（Harness），才能让模型跑的又快又稳。


### 3. LangChain与LangGraph
LangChain 1.x之后的版本中，Agent的底层实现已经全部替换为基于LangGraph了！
- Memory
- HITL
- ...

两者的定位完全不同：
- **LangChain**：便捷开发AI应用的框架，提供了开发AI应用的各种统一API
  - 统一的LLM调用
  - 统一的Embedding Model调用
  - 统一的Vector Store调用
  - ...
- **LangGraph**: 工作流编排框架，提供了完善的工作流编排工具
  - 基于Node和Edge的工作流编排
  - 基于State的工作流数据传输
  - 基于Checkpointer的数据持久化

总结一下：
- **LangGraph**关注的是工作流的编排，你的工作流甚至可以完全与LLM无关，与Agent无关。如果你利用LangGraph开发Agent，可以自由的控制Agent工作流中的每一个细节
  - 优点：自由度更高。
  - 缺点：比较繁琐
  - 场景：需要完全控制Agent工作流程和细节，或者复杂Agent工作流的情况
- **LangChain**则是提供的统一API，底层基于LangGraph实现Agent，简化了Agent的开发。
  - 优点：简化Agent开发
  - 确定：灵活度不如LangGraph
  - 场景：简单的LLM调用，或者快捷的Agent开发