"""
通用工具封装
统一对外提供给各个Agent使用的工具函数，避免在Agent内重复创建与包装。
"""

from typing import List
from datetime import datetime

from utils.logger import get_logger
from .google_news_tool import create_google_news_tool


_logger = get_logger()
_NEWS_TOOL = None


def _get_news_tool():
    """懒加载并复用单例的 GoogleNewsTool 实例"""
    global _NEWS_TOOL
    if _NEWS_TOOL is None:
        _logger.info("初始化GoogleNewsTool单例")
        _NEWS_TOOL = create_google_news_tool()
    return _NEWS_TOOL


def google_search(queries: List[str], curr_date: str = None, look_back_days: int = 7) -> str:
    """Google新闻主题检索

    用途:
    - 基于一组主题/关键词检索最近 N 天相关新闻，返回可读的 Markdown 汇总。

    参数:
    - queries (List[str], required): 主题/关键词列表，至少包含 1 项。
    - curr_date (str, optional, default: 今天 YYYY-MM-DD): 作为检索时间上限。
    - look_back_days (int, optional, default: 7): 回看天数，建议范围 1-30。

    返回:
    - str: Markdown 文本，包含主题标题、前若干条新闻条目（标题/来源/时间/链接）及来源说明。

    注意:
    - 作为 LLM 工具使用时，queries 为必填；若缺失会使用最小兜底以避免中断，但建议显式提供以提升相关性。
    - 结果为聚合摘要，不保证覆盖全量新闻，时间和可用性受外部数据源影响。

    示例:
    - google_search(queries=["NVDA earnings", "semiconductor demand"], look_back_days=5)
    """
    tool = _get_news_tool()
    if curr_date is None:
        curr_date = datetime.now().strftime("%Y-%m-%d")
    if not queries:
        queries = ["stock market", "economy news", "federal reserve", "inflation", "GDP"]

    _logger.info(f"执行统一google_search: 主题数={len(queries)} 回看={look_back_days}天")
    return tool.search_market_news(queries, curr_date, look_back_days)


def get_stock_news_tool(symbol: str, queries: List[str], curr_date: str = None, look_back_days: int = 7) -> str:
    """股票新闻聚合

    用途:
    - 针对某股票代码，结合多组查询词聚合最近 N 天新闻，返回 Markdown 汇总用于分析引用。
    - 你无须在queries中包含symbol，我会自动添加。

    参数:
    - symbol (str, required): 股票代码，如 "AAPL"、"NVDA"。
    - queries (List[str], required): 附加关键词列表（如 "earnings", "guidance", "SEC filing"）。
    - curr_date (str, optional, default: 今天 YYYY-MM-DD): 作为检索时间上限。
    - look_back_days (int, optional, default: 7): 回看天数，建议范围 1-30。

    返回:
    - str: Markdown 文本，分块展示各查询的前若干条新闻（标题/来源/时间/链接）及来源说明。

    注意:
    - queries 为必填；若缺失会使用标准兜底 [symbol, f"{symbol} stock", f"{symbol} earnings", f"{symbol} news"]，但建议显式传入以提高相关性。
    - 结果为聚合摘要，不保证覆盖全量新闻。

    示例:
    - get_stock_news_tool("NVDA", ["H200", "AI GPU", "Earnings"], look_back_days=5)
    - 然后我就会搜索 “NVDA+H200”、 “NVDA+AI GPU”、 “NVDA+Earnings” 的新闻
    """
    tool = _get_news_tool()
    if curr_date is None:
        curr_date = datetime.now().strftime("%Y-%m-%d")
    if queries is None:
        queries = [symbol, f"{symbol} stock", f"{symbol} earnings", f"{symbol} news"]

    _logger.info(f"执行统一get_stock_news_tool: {symbol} 主题数={len(queries)} 回看={look_back_days}天")
    return tool.get_stock_news(symbol, queries, curr_date, look_back_days)

__all__ = [
    "google_search",
    "get_stock_news_tool",
]


