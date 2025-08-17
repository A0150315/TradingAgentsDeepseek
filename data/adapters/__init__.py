"""
数据适配器模块
统一不同数据源的接口
"""
from .market_data_provider import MarketDataAdapter, create_data_adapter

__all__ = ['MarketDataAdapter', 'create_data_adapter']