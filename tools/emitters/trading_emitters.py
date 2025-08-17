"""
交易结果发射工具
提供交易员的结构化结果发射函数
"""

from typing import List, Dict, Any


def emit_trading_decision(
    recommendation: str,
    confidence_score: float,
    target_price: float,
    stop_loss: float,
    take_profit: float,
    position_size: float,
    time_horizon: str,
    reasoning: str,
    key_factors: List[str],
    risk_factors: List[str],
    # 价格区间参数
    acceptable_price_min: float,
    acceptable_price_max: float,
    # 执行计划（展平参数）
    execution_entry_strategy: str,
    execution_exit_strategy: str,
    execution_monitoring_points: List[str],
    execution_contingency_plan: str,
    # 其他
    market_timing: str,
    alternatives: str,
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """交易决策结果发射器
    
    用途: 让交易员通过工具调用输出交易决策的最终结构化结果
    
    参数说明:
    - recommendation: 交易建议 (BUY|HOLD|SELL)
    - confidence_score: 置信度评分 (0.0-1.0)
    - target_price: 目标价格
    - stop_loss: 止损价格
    - take_profit: 止盈价格
    - position_size: 建议仓位比例 (0.0-1.0)
    - time_horizon: 时间框架 (短期/中期/长期)
    - reasoning: 详细的决策理由
    - key_factors: 关键因素列表
    - risk_factors: 风险因素列表
    - acceptable_price_min: 可接受的最低价格
    - acceptable_price_max: 可接受的最高价格
    - execution_*: 执行计划相关参数
    - market_timing: 入场时机建议
    - alternatives: 备选方案
    """
    return {
        "recommendation": recommendation,
        "confidence_score": confidence_score,
        "position_size": position_size,
        "time_horizon": time_horizon,
        "reasoning": reasoning,
        "key_factors": key_factors,
        "risk_factors": risk_factors,
        "price_range": {
            "target_price": target_price,
            "acceptable_min": acceptable_price_min,
            "acceptable_max": acceptable_price_max
        },
        "risk_management": {
            "stop_loss": stop_loss,
            "take_profit": take_profit
        },
        "execution_plan": {
            "entry_strategy": execution_entry_strategy,
            "exit_strategy": execution_exit_strategy,
            "monitoring_points": execution_monitoring_points,
            "contingency_plan": execution_contingency_plan
        },
        "market_timing": market_timing,
        "alternatives": alternatives
    }