"""
研究员结果发射工具
提供研究团队的结构化结果发射函数
"""

from typing import List, Dict, Any


def emit_bull_research_result(
    bull_thesis: str,
    key_bull_points: List[str],
    target_price: float,
    upside_potential: float,
    investment_horizon: str,
    catalysts: List[str],
    risk_mitigation: List[str],
    confidence_level: float,
    supporting_evidence: str,
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """多头研究结果发射器
    
    用途: 让多头研究员通过工具调用输出多头研究的最终结构化结果
    
    参数说明:
    - bull_thesis: 核心多头观点
    - key_bull_points: 核心买入理由列表（5个）
    - target_price: 目标价格
    - upside_potential: 上涨空间百分比
    - investment_horizon: 投资时间框架（短期/中期/长期）
    - catalysts: 催化剂列表
    - risk_mitigation: 风险缓释因素列表
    - confidence_level: 置信度评分 (0.0-1.0)
    - supporting_evidence: 详细论证说明
    """
    return {
        "bull_thesis": bull_thesis,
        "key_bull_points": key_bull_points,
        "target_price": target_price,
        "upside_potential": upside_potential,
        "investment_horizon": investment_horizon,
        "catalysts": catalysts,
        "risk_mitigation": risk_mitigation,
        "confidence_level": confidence_level,
        "supporting_evidence": supporting_evidence
    }


def emit_bear_research_result(
    bear_thesis: str,
    key_risk_points: List[str],
    target_price: float,
    downside_risk: float,
    risk_horizon: str,
    negative_catalysts: List[str],
    structural_issues: List[str],
    confidence_level: float,
    supporting_evidence: str,
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """空头研究结果发射器
    
    用途: 让空头研究员通过工具调用输出空头研究的最终结构化结果
    
    参数说明:
    - bear_thesis: 核心空头观点
    - key_risk_points: 核心风险点列表（5个）
    - target_price: 目标价格
    - downside_risk: 下跌风险百分比
    - risk_horizon: 风险时间框架（短期/中期/长期）
    - negative_catalysts: 负面催化剂列表
    - structural_issues: 结构性问题列表
    - confidence_level: 置信度评分 (0.0-1.0)
    - supporting_evidence: 详细论证说明
    """
    return {
        "bear_thesis": bear_thesis,
        "key_risk_points": key_risk_points,
        "target_price": target_price,
        "downside_risk": downside_risk,
        "risk_horizon": risk_horizon,
        "negative_catalysts": negative_catalysts,
        "structural_issues": structural_issues,
        "confidence_level": confidence_level,
        "supporting_evidence": supporting_evidence
    }