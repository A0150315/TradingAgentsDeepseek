"""
智能体模块
包含所有类型的智能体：分析师、研究员、交易员、风险管理员
"""

from .analysts import *
from .researchers import *
from .trader import *
from .risk_management import *

__all__ = [
    # 分析师
    'FundamentalAnalyst',
    'TechnicalAnalyst',
    'SentimentAnalyst', 
    'NewsAnalyst',
    'create_fundamental_analyst',
    'create_technical_analyst',
    'create_sentiment_analyst',
    'create_news_analyst',
    
    # 研究员
    'BullResearcher',
    'BearResearcher',
    'create_bull_researcher',
    'create_bear_researcher',
    
    # 交易员
    'Trader',
    'create_trader',
    
    # 风险管理团队
    'ConservativeAnalyst',
    'AggressiveAnalyst',
    'NeutralAnalyst',
    'RiskManager',
    'RiskDebateCoordinator',
    'create_conservative_analyst',
    'create_aggressive_analyst',
    'create_neutral_analyst',
    'create_risk_manager',
    'create_risk_debate_coordinator',
    
    # 基金经理
    'FundManager',
    'create_fund_manager',
]