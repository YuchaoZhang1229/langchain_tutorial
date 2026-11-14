"""
plan and execute 需求：贷款申请自动审批
- plan: 贷款表单数据校验 → 计算贷款最大额度 → 提交贷款申请三步
- execute: 调用工具执行计划
- summary: 汇总执行结果，给出最终答案
"""
import json
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool


# ----------------------------
# 1. 定义贷款审批工具
# ----------------------------
@tool
def validate_form(age: int, monthly_income: float, loan_amount: float) -> str:
    """验证贷款申请表单，返回 VALID 或错误信息。"""
    if age < 18:
        return "INVALID: 年龄必须≥18"
    if monthly_income <= 0:
        return "INVALID: 月收入必须>0"
    if loan_amount <= 0:
        return "INVALID: 贷款金额必须>0"
    if loan_amount > monthly_income * 36:
        return "INVALID: 贷款金额不能超过月收入的36倍"
    return "VALID"


@tool
def calculate_max_loan(age: int, monthly_income: float) -> str:
    """计算最大可贷额度，返回数字字符串。"""
    return str(monthly_income * 12 * 0.5)


@tool
def submit_form(age: int, monthly_income: float, loan_amount: float, max_loan: str) -> str:
    """提交最终贷款申请。"""
    return (
        f"申请已提交！年龄 {age}，月收入 {monthly_income}，"
        f"申请额度 {loan_amount}，批准额度 {float(max_loan):.2f}"
    )


TOOLS = [validate_form, calculate_max_loan, submit_form]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}


# ----------------------------
# 2. 数据模型
# ----------------------------
class Step(BaseModel):
    id: int = Field(..., description="步骤ID")
    description: str = Field(..., description="步骤描述")
    tool: str = Field(..., description="需要调用的工具名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具输入参数")


class Plan(BaseModel):
    steps: List[Step] = Field(default_factory=list, description="执行计划")


# ----------------------------
# 3. 占位符替换：把计划里写的 "{{step_2_result}}" 替换成第 2 步的真实执行结果
# ----------------------------
def _fill(params: Any, results: Dict[str, Any]) -> Any:
    if isinstance(params, dict):
        return {k: _fill(v, results) for k, v in params.items()}
    if isinstance(params, str):
        m = re.fullmatch(r"\{+(\w+)\}+", params)
        if m and m.group(1) in results:
            return results[m.group(1)]
    return params


# ----------------------------
# 4. 贷款审批 Agent
# ----------------------------
class LoanApprovalAgent:
    def __init__(self, llm=None):
        self.llm = llm or init_chat_model(
            model="deepseek-v4-flash",
            extra_body={"thinking": {"type": "disabled"}},
        )

        self.plan_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个贷款申请自动审批助手。请根据用户问题生成可执行的步骤计划。\n"
                    "每个步骤必须明确使用哪个工具，以及工具输入参数。\n\n"
                    "可用工具：\n"
                    "- validate_form(age: int, monthly_income: float, loan_amount: float)：验证贷款申请表单\n"
                    "- calculate_max_loan(age: int, monthly_income: float)：计算最大可贷额度\n"
                    "- submit_form(age: int, monthly_income: float, loan_amount: float, max_loan: str)：提交贷款申请\n\n"
                    "如果某一步需要引用前一步结果，可以在 params 中写占位符，例如：\n"
                    '{{"max_loan": "{{step_2_result}}"}}\n'
                    "请按照 Plan 结构返回步骤。",
                ),
                ("human", "用户需求：{input}"),
            ]
        )

        self.summary_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一个贷款审批助手。请根据执行结果，给出清晰、自然、礼貌的回复。\n"
                    "如果验证失败，需要明确说明失败原因；如果审批通过，需要说明批准额度。",
                ),
                (
                    "human",
                    "用户需求：{input}\n\n执行过程：\n{context}",
                ),
            ]
        )

        self.plan_chain = self.plan_prompt | self.llm.with_structured_output(Plan)
        self.summary_chain = self.summary_prompt | self.llm

    def run(self, user_input: str) -> str:
        print("用户输入：", user_input)
        print("=========================== 1. Plan 阶段 ===========================")
        plan = self.plan_chain.invoke({"input": user_input})

        if not plan.steps:
            return "无法生成有效审批计划，请补充年龄、月收入、申请额度等信息。"

        print("=== 审批计划 ===")
        for step in plan.steps:
            print(
                f"{step.id}. {step.description} | "
                f"工具：{step.tool} | 参数：{step.params}"
            )

        print("=========================== 2. Execute 阶段 ===========================")
        """
            # 1. results (程序看，为了传参)
            results = {
                "step_1_result": "VALID",
                "step_2_result": "48000.0"
            }
            
            # 2. logs (列表状态，为了记录)
            logs = [
                "步骤 1：验证表单信息\n结果：VALID",
                "步骤 2：计算最大可贷额度\n结果：48000.0"
            ]
            
            # 3. context (大模型看，为了总结)
            context = (
                "步骤 1：验证表单信息\n"
                "结果：VALID\n\n"
                "步骤 2：计算最大可贷额度\n"
                "结果：48000.0"
            )
        """
        results: Dict[str, Any] = {}
        logs: List[str] = []
        print("=== 工具执行 ===")
        for step in plan.steps:
            params = _fill(step.params, results)
            tool_obj = TOOLS_BY_NAME.get(step.tool)

            if not tool_obj:
                return f"步骤 {step.id} 失败：找不到工具 {step.tool}"

            print(f"\n执行步骤 {step.id}：{step.description}")
            print(f"调用工具：{step.tool}")
            print(f"调用参数：{json.dumps(params, ensure_ascii=False)}")
            result = tool_obj.invoke(params)

            results[f"step_{step.id}_result"] = result
            logs.append(f"步骤 {step.id}：{step.description}\n结果：{result}")
            print(f"执行结果：{result}")

            # 短路：验证不通过就立即终止，不再执行后续“算额度/提交”
            if step.tool == "validate_form" and result != "VALID":
                # return f"❌ 贷款申请表单验证失败：{result}"
                print("\n贷款申请表单验证失败，终止后续步骤。")
                print("=========================== 3. Summary 阶段 ===========================")
                context = "\n\n".join(logs)
                response = self.summary_chain.invoke(
                    {
                        "input": user_input,
                        "context": context,
                    }
                )
                return response.content

        print("=========================== 3. Summary 阶段 ===========================")
        context = "\n\n".join(logs)
        response = self.summary_chain.invoke(
            {
                "input": user_input,
                "context": context,
            }
        )
        return response.content


# ----------------------------
# 5. 运行示例
# ----------------------------
if __name__ == "__main__":
    agent = LoanApprovalAgent()

    print(agent.run("处理贷款申请：年龄28岁，月收入8000元，申请贷款50000元。"))
    print(agent.run("处理贷款申请：年龄17岁，月收入8000元，申请贷款50000元。"))
    # print(agent.run("处理贷款申请：年龄18岁，月收入8000元，申请贷款1000000元。"))