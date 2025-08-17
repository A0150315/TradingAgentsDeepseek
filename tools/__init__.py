"""
工具包初始化文件
集成所有数据获取工具
"""
from .google_news_tool import (
    GoogleNewsTool,
    create_google_news_tool,
    get_google_news,
    get_stock_news
)

from .yfinance_tool import (
    YFinanceTool,
    create_yfinance_tool,
    get_stock_data,
    get_stock_info,
    get_market_summary
)

__all__ = [
    # Google News 工具
    'GoogleNewsTool',
    'create_google_news_tool',
    'get_google_news',
    'get_stock_news',
    
    # YFinance 工具
    'YFinanceTool',
    'create_yfinance_tool',
    'get_stock_data',
    'get_stock_info',
    'get_market_summary'
]


class ToolKit:
    """工具包管理器"""
    
    def __init__(self):
        self.google_news = create_google_news_tool()
        self.yfinance = create_yfinance_tool()
    
    def get_stock_market_data(self, symbol: str, days_back: int = 30):
        """获取股票市场数据"""
        return self.yfinance.get_market_summary(symbol, days_back)
    
    def get_stock_news_data(self, symbol: str, days_back: int = 7):
        """获取股票新闻数据"""
        from datetime import datetime, timedelta
        curr_date = datetime.now().strftime('%Y-%m-%d')
        return self.google_news.get_stock_news(symbol, [f"{symbol} stock", f"{symbol} earnings", f"{symbol} news"], curr_date, days_back)
    
    def get_market_news_data(self, days_back: int = 7):
        """获取市场新闻数据"""
        from datetime import datetime
        curr_date = datetime.now().strftime('%Y-%m-%d')
        return self.google_news.search_market_news(None, curr_date, days_back)
    
    def get_comprehensive_data(self, symbol: str, days_back: int = 30):
        """获取综合数据"""
        market_data = self.get_stock_market_data(symbol, days_back)
        news_data = self.get_stock_news_data(symbol, min(days_back, 7))
        
        return {
            'market_data': market_data,
            'news_data': news_data,
            'symbol': symbol,
            'data_period': f"过去 {days_back} 天"
        }


def create_toolkit() -> ToolKit:
    """创建工具包实例"""
    return ToolKit()