"""
基金经理模块
负责最终投资决策的整合与执行
"""

from .fund_manager import FundManager, create_fund_manager

__all__ = ['FundManager', 'create_fund_manager']