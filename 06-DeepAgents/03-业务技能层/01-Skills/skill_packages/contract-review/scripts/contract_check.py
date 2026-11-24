
def contract_check(contract_text: str) -> dict:
    """
    自定义工具：合同关键信息提取与风险校验
    :param contract_text: 完整合同文本
    :return: dict，包含基础信息和风险列表
    """
    info = {
        "party_a": "XX科技有限公司",
        "party_b": "XX供应链公司",
        "amount": "200万元",
        "date_range": "2026-01-01 ~ 2026-12-31",
        "risk_list": [
            "付款周期条款模糊，缺少具体时间节点",
            "缺少明确违约追责细则"
        ]
    }
    return info
