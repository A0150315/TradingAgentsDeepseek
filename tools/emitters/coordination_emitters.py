"""
协调结果发射工具
提供协调层的结构化结果发射函数
"""

from typing import List, Dict, Any


def emit_debate_quality_evaluation(
    debate_quality: str,
    quality_score: float,
    argument_strengths: Dict[str, str],
    key_insights: List[str],
    consensus_level: str,
    decision_confidence: float,
    evaluation_summary: str,
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """辩论质量评估结果发射器
    
    用途: 让辩论协调器通过工具调用输出辩论质量评估的最终结构化结果
    
    参数说明:
    - debate_quality: 辩论质量评级（优秀/良好/一般/较差）
    - quality_score: 质量评分 (0.0-1.0)
    - argument_strengths: 论证强度分析 {"bull": "多头论证强度", "bear": "空头论证强度"}
    - key_insights: 关键洞察列表
    - consensus_level: 共识水平（高度共识/部分共识/分歧较大）
    - decision_confidence: 决策置信度 (0.0-1.0)
    - evaluation_summary: 评估总结
    """
    return {
        "debate_quality": debate_quality,
        "quality_score": quality_score,
        "argument_strengths": argument_strengths,
        "key_insights": key_insights,
        "consensus_level": consensus_level,
        "decision_confidence": decision_confidence,
        "evaluation_summary": evaluation_summary
    }


def emit_debate_judgment(
    decision: str,
    confidence: float,
    reasoning: str,
    supporting_factors: List[str],
    risk_factors: List[str],
    investment_strategy: str,
    winner: str,
    winning_arguments: List[str],
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """辩论判断结果发射器
    
    用途: 让辩论协调器通过工具调用输出辩论判断的最终结构化结果
    
    参数说明:
    - decision: 投资决策 (强烈买入/买入/持有/卖出/强烈卖出)
    - confidence: 决策置信度 (0.0-1.0)
    - reasoning: 决策理由总结
    - supporting_factors: 关键支持因素列表
    - risk_factors: 主要风险因素列表
    - investment_strategy: 投资策略建议
    - winner: 辩论获胜方 (bull/bear/draw)
    - winning_arguments: 获胜论点列表
    """
    return {
        "decision": decision,
        "confidence": confidence,
        "reasoning": reasoning,
        "supporting_factors": supporting_factors,
        "risk_factors": risk_factors,
        "investment_strategy": investment_strategy,
        "winner": winner,
        "winning_arguments": winning_arguments
    }