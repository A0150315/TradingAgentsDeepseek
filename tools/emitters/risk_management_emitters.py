"""
风险管理工具模块
提供风险分析师和风险管理总监的结构化输出工具
"""
from typing import Dict, Any, List


def emit_conservative_risk_analysis(
    risk_assessment: str,
    risk_level: str,  # 低/中/高
    key_risks: List[str],
    conservative_recommendation: str,
    position_adjustment: str,
    risk_mitigation: List[str],
    alternative_strategies: List[str],
    concerns: List[str],
    confidence_level: float,
    **kwargs
) -> Dict[str, Any]:
    """
    保守风险分析结果输出工具
    
    用途：保守风险分析师使用此工具输出对交易决策的风险评估结果
    
    参数：
        risk_assessment: 整体风险评估
        risk_level: 风险等级（低/中/高）
        key_risks: 主要风险因素列表
        conservative_recommendation: 保守建议
        position_adjustment: 仓位调整建议
        risk_mitigation: 风险缓解措施列表
        alternative_strategies: 替代策略列表
        concerns: 主要担忧列表
        confidence_level: 信心水平（0-1）
    """
    return {
        "risk_assessment": risk_assessment,
        "risk_level": risk_level,
        "key_risks": key_risks,
        "conservative_recommendation": conservative_recommendation,
        "position_adjustment": position_adjustment,
        "risk_mitigation": risk_mitigation,
        "alternative_strategies": alternative_strategies,
        "concerns": concerns,
        "confidence_level": confidence_level
    }


def emit_aggressive_opportunity_analysis(
    opportunity_assessment: str,
    upside_potential: str,  # 高/中/低
    key_opportunities: List[str],
    aggressive_recommendation: str,
    position_enhancement: str,
    growth_catalysts: List[str],
    competitive_advantages: List[str],
    timing_factors: List[str],
    confidence_level: float,
    **kwargs
) -> Dict[str, Any]:
    """
    激进机会分析结果输出工具
    
    用途：激进风险分析师使用此工具输出对交易决策的机会评估结果
    
    参数：
        opportunity_assessment: 整体机会评估
        upside_potential: 上行潜力（高/中/低）
        key_opportunities: 主要机会因素列表
        aggressive_recommendation: 激进建议
        position_enhancement: 仓位提升建议
        growth_catalysts: 增长催化剂列表
        competitive_advantages: 竞争优势列表
        timing_factors: 时机因素列表
        confidence_level: 信心水平（0-1）
    """
    return {
        "opportunity_assessment": opportunity_assessment,
        "upside_potential": upside_potential,
        "key_opportunities": key_opportunities,
        "aggressive_recommendation": aggressive_recommendation,
        "position_enhancement": position_enhancement,
        "growth_catalysts": growth_catalysts,
        "competitive_advantages": competitive_advantages,
        "timing_factors": timing_factors,
        "confidence_level": confidence_level
    }


def emit_neutral_balance_analysis(
    balance_assessment: str,
    risk_reward_ratio: str,  # 合理/偏高/偏低
    key_considerations: List[str],
    balanced_recommendation: str,
    optimal_position_size: str,
    timing_assessment: List[str],
    diversification_needs: List[str],
    monitoring_metrics: List[str],
    confidence_level: float,
    **kwargs
) -> Dict[str, Any]:
    """
    中性平衡分析结果输出工具
    
    用途：中性风险分析师使用此工具输出对交易决策的平衡评估结果
    
    参数：
        balance_assessment: 整体平衡评估
        risk_reward_ratio: 风险收益比（合理/偏高/偏低）
        key_considerations: 主要考虑因素列表
        balanced_recommendation: 平衡建议
        optimal_position_size: 最优仓位建议
        timing_assessment: 时机评估列表
        diversification_needs: 分散化需求列表
        monitoring_metrics: 监控指标列表
        confidence_level: 信心水平（0-1）
    """
    return {
        "balance_assessment": balance_assessment,
        "risk_reward_ratio": risk_reward_ratio,
        "key_considerations": key_considerations,
        "balanced_recommendation": balanced_recommendation,
        "optimal_position_size": optimal_position_size,
        "timing_assessment": timing_assessment,
        "diversification_needs": diversification_needs,
        "monitoring_metrics": monitoring_metrics,
        "confidence_level": confidence_level
    }


def emit_risk_management_decision(
    final_risk_assessment: str,
    recommended_action: str,  # BUY/HOLD/SELL
    position_adjustment: str,
    risk_level: str,  # 低/中/高
    key_risk_factors: List[str],
    risk_mitigation_measures: List[str],
    monitoring_requirements: List[str],
    contingency_plans: List[str],
    confidence_level: float,
    decision_rationale: str,
    winning_arguments: List[str],
    rejected_arguments: List[str],
    **kwargs
) -> Dict[str, Any]:
    """
    风险管理决策结果输出工具
    
    用途：风险管理总监使用此工具输出对风险辩论的最终评估决策
    
    参数：
        final_risk_assessment: 综合风险评估
        recommended_action: 推荐行动（BUY/HOLD/SELL）
        position_adjustment: 仓位调整建议
        risk_level: 风险等级（低/中/高）
        key_risk_factors: 关键风险因素列表
        risk_mitigation_measures: 风险缓解措施列表
        monitoring_requirements: 监控要求列表
        contingency_plans: 应急计划列表
        confidence_level: 信心水平（0-1）
        decision_rationale: 详细决策理由
        winning_arguments: 最有说服力的论点列表
        rejected_arguments: 被拒绝的论点列表
    """
    return {
        "final_risk_assessment": final_risk_assessment,
        "recommended_action": recommended_action,
        "position_adjustment": position_adjustment,
        "risk_level": risk_level,
        "key_risk_factors": key_risk_factors,
        "risk_mitigation_measures": risk_mitigation_measures,
        "monitoring_requirements": monitoring_requirements,
        "contingency_plans": contingency_plans,
        "confidence_level": confidence_level,
        "decision_rationale": decision_rationale,
        "winning_arguments": winning_arguments,
        "rejected_arguments": rejected_arguments
    }