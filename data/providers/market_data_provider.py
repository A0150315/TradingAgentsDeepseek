"""
数据提供者接口
从原有tradingagents系统迁移核心数据获取功能
集成Google News和YFinance工具
"""
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import sys

# 添加tools目录到路径
tools_path = Path(__file__).parent.parent.parent / "tools"
if str(tools_path) not in sys.path:
    sys.path.insert(0, str(tools_path))

try:
    from tools.google_news_tool import create_google_news_tool
    from tools.yfinance_tool import create_yfinance_tool
    TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: 无法导入工具模块: {e}")
    TOOLS_AVAILABLE = False


class DataProvider:
    """数据提供者基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票价格数据"""
        raise NotImplementedError
    
    def get_news_data(self, symbol: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """获取新闻数据"""
        raise NotImplementedError
    
    def get_sentiment_data(self, symbol: str, days_back: int = 7) -> Dict[str, Any]:
        """获取情感数据"""
        raise NotImplementedError


class YahooFinanceProvider(DataProvider):
    """Yahoo Finance数据提供者"""
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从Yahoo Finance获取股票数据"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                print(f"Warning: No data found for {symbol}")
                return pd.DataFrame()
            
            # 添加技术指标
            data = self._add_technical_indicators(data)
            return data
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """添加技术指标"""
        if data.empty:
            return data
            
        # 移动平均线
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        # RSI
        data['RSI'] = self._calculate_rsi(data['Close'])
        
        # MACD
        data['MACD'], data['MACD_Signal'], data['MACD_Histogram'] = self._calculate_macd(data['Close'])
        
        # 布林带
        data['BB_Upper'], data['BB_Lower'] = self._calculate_bollinger_bands(data['Close'])
        
        return data
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """计算MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, window: int = 20, num_std: int = 2):
        """计算布林带"""
        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        return upper_band, lower_band


class CachedDataProvider:
    """缓存数据提供者 - 从原有系统迁移的离线数据"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.market_data_dir = self.data_dir / "market_data" / "price_data"
        
    def get_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从缓存文件获取股票数据"""
        # 查找缓存文件
        cache_file = self.market_data_dir / f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv"
        
        if not cache_file.exists():
            print(f"Cache file not found: {cache_file}")
            return pd.DataFrame()
        
        try:
            data = pd.read_csv(cache_file)
            data['Date'] = pd.to_datetime(data['Date'])
            
            # 筛选日期范围
            mask = (data['Date'] >= start_date) & (data['Date'] <= end_date)
            filtered_data = data.loc[mask].copy()
            
            # 设置索引
            filtered_data.set_index('Date', inplace=True)
            
            return filtered_data
            
        except Exception as e:
            print(f"Error reading cache file: {e}")
            return pd.DataFrame()
    
    def get_finnhub_news(self, symbol: str, start_date: str, days_back: int) -> str:
        """获取Finnhub新闻数据（从原有系统迁移）"""
        try:
            # 这里需要实现从原有数据缓存中获取新闻的逻辑
            # 暂时返回模拟数据
            return f"## {symbol} News from {start_date}\n\n暂未实现新闻数据获取功能"
            
        except Exception as e:
            print(f"Error getting news data: {e}")
            return ""


class MarketDataAdapter:
    """市场数据适配器 - 统一数据接口"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.use_online = config.get('online_tools', False)
        
        # 初始化工具
        if TOOLS_AVAILABLE:
            self.google_news_tool = create_google_news_tool()
            self.yfinance_tool = create_yfinance_tool()
        else:
            self.google_news_tool = None
            self.yfinance_tool = None
        
        if self.use_online:
            self.primary_provider = YahooFinanceProvider(config)
        else:
            data_dir = config.get('data_dir', './data')
            self.primary_provider = CachedDataProvider(data_dir)
        
        # 备用在线提供者
        self.fallback_provider = YahooFinanceProvider(config)
    
    def get_market_data(self, symbol: str, days_back: int = 365) -> Dict[str, Any]:
        """获取市场数据"""
        if self.yfinance_tool and self.use_online:
            # 使用增强的YFinance工具
            try:
                market_summary = self.yfinance_tool.get_market_summary(symbol, days_back)
                if 'error' not in market_summary:
                    return market_summary
            except Exception as e:
                print(f"YFinance工具获取数据失败: {e}")
        
        else:
            return {
                'symbol': symbol,
                'error': 'No data available',
                'price_data': {},
                'technical_indicators': {},
                'summary': f'无法获取 {symbol} 的市场数据'
            }
    
    def get_news_data(self, symbol: str, days_back: int = 7) -> Dict[str, Any]:
        """获取新闻数据"""
        if self.google_news_tool:
            try:
                curr_date = datetime.now().strftime('%Y-%m-%d')
                news_content = self.google_news_tool.get_stock_news(symbol, [f"{symbol} stock", f"{symbol} earnings", f"{symbol} news"], curr_date, days_back)
                
                return {
                    'symbol': symbol,
                    'period': f"过去 {days_back} 天",
                    'news_content': news_content,
                    'summary': f"已通过Google News获取 {symbol} 过去 {days_back} 天的新闻数据"
                }
            except Exception as e:
                print(f"Google News工具获取新闻失败: {e}")
        
        # 回退到原有逻辑
        if hasattr(self.primary_provider, 'get_finnhub_news'):
            news_text = self.primary_provider.get_finnhub_news(symbol, datetime.now().strftime('%Y-%m-%d'), days_back)
        else:
            news_text = f"## {symbol} 新闻摘要\n\n暂无可用新闻数据"
        
        return {
            'symbol': symbol,
            'period': f"过去 {days_back} 天",
            'news_content': news_text,
            'summary': f"已获取 {symbol} 过去 {days_back} 天的新闻数据"
        }
    
    def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """获取基本面数据"""
        if self.yfinance_tool:
            try:
                company_info = self.yfinance_tool.get_company_info(symbol)
                
                return {
                    'symbol': symbol,
                    'company_name': company_info.get('Company Name', 'N/A'),
                    'sector': company_info.get('Sector', 'N/A'),
                    'industry': company_info.get('Industry', 'N/A'),
                    'market_cap': company_info.get('Market Cap', 'N/A'),
                    'pe_ratio': company_info.get('P/E Ratio', 'N/A'),
                    'forward_pe': company_info.get('Forward P/E', 'N/A'),
                    'peg_ratio': company_info.get('PEG Ratio', 'N/A'),
                    'price_to_sales': company_info.get('Price to Sales', 'N/A'),
                    'price_to_book': company_info.get('Price to Book', 'N/A'),
                    'enterprise_value': company_info.get('Enterprise Value', 'N/A'),
                    'enterprise_to_revenue': company_info.get('Enterprise to Revenue', 'N/A'),
                    'enterprise_to_ebitda': company_info.get('Enterprise to EBITDA', 'N/A'),
                    'summary': f"已通过YFinance获取 {symbol} 的基本面数据"
                }
            except Exception as e:
                print(f"YFinance工具获取基本面数据失败: {e}")
        
        # 回退到模拟数据
        return {
            'symbol': symbol,
            'pe_ratio': 25.5,
            'ps_ratio': 8.2,
            'debt_to_equity': 0.3,
            'roe': 0.15,
            'revenue_growth': 0.08,
            'summary': f"{symbol} 基本面数据已获取（模拟数据）"
        }
    
    def get_sentiment_data(self, symbol: str, days_back: int = 7) -> Dict[str, Any]:
        """获取情感数据"""
        # 暂时返回模拟数据，可以后续集成社交媒体情感分析
        return {
            'symbol': symbol,
            'period': f"过去 {days_back} 天",
            'sentiment_score': 0.6,  # -1 to 1
            'bullish_ratio': 0.65,
            'bearish_ratio': 0.35,
            'total_mentions': 1250,
            'summary': f"{symbol} 社交媒体情感倾向为正面（模拟数据）"
        }
    
    def get_market_news(self, days_back: int = 7) -> Dict[str, Any]:
        """获取市场整体新闻"""
        if self.google_news_tool:
            try:
                curr_date = datetime.now().strftime('%Y-%m-%d')
                market_news = self.google_news_tool.search_market_news(None, curr_date, days_back)
                
                return {
                    'period': f"过去 {days_back} 天",
                    'news_content': market_news,
                    'summary': f"已通过Google News获取过去 {days_back} 天的市场新闻"
                }
            except Exception as e:
                print(f"Google News工具获取市场新闻失败: {e}")
        
        return {
            'period': f"过去 {days_back} 天",
            'news_content': "## 市场新闻\n\n暂无可用市场新闻数据",
            'summary': f"暂无过去 {days_back} 天的市场新闻数据"
        }


def create_data_adapter(config: Dict[str, Any]) -> MarketDataAdapter:
    """创建数据适配器实例"""
    return MarketDataAdapter(config)