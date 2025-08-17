"""
工具发射器统一接口
提供所有结构化结果发射工具的统一导入入口
"""

# 分析师工具
from .analyst_emitters import (
    emit_fundamental_analysis,
    emit_technical_analysis,
    emit_news_analysis,
    emit_sentiment_analysis
)

# 研究员工具
from .research_emitters import (
    emit_bull_research_result,
    emit_bear_research_result
)

# 决策工具
from .decision_emitters import (
    emit_fund_manager_decision
)

# 交易工具
from .trading_emitters import (
    emit_trading_decision
)

# 协调工具
from .coordination_emitters import (
    emit_debate_quality_evaluation,
    emit_debate_judgment
)

# 风险管理工具
from .risk_management_emitters import (
    emit_conservative_risk_analysis,
    emit_aggressive_opportunity_analysis,
    emit_neutral_balance_analysis,
    emit_risk_management_decision
)

__all__ = [
    # 分析师工具
    'emit_fundamental_analysis',
    'emit_technical_analysis', 
    'emit_news_analysis',
    'emit_sentiment_analysis',
    
    # 研究员工具
    'emit_bull_research_result',
    'emit_bear_research_result',
    
    # 决策工具
    'emit_fund_manager_decision',
    
    # 交易工具
    'emit_trading_decision',
    
    # 协调工具
    'emit_debate_quality_evaluation',
    'emit_debate_judgment',
    
    # 风险管理工具
    'emit_conservative_risk_analysis',
    'emit_aggressive_opportunity_analysis',
    'emit_neutral_balance_analysis',
    'emit_risk_management_decision'
]