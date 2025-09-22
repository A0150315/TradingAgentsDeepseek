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
    # 执行计划
    immediate_action: str,
    position_change_rationale: str,
    weekly_monitoring_points: List[str],
    next_week_conditions: str,
    # 其他
    current_market_assessment: str,
    alternative_scenarios: str,
    **kwargs  # 忽略额外的未知参数
) -> Dict[str, Any]:
    """交易决策结果发射器（专注当前即时决策）

    用途: 让交易员基于当前仓位状态输出当前的具体操作决策

    参数说明:
    - recommendation: 交易建议 (BUY|HOLD|SELL)
    - confidence_score: 置信度评分 (0.0-1.0)
    - target_price: 目标价格
    - stop_loss: 止损价格
    - take_profit: 止盈价格
    - position_size: 目标仓位比例 (0.0-1.0) - 注意：这是目标仓位，不是增减量
    - time_horizon: 时间框架 (周/短期/中期)
    - reasoning: 基于当前仓位状态的决策理由
    - key_factors: 支持本次决策的关键因素
    - risk_factors: 本次操作的主要风险
    - acceptable_price_min: 当前可接受的最低执行价格
    - acceptable_price_max: 当前可接受的最高执行价格
    - immediate_action: 当前具体应该采取的行动
    - position_change_rationale: 仓位调整的具体原因
    - weekly_monitoring_points: 当前需要关注的监控点
    - next_week_conditions: 下周期重新评估的条件
    - current_market_assessment: 对当前市场时机的评估
    - alternative_scenarios: 如果市场条件变化的备选方案
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
            "acceptable_max": acceptable_price_max,
        },
        "risk_management": {"stop_loss": stop_loss, "take_profit": take_profit},
        "execution_plan": {
            "immediate_action": immediate_action,
            "position_change_rationale": position_change_rationale,
            "weekly_monitoring_points": weekly_monitoring_points,
            "next_week_conditions": next_week_conditions,
        },
        "market_timing": current_market_assessment,
        "alternatives": alternative_scenarios,
    }
