""""
Context Precision
- 在检索到的上下文片段中，相关的片段是否被排在了更靠前的位置。
- 得分越高，说明检索器的排序能力越好，把有用的信息都放在了前面

# 公式： Context_Precision@K = [ Σ(Precision@k × v_k) (k从1到K) ] / Top_K相关项总数
# 注意：
- v_k 为相关性判断值 (1 或 0)
- Precision@k 为前k个片段中相关片段的比例，即Precision@k = (前k个结果中相关片段数量 / k)
"""


import numpy as np
def _calculate_average_precision(verdict_list) -> float:
    score = np.nan
    numerator = sum(
        [
            (sum(verdict_list[: i + 1]) / (i + 1)) * verdict_list[i]
            for i in range(len(verdict_list)) # i= 0,1,2,3,4
        ]
    )
    denominator = sum(verdict_list) + 1e-10
    print(denominator)
    print(numerator)
    score = numerator / denominator
    return score
# 1--相关的文档片段，0，不相关的文档片段
verdict_list = [1, 0, 1, 1, 0]
score = _calculate_average_precision(verdict_list)
print("score1:",score)  # 输出结果
'''
i= 0,1,2,3,4
第一个片段：(1 / 0+1) * 1 = 1
第二个片段：(1 / 1+1) * 0 = 0
第三个片段：(2 / 2+1) * 1 = 0.6667
第四个片段：(3 / 3+1) * 1 = 0.75
第五个片段：(3 / 4+1) * 0 = 0
分子总和：1 + 0 + 0.6667 + 0.75 + 0 = 2.4167
相关片段的总数为3，所以分母为3
最终得分：2.4167 / 3 ≈ 0.8056
'''

verdict_list = [1, 1, 0, 1, 0]
score = _calculate_average_precision(verdict_list)
print("score2:",score)  # 输出结果