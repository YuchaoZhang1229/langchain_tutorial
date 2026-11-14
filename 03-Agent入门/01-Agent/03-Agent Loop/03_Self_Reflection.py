"""
Self-Reflection: 深度思考 -> 生成初稿 -> 反思 -> 修正

- 这个机制会额外调用token，简单的闲聊的场景 无需开启；
- 高准确率需求 -- 设置1-3轮的自省
"""


from typing import Optional
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# ======================
# 1. 定义结构化输出模型
# ======================
class ThinkingProcess(BaseModel):
    """深度思考的结构化输出"""
    goal: str = Field(description="任务的核心目标")
    steps: list[str] = Field(description="执行步骤列表")
    risks: list[str] = Field(description="可能出现的错误或风险")
    final_output_format: str = Field(description="最终输出应该是什么格式")

class ReflectionResult(BaseModel):
    """自我反思的结构化输出"""
    is_correct: bool = Field(description="当前回答是否正确")
    issues: list[str] = Field(description="存在的问题或遗漏")
    suggestions: str = Field(description="具体的修正建议")

# ======================
# 2. 封装自省 Agent
# ======================
class ThinkingReflectionAgent:
    def __init__(self, model: Optional[ChatOpenAI] = None):
        self.model = model or init_chat_model(
            model="deepseek-v4-flash",
            extra_body={"thinking": {"type": "disabled"}},
        )

        # 思考链：强制结构化输出
        self.thinking_chain = ChatPromptTemplate.from_messages([
            ("system", "你是一个深度思考专家。请分析任务并输出思考过程。"),
            ("human", "任务：{task}"),
        ]) | self.model.with_structured_output(ThinkingProcess)

        # 生成初稿链
        self.draft_chain = ChatPromptTemplate.from_messages([
            ("system", "你是一个助手。请根据思考结果完成任务。"),
            ("human", "任务：{task}\n\n思考结果：{thinking}"),
        ]) | self.model

        # 反思链：强制结构化输出
        self.reflection_chain = ChatPromptTemplate.from_messages([
            ("system", "你是一个严格的评审。请检查回答的质量。"),
            ("human", "任务：{task}\n当前回答：{answer}"),
        ]) | self.model.with_structured_output(ReflectionResult)

        # 修正链
        self.refine_chain = ChatPromptTemplate.from_messages([
            ("system", "请根据评审意见优化回答，直接输出最终结果。"),
            ("human", "任务：{task}\n原回答：{answer}\n评审建议：{feedback}"),
        ]) | self.model

    def run(self, task: str, max_rounds: int = 1) -> str:
        print("=" * 60)
        print(f"🚀 开始处理任务：{task}")
        print("=" * 60)

        # 1. Thinking：深度思考
        print("\n🧠 [Thinking] 深度思考中...")
        thinking = self.thinking_chain.invoke({"task": task})
        print(f"   目标：{thinking.goal}")
        print(f"   步骤：{thinking.steps}")

        # 2. Draft：生成初稿
        print("\n📝 [Draft] 生成初步答案...")
        # 将 Pydantic 对象转为字典或字符串传入 Prompt
        draft_response = self.draft_chain.invoke({
            "task": task,
            "thinking": thinking.model_dump()
        })
        current_answer = draft_response.content
        print(current_answer)

        # 3. Reflection Loop：反思与修正循环
        for i in range(max_rounds):
            print(f"\n🔍 [Reflection {i + 1}] 自我反思中...")
            reflection = self.reflection_chain.invoke({
                "task": task,
                "answer": current_answer
            })

            print(f"   是否正确：{reflection.is_correct}")
            if reflection.issues:
                print(f"   发现问题：{reflection.issues}")

            # 如果没问题，提前结束
            if reflection.is_correct and not reflection.issues:
                print("✅ 质量达标，无需修正。")
                break

            # 修正
            print("\n🔧 [Refine] 正在修正...")
            refined_response = self.refine_chain.invoke({
                "task": task,
                "answer": current_answer,
                "feedback": reflection.suggestions
            })
            current_answer = refined_response.content
            print(current_answer)

        print("\n" + "=" * 60)
        print("🎉 最终结果输出")
        print("=" * 60)
        return current_answer


# ======================
# 3. 运行测试
# ======================
if __name__ == "__main__":
    agent = ThinkingReflectionAgent()
    # 你可以换成任何任务：数学题、文案、代码、方案、推理题
    # task = "15乘8加20等于多少？请写出计算过程"
    task = "写一段50字以内的人工智能介绍"
    # task = "检查这段代码有没有错误：print(15*8+20)"
    final_result = agent.run(task, max_rounds=3)

    print("\n最终输出：\n", final_result)