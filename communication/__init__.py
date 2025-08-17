"""
通信协议模块
管理智能体之间的通信和协作
"""

from .debate_coordinator import DebateCoordinator, create_debate_coordinator

__all__ = [
    'DebateCoordinator',
    'create_debate_coordinator'
]