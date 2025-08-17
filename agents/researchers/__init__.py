"""
研究团队模块
包含多头研究员和空头研究员，负责团队辩论和投资决策
"""

from .bull_researcher import BullResearcher, create_bull_researcher
from .bear_researcher import BearResearcher, create_bear_researcher

__all__ = [
    'BullResearcher',
    'create_bull_researcher',
    'BearResearcher',
    'create_bear_researcher'
]