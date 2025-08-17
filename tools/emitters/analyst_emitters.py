"""
分析师结果发射工具
提供分析师团队的结构化结果发射函数
"""

from typing import List, Dict, Any


def emit_fundamental_analysis(
    key_findings: List[str],
    recommendation: str,
    confidence_score: float,
    # 估值（展平参数）
    valuation_current_valuation: str,
    valuation_target_price_min: float,
    valuation_target_price_max: float,
    valuation_pe_assessment: str,
    valuation_pb_assessment: str,
    # 财务健康（展平参数）
    financial_overall_rating: str,
    financial_debt_level: str,
    financial_profitability: str,
    # 成长性（展平参数）
    growth_revenue_outlook: str,
    growth_market_position: str,
    growth_competitive_advantage: str,
    # 其他
    risk_factors: List[str],
    catalysts: List[str],
    time_short_term: str,
    time_long_term: str,
    supporting_evidence: str,
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """基本面分析结果发射器
    
    用途: 让基本面分析师通过工具调用输出基本面分析的最终结构化结果
    
    参数说明 (所有参数必填):
    - key_findings: 基本面关键发现列表
    - recommendation: 投资建议 (BUY|HOLD|SELL)
    - confidence_score: 置信度评分 (0.0-1.0)
    - valuation_*: 估值分析相关参数
    - financial_*: 财务健康相关参数  
    - growth_*: 成长性分析相关参数
    - risk_factors: 风险因素列表
    - catalysts: 催化剂列表
    - time_*: 时间框架预期
    - supporting_evidence: 支撑证据说明
    """
    return {
        "key_findings": key_findings,
        "recommendation": recommendation,
        "confidence_score": confidence_score,
        "valuation": {
            "current_valuation": valuation_current_valuation,
            "target_price_min": valuation_target_price_min,
            "target_price_max": valuation_target_price_max,
            "pe_assessment": valuation_pe_assessment,
            "pb_assessment": valuation_pb_assessment
        },
        "financial_health": {
            "overall_rating": financial_overall_rating,
            "debt_level": financial_debt_level,
            "profitability": financial_profitability
        },
        "growth_prospects": {
            "revenue_outlook": growth_revenue_outlook,
            "market_position": growth_market_position, 
            "competitive_advantage": growth_competitive_advantage
        },
        "risk_factors": risk_factors,
        "catalysts": catalysts,
        "time_horizon": {
            "short_term": time_short_term,
            "long_term": time_long_term
        },
        "supporting_evidence": supporting_evidence
    }


def emit_technical_analysis(
    key_findings: List[str],
    recommendation: str,
    confidence_score: float,
    trend_direction: str,
    trend_strength: str,
    # 关键位 (展平参数)
    levels_support_primary: float,
    levels_support_secondary: float,
    levels_resistance_primary: float,
    levels_resistance_secondary: float,
    # 技术信号 (展平参数)
    signals_momentum: str,
    signals_volume: str,
    signals_volatility: str,
    # 其他
    risk_factors: List[str],
    time_short_term: str,
    time_medium_term: str,
    time_long_term: str,
    supporting_evidence: str,
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """技术分析结果发射器
    
    用途: 让技术分析师通过工具调用输出技术分析的最终结构化结果
    
    参数说明:
    - key_findings: 技术分析关键发现
    - recommendation: 投资建议 (BUY|HOLD|SELL)
    - confidence_score: 置信度评分 (0.0-1.0)
    - trend_direction: 趋势方向 (上升/下降/横盘)
    - trend_strength: 趋势强度 (强/中/弱)
    - levels_*: 关键支撑阻力位
    - signals_*: 各类技术信号
    - risk_factors: 技术面风险因素
    - time_*: 不同时间框架分析
    - supporting_evidence: 技术分析依据
    """
    return {
        "key_findings": key_findings,
        "recommendation": recommendation,
        "confidence_score": confidence_score,
        "trend_direction": trend_direction,
        "trend_strength": trend_strength,
        "key_levels": {
            "support": {
                "primary": levels_support_primary,
                "secondary": levels_support_secondary
            },
            "resistance": {
                "primary": levels_resistance_primary,
                "secondary": levels_resistance_secondary
            }
        },
        "technical_signals": {
            "momentum": signals_momentum,
            "volume": signals_volume,
            "volatility": signals_volatility
        },
        "risk_factors": risk_factors,
        "time_horizon": {
            "short_term": time_short_term,
            "medium_term": time_medium_term,
            "long_term": time_long_term
        },
        "supporting_evidence": supporting_evidence
    }


def emit_news_analysis(
    key_findings: List[str],
    recommendation: str,
    confidence_score: float,
    news_impact: str,
    impact_magnitude: float,
    market_reaction_prediction: str,
    catalyst_events: List[str],
    risk_factors: List[str],
    time_short_term: str,
    time_medium_term: str,
    supporting_evidence: str,
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """新闻分析结果发射器
    
    用途: 让新闻分析师通过工具调用输出新闻分析的最终结构化结果
    
    参数说明:
    - key_findings: 新闻分析关键发现
    - recommendation: 投资建议 (BUY|HOLD|SELL)
    - confidence_score: 置信度评分 (0.0-1.0)
    - news_impact: 新闻影响评估 (非常利好/利好/中性/利空/非常利空)
    - impact_magnitude: 影响强度 (0.0-1.0)
    - market_reaction_prediction: 市场反应预测
    - catalyst_events: 催化剂事件列表
    - risk_factors: 新闻相关风险因素
    - time_*: 时间框架影响分析
    - supporting_evidence: 新闻分析依据
    """
    return {
        "key_findings": key_findings,
        "recommendation": recommendation,
        "confidence_score": confidence_score,
        "news_impact": news_impact,
        "impact_magnitude": impact_magnitude,
        "market_reaction_prediction": market_reaction_prediction,
        "catalyst_events": catalyst_events,
        "risk_factors": risk_factors,
        "time_frame": {
            "short_term": time_short_term,
            "medium_term": time_medium_term
        },
        "supporting_evidence": supporting_evidence
    }


def emit_sentiment_analysis(
    key_findings: List[str],
    recommendation: str,
    confidence_score: float,
    sentiment_level: str,
    sentiment_score: float,
    sentiment_magnitude: float,
    turning_points: List[str],
    contrarian_signals: List[str],
    market_mood_indicators: Dict[str, Any],
    risk_factors: List[str],
    time_short_term: str,
    time_medium_term: str,
    supporting_evidence: str,
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """情绪分析结果发射器
    
    用途: 让情绪分析师通过工具调用输出情绪分析的最终结构化结果
    
    参数说明:
    - key_findings: 情绪分析关键发现
    - recommendation: 投资建议 (BUY|HOLD|SELL)  
    - confidence_score: 置信度评分 (0.0-1.0)
    - sentiment_level: 情绪水平 (极度乐观/乐观/中性/悲观/极度悲观)
    - sentiment_score: 情绪评分 (0.0-1.0, 0.5为中性)
    - sentiment_magnitude: 情绪强度 (0.0-1.0)
    - turning_points: 情绪转折点分析
    - contrarian_signals: 逆向投资信号
    - market_mood_indicators: 市场情绪指标
    - risk_factors: 情绪相关风险因素
    - time_*: 时间框架情绪分析
    - supporting_evidence: 情绪分析依据
    """
    return {
        "key_findings": key_findings,
        "recommendation": recommendation,
        "confidence_score": confidence_score,
        "sentiment_level": sentiment_level,
        "sentiment_score": sentiment_score,
        "sentiment_magnitude": sentiment_magnitude,
        "turning_points": turning_points,
        "contrarian_signals": contrarian_signals,
        "market_mood_indicators": market_mood_indicators,
        "risk_factors": risk_factors,
        "time_frame": {
            "short_term": time_short_term,
            "medium_term": time_medium_term
        },
        "supporting_evidence": supporting_evidence
    }