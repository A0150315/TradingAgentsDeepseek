"""
YFinance 工具实现
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
from functools import wraps
from utils.logger import logger

DEFAULT_DAYS_BACK = 365

# 尝试导入ta-lib，如果不可用则使用pandas实现
try:
    import talib
    TALIB_AVAILABLE = True
    logger.info("TA-Lib可用，将使用专业技术分析库")
except ImportError:
    TALIB_AVAILABLE = False
    logger.warning("TA-Lib不可用，将使用pandas实现技术指标计算")
    logger.info("建议安装TA-Lib以获得更高精度: pip install TA-Lib")


def init_ticker(func):
    """装饰器：初始化 yf.Ticker 并将其传递给函数"""
    @wraps(func)
    def wrapper(self, symbol: str, *args, **kwargs):
        ticker = yf.Ticker(symbol)
        return func(self, ticker, *args, **kwargs)
    return wrapper


class YFinanceTool:
    """YFinance 工具类"""
    
    def __init__(self):
        self.name = "yfinance"
        self.description = "获取Yahoo Finance股票数据"
    
    def get_stock_data(
        self, 
        symbol: str,
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """
        获取指定股票代码的价格数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-mm-dd)
            end_date: 结束日期 (YYYY-mm-dd)
            
        Returns:
            股票价格数据DataFrame
        """
        try:
            ticker = yf.Ticker(symbol)
            # 给结束日期加一天，使日期范围包含结束日期
            end_date_dt = pd.to_datetime(end_date) + pd.DateOffset(days=1)
            end_date = end_date_dt.strftime("%Y-%m-%d")
            stock_data = ticker.history(start=start_date, end=end_date)
            return stock_data
            
        except Exception as e:
            logger.error(f"获取股票数据失败 [{symbol}]: {e}")
            return pd.DataFrame()
    
    @init_ticker
    def get_stock_info(self, symbol: yf.Ticker) -> Dict[str, Any]:
        """
        获取并返回最新股票信息
        
        Args:
            symbol: yf.Ticker对象
            
        Returns:
            股票信息字典
        """
        try:
            stock_info = symbol.info
            return stock_info
        except Exception as e:
            logger.error(f"获取股票信息失败 [{symbol.ticker}]: {e}")
            return {}
    
    @init_ticker
    def get_company_info(self, symbol: yf.Ticker) -> Dict[str, Any]:
        """
        获取并返回公司信息
        
        Args:
            symbol: yf.Ticker对象
            
        Returns:
            公司信息字典
        """
        try:
            info = symbol.info
            company_info = {
                "Company Name": info.get("shortName", "N/A"),
                "Long Name": info.get("longName", "N/A"),
                "Industry": info.get("industry", "N/A"),
                "Sector": info.get("sector", "N/A"),
                "Country": info.get("country", "N/A"),
                "Website": info.get("website", "N/A"),
                "Market Cap": info.get("marketCap", "N/A"),
                "Enterprise Value": info.get("enterpriseValue", "N/A"),
                "P/E Ratio": info.get("trailingPE", "N/A"),
                "Forward P/E": info.get("forwardPE", "N/A"),
                "PEG Ratio": info.get("trailingPegRatio", "N/A"),
                "Price to Sales": info.get("priceToSalesTrailing12Months", "N/A"),
                "Price to Book": info.get("priceToBook", "N/A"),
                "Enterprise to Revenue": info.get("enterpriseToRevenue", "N/A"),
                "Enterprise to EBITDA": info.get("enterpriseToEbitda", "N/A"),
                "Beta": info.get("beta", "N/A"),
                "ROE": info.get("returnOnEquity", "N/A"),
                "ROA": info.get("returnOnAssets", "N/A"),
                "Profit Margins": info.get("profitMargins", "N/A"),
                "Debt to Equity": info.get("debtToEquity", "N/A"),
                "Current Ratio": info.get("currentRatio", "N/A"),
                "Quick Ratio": info.get("quickRatio", "N/A")
            }
            return company_info
        except Exception as e:
            logger.error(f"获取公司信息失败 [{symbol.ticker}]: {e}")
            return {}
    
    @init_ticker
    def get_financial_data(self, symbol: yf.Ticker) -> Dict[str, pd.DataFrame]:
        """
        获取财务数据（收入表、资产负债表、现金流量表）
        
        Args:
            symbol: yf.Ticker对象·
            
        Returns:
            包含财务数据的字典
        """
        try:
            financial_data = {
                "income_statement": symbol.financials,
                "balance_sheet": symbol.balance_sheet,
                "cash_flow": symbol.cashflow,
                "quarterly_income": symbol.quarterly_financials,
                "quarterly_balance_sheet": symbol.quarterly_balance_sheet,
                "quarterly_cash_flow": symbol.quarterly_cashflow
            }
            return financial_data
        except Exception as e:
            logger.error(f"获取财务数据失败 [{symbol.ticker}]: {e}")
            return {}
    
    @init_ticker
    def get_stock_dividends(self, symbol: yf.Ticker) -> pd.DataFrame:
        """
        获取股息数据
        
        Args:
            symbol: yf.Ticker对象
            
        Returns:
            股息数据DataFrame
        """
        try:
            dividends = symbol.dividends
            return dividends
        except Exception as e:
            logger.error(f"获取股息数据失败 [{symbol.ticker}]: {e}")
            return pd.DataFrame()
    
    @init_ticker
    def get_analyst_recommendations(self, symbol: yf.Ticker) -> Tuple[Optional[str], int]:
        """
        获取最新分析师推荐并返回最常见的推荐及其数量
        
        Args:
            symbol: yf.Ticker对象
            
        Returns:
            (最常见推荐, 票数) 的元组
        """
        try:
            recommendations = symbol.recommendations
            if recommendations is None or recommendations.empty:
                return None, 0
            
            # 获取最新推荐数据
            latest_rec = recommendations.iloc[-1]
            
            # 找到票数最多的推荐
            rec_cols = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']
            available_cols = [col for col in rec_cols if col in latest_rec.index]
            
            if not available_cols:
                return None, 0
            
            max_votes = 0
            majority_rec = None
            
            for col in available_cols:
                votes = latest_rec[col]
                if votes > max_votes:
                    max_votes = votes
                    majority_rec = col
            
            return majority_rec, int(max_votes)
            
        except Exception as e:
            logger.error(f"获取分析师推荐失败 [{symbol.ticker}]: {e}")
            return None, 0
    
    def get_market_summary(self, symbol: str, days_back: int = DEFAULT_DAYS_BACK) -> Dict[str, Any]:
        """
        获取市场数据摘要
        
        Args:
            symbol: 股票代码
            days_back: 回看天数
            
        Returns:
            市场摘要数据
        """
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            # 获取股票数据
            stock_data = self.get_stock_data(symbol, start_date, end_date)
            
            if stock_data.empty:
                return {
                    'symbol': symbol,
                    'error': '无法获取数据',
                    'summary': f'无法获取 {symbol} 的市场数据'
                }
            
            # 获取公司信息
            company_info = self.get_company_info(symbol)
            
            # 获取分析师推荐
            analyst_rec, rec_count = self.get_analyst_recommendations(symbol)
            
            # 从LLM获取技术分析
            technical_analysis = self.get_technical(stock_data)

            # 提取价格信息
            current_price = stock_data['Close'].iloc[-1]
            prev_price = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            # 构建摘要
            summary = {
                'symbol': symbol,
                'company_name': company_info.get('Company Name', 'N/A'),
                'sector': company_info.get('Sector', 'N/A'),
                'industry': company_info.get('Industry', 'N/A'),
                'current_price': round(current_price, 2),
                'price_change': round(price_change, 2),
                'price_change_pct': round(price_change_pct, 2),
                'volume': int(stock_data['Volume'].iloc[-1]),
                'avg_volume': int(stock_data['Volume'].mean()),
                'high_52w': round(stock_data['High'].max(), 2),
                'low_52w': round(stock_data['Low'].min(), 2),
                'market_cap': company_info.get('Market Cap', 'N/A'),
                'pe_ratio': company_info.get('P/E Ratio', 'N/A'),
                'analyst_recommendation': analyst_rec,
                'analyst_votes': rec_count,
                'technical_analysis': technical_analysis,
                'data_period': f"{start_date} to {end_date}",
                'summary_text': self._generate_summary_text(
                    symbol, current_price, price_change_pct, 
                    company_info, analyst_rec, technical_analysis
                )
            }
            
            return summary
            
        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e),
                'summary': f'获取 {symbol} 市场摘要时出错: {str(e)}'
            }

    def get_technical(self, stock_data: pd.DataFrame) -> Dict[str, Any]:
        """计算技术指标并使用LLM进行分析"""
        
        try:
            # 优先使用ta-lib，如果不可用则使用pandas
            if TALIB_AVAILABLE:
                logger.debug("使用TA-Lib专业库计算技术指标")
                indicators = self._calculate_technical_indicators_talib(stock_data)
            else:
                logger.debug("使用pandas实现计算技术指标")
                indicators = self._calculate_technical_indicators_pandas(stock_data)
                
            return indicators
            
            # 将指标数据传递给LLM进行分析
            # analysis = self._get_llm_analysis(indicators, stock_data)
            
            # 合并数据和分析
            # result = {**indicators, **analysis}
            # return result
            
        except Exception as e:
            logger.error(f"技术分析计算失败: {e}")
            return {"error": "无法计算技术分析"}
    
    def _calculate_technical_indicators_talib(self, stock_data: pd.DataFrame) -> Dict[str, float]:
        """使用TA-Lib计算技术指标（推荐）"""
        if stock_data.empty:
            return {}
        
        # 提取OHLCV数据 - TA-Lib要求double类型的numpy数组
        high = stock_data['High'].astype(float).values
        low = stock_data['Low'].astype(float).values  
        close = stock_data['Close'].astype(float).values
        volume = stock_data['Volume'].astype(float).values
        
        # 检查数据质量
        nan_counts = {
            'High': pd.isna(high).sum(),
            'Low': pd.isna(low).sum(), 
            'Close': pd.isna(close).sum(),
            'Volume': pd.isna(volume).sum()
        }
        
        # 如果有太多NaN值，给出警告
        if any(count > len(stock_data) * 0.1 for count in nan_counts.values()):
            logger.warning(f"数据质量问题：存在较多NaN值 {nan_counts}，可能影响计算精度")
        
        logger.debug(f"开始TA-Lib技术指标计算，数据行数: {len(stock_data)}")
        
        try:
            # 移动平均线
            sma_50 = talib.SMA(close, timeperiod=50)[-1] if len(close) >= 50 else None
            sma_200 = talib.SMA(close, timeperiod=200)[-1] if len(close) >= 200 else None
            ema_10 = talib.EMA(close, timeperiod=10)[-1] if len(close) >= 10 else None
            
            # MACD
            if len(close) >= 35:
                macd, macd_signal, macd_histogram = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
                macd_val = macd[-1] if not pd.isna(macd[-1]) else None
                macds_val = macd_signal[-1] if not pd.isna(macd_signal[-1]) else None
                macdh_val = macd_histogram[-1] if not pd.isna(macd_histogram[-1]) else None
            else:
                macd_val = macds_val = macdh_val = None
            
            # RSI
            rsi = talib.RSI(close, timeperiod=14)[-1] if len(close) >= 14 else None
            
            # 布林带
            if len(close) >= 20:
                boll_upper, boll_middle, boll_lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
                boll_ub = boll_upper[-1] if not pd.isna(boll_upper[-1]) else None
                boll = boll_middle[-1] if not pd.isna(boll_middle[-1]) else None
                boll_lb = boll_lower[-1] if not pd.isna(boll_lower[-1]) else None
            else:
                boll_ub = boll = boll_lb = None
            
            # ATR
            atr = talib.ATR(high, low, close, timeperiod=14)[-1] if len(close) >= 15 else None
            
            # VWMA (Volume Weighted Moving Average) - TA-Lib没有直接函数，需要手动计算
            if len(close) >= 20:
                try:
                    # 手动计算VWMA: sum(price * volume) / sum(volume) for last 20 periods
                    vwma_period = 20
                    recent_close = close[-vwma_period:]
                    recent_volume = volume[-vwma_period:]
                    
                    price_volume = recent_close * recent_volume
                    volume_sum = recent_volume.sum()
                    
                    if volume_sum > 0:  # 避免除零错误
                        vwma = price_volume.sum() / volume_sum
                        vwma = round(float(vwma), 2) if not pd.isna(vwma) else None
                    else:
                        vwma = None
                except Exception as e:
                    logger.error(f"VWMA计算失败: {e}")
                    vwma = None
            else:
                vwma = None
            
            # MFI
            mfi = talib.MFI(high, low, close, volume, timeperiod=14)[-1] if len(close) >= 15 else None
            
            # === 量能指标 ===
            # OBV (On Balance Volume) - 能量潮指标
            obv = talib.OBV(close, volume)[-1] if len(close) >= 10 else None
            
            # A/D Line (Accumulation/Distribution Line) - 累积/派发线
            ad = talib.AD(high, low, close, volume)[-1] if len(close) >= 10 else None
            
            # === 超买超卖指标 ===
            # Stochastic %K和%D
            if len(close) >= 14:
                slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
                stoch_k = slowk[-1] if not pd.isna(slowk[-1]) else None
                stoch_d = slowd[-1] if not pd.isna(slowd[-1]) else None
            else:
                stoch_k = stoch_d = None
                
            # Williams %R
            willr = talib.WILLR(high, low, close, timeperiod=14)[-1] if len(close) >= 15 else None
            
            # CCI (Commodity Channel Index)
            cci = talib.CCI(high, low, close, timeperiod=14)[-1] if len(close) >= 15 else None
            
            # === 趋势指标 ===
            # ROC (Rate of Change) - 变化率
            roc = talib.ROC(close, timeperiod=10)[-1] if len(close) >= 11 else None
            
            # TRIX - 三重指数平滑平均 (需要更多数据因为是三重平滑)
            trix = talib.TRIX(close, timeperiod=14)[-1] if len(close) >= 45 else None
            
            # 计算完成，统计可用指标数量
            available_count = len([v for v in [sma_50, sma_200, ema_10, macd_val, rsi, obv, stoch_k, willr] if v is not None])
            logger.debug(f"TA-Lib技术指标计算完成，{available_count}个指标可用")
            
            return {
                # === 基础趋势指标 ===
                "close_50_sma": round(sma_50, 2) if sma_50 and not pd.isna(sma_50) else f"需要至少50天数据(当前{len(close)}天)",
                "close_200_sma": round(sma_200, 2) if sma_200 and not pd.isna(sma_200) else f"需要至少200天数据(当前{len(close)}天)",
                "close_10_ema": round(ema_10, 2) if ema_10 and not pd.isna(ema_10) else f"需要至少10天数据(当前{len(close)}天)",
                
                # === MACD系列 ===
                "macd": round(macd_val, 4) if macd_val and not pd.isna(macd_val) else f"需要至少35天数据(当前{len(close)}天)",
                "macds": round(macds_val, 4) if macds_val and not pd.isna(macds_val) else f"需要至少35天数据(当前{len(close)}天)",
                "macdh": round(macdh_val, 4) if macdh_val and not pd.isna(macdh_val) else f"需要至少35天数据(当前{len(close)}天)",
                
                # === 动量指标 ===
                "rsi": round(rsi, 2) if rsi and not pd.isna(rsi) else f"需要至少14天数据(当前{len(close)}天)",
                "mfi": round(mfi, 2) if mfi and not pd.isna(mfi) else f"需要至少15天数据(当前{len(close)}天)",
                
                # === 波动率指标 ===
                "boll": round(boll, 2) if boll and not pd.isna(boll) else f"需要至少20天数据(当前{len(close)}天)",
                "boll_ub": round(boll_ub, 2) if boll_ub and not pd.isna(boll_ub) else f"需要至少20天数据(当前{len(close)}天)",
                "boll_lb": round(boll_lb, 2) if boll_lb and not pd.isna(boll_lb) else f"需要至少20天数据(当前{len(close)}天)",
                "atr": round(atr, 2) if atr and not pd.isna(atr) else f"需要至少15天数据(当前{len(close)}天)",
                
                # === 成交量指标 ===
                "vwma": round(vwma, 2) if vwma and not pd.isna(vwma) else f"需要至少20天数据(当前{len(close)}天)",
                "obv": round(obv, 0) if obv and not pd.isna(obv) else f"需要至少10天数据(当前{len(close)}天)",
                "ad": round(ad, 0) if ad and not pd.isna(ad) else f"需要至少10天数据(当前{len(close)}天)",
                
                # === 超买超卖指标 ===
                "stoch_k": round(stoch_k, 2) if stoch_k and not pd.isna(stoch_k) else f"需要至少14天数据(当前{len(close)}天)",
                "stoch_d": round(stoch_d, 2) if stoch_d and not pd.isna(stoch_d) else f"需要至少14天数据(当前{len(close)}天)",
                "willr": round(willr, 2) if willr and not pd.isna(willr) else f"需要至少15天数据(当前{len(close)}天)",
                "cci": round(cci, 2) if cci and not pd.isna(cci) else f"需要至少15天数据(当前{len(close)}天)",
                
                # === 趋势强度指标 ===
                "roc": round(roc, 4) if roc and not pd.isna(roc) else f"需要至少11天数据(当前{len(close)}天)",
                "trix": round(trix, 6) if trix and not pd.isna(trix) else f"需要至少45天数据(当前{len(close)}天)"
            }
        
        except Exception as e:
            logger.error(f"TA-Lib技术指标计算失败: {e}")
            logger.info("回退使用pandas实现技术指标计算")
            # 回退到pandas实现
            return self._calculate_technical_indicators_pandas(stock_data)
    
    def _calculate_technical_indicators_pandas(self, stock_data: pd.DataFrame) -> Dict[str, float]:
        """使用pandas计算技术指标（备用方案）"""
        if stock_data.empty:
            return {}
        
        close_prices = stock_data['Close']
        high_prices = stock_data['High']
        low_prices = stock_data['Low']
        volume = stock_data['Volume']
        
        # 计算移动平均线
        sma_50 = close_prices.rolling(window=50).mean().iloc[-1] if len(close_prices) >= 50 else None
        sma_200 = close_prices.rolling(window=200).mean().iloc[-1] if len(close_prices) >= 200 else None
        ema_10 = close_prices.ewm(span=10).mean().iloc[-1] if len(close_prices) >= 10 else None
        
        # 计算MACD
        ema_12 = close_prices.ewm(span=12).mean()
        ema_26 = close_prices.ewm(span=26).mean()
        macd_line = ema_12 - ema_26
        macd_signal = macd_line.ewm(span=9).mean()
        macd_histogram = macd_line - macd_signal
        
        # 计算RSI
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 计算布林带
        sma_20 = close_prices.rolling(window=20).mean()
        std_20 = close_prices.rolling(window=20).std()
        bollinger_upper = sma_20 + (std_20 * 2)
        bollinger_lower = sma_20 - (std_20 * 2)
        
        # 计算ATR
        tr1 = high_prices - low_prices
        tr2 = abs(high_prices - close_prices.shift())
        tr3 = abs(low_prices - close_prices.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean()
        
        # 计算VWMA (Volume Weighted Moving Average)
        vwma = (close_prices * volume).rolling(window=20).sum() / volume.rolling(window=20).sum()
        
        # 计算MFI (Money Flow Index)
        typical_price = (high_prices + low_prices + close_prices) / 3
        money_flow = typical_price * volume
        positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=14).sum()
        negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=14).sum()
        mfi = 100 - (100 / (1 + positive_flow / negative_flow))
        
        # 创建结果字典，包含数据状态信息
        result = {
            "close_50_sma": round(sma_50, 2) if sma_50 and not pd.isna(sma_50) else f"需要至少50天数据(当前{len(close_prices)}天)",
            "close_200_sma": round(sma_200, 2) if sma_200 and not pd.isna(sma_200) else f"需要至少200天数据(当前{len(close_prices)}天)",
            "close_10_ema": round(ema_10, 2) if ema_10 and not pd.isna(ema_10) else f"需要至少10天数据(当前{len(close_prices)}天)",
            "macd": round(macd_line.iloc[-1], 4) if len(close_prices) >= 26 and not pd.isna(macd_line.iloc[-1]) else f"需要至少26天数据(当前{len(close_prices)}天)",
            "macds": round(macd_signal.iloc[-1], 4) if len(close_prices) >= 35 and not pd.isna(macd_signal.iloc[-1]) else f"需要至少35天数据(当前{len(close_prices)}天)",
            "macdh": round(macd_histogram.iloc[-1], 4) if len(close_prices) >= 35 and not pd.isna(macd_histogram.iloc[-1]) else f"需要至少35天数据(当前{len(close_prices)}天)",
            "rsi": round(rsi.iloc[-1], 2) if len(close_prices) >= 15 and not pd.isna(rsi.iloc[-1]) else f"需要至少15天数据(当前{len(close_prices)}天)",
            "boll": round(sma_20.iloc[-1], 2) if len(close_prices) >= 20 and not pd.isna(sma_20.iloc[-1]) else f"需要至少20天数据(当前{len(close_prices)}天)",
            "boll_ub": round(bollinger_upper.iloc[-1], 2) if len(close_prices) >= 20 and not pd.isna(bollinger_upper.iloc[-1]) else f"需要至少20天数据(当前{len(close_prices)}天)",
            "boll_lb": round(bollinger_lower.iloc[-1], 2) if len(close_prices) >= 20 and not pd.isna(bollinger_lower.iloc[-1]) else f"需要至少20天数据(当前{len(close_prices)}天)",
            "atr": round(atr.iloc[-1], 2) if len(close_prices) >= 15 and not pd.isna(atr.iloc[-1]) else f"需要至少15天数据(当前{len(close_prices)}天)",
            "vwma": round(vwma.iloc[-1], 2) if len(close_prices) >= 20 and not pd.isna(vwma.iloc[-1]) else f"需要至少20天数据(当前{len(close_prices)}天)",
            "mfi": round(mfi.iloc[-1], 2) if len(close_prices) >= 15 and not pd.isna(mfi.iloc[-1]) else f"需要至少15天数据(当前{len(close_prices)}天)"
        }
        
        return result
    
    def _generate_summary_text(
        self, 
        symbol: str, 
        price: float, 
        change_pct: float,
        company_info: Dict[str, Any],
        analyst_rec: Optional[str],
        technical_analysis: Dict[str, Any]
    ) -> str:
        """生成文本摘要"""
        company_name = company_info.get('Company Name', symbol)
        sector = company_info.get('Sector', '未知')
        
        trend = "上涨" if change_pct > 0 else "下跌" if change_pct < 0 else "持平"
        
        tech_summary = technical_analysis.get('overall_trend', '技术分析不可用')
        
        analyst_info = ""
        if analyst_rec:
            rec_map = {
                'strongBuy': '强烈买入',
                'buy': '买入',
                'hold': '持有',
                'sell': '卖出',
                'strongSell': '强烈卖出'
            }
            analyst_info = f"，分析师推荐: {rec_map.get(analyst_rec, analyst_rec)}"
        
        summary = f"""
{company_name} ({symbol}) - {sector}行业
当前价格: ${price:.2f} ({trend} {abs(change_pct):.2f}%)
技术分析摘要: {tech_summary}{analyst_info}
        """.strip()
        
        return summary


def create_yfinance_tool() -> YFinanceTool:
    """创建YFinance工具实例"""
    return YFinanceTool()


# 便捷函数
def get_stock_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """便捷函数：获取股票数据"""
    tool = create_yfinance_tool()
    return tool.get_stock_data(symbol, start_date, end_date)


def get_stock_info(symbol: str) -> Dict[str, Any]:
    """便捷函数：获取股票信息"""
    tool = create_yfinance_tool()
    return tool.get_stock_info(symbol)


def get_market_summary(symbol: str, days_back: int = DEFAULT_DAYS_BACK) -> Dict[str, Any]:
    """便捷函数：获取市场摘要"""
    tool = create_yfinance_tool()
    return tool.get_market_summary(symbol, days_back)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(get_market_summary("AAPL"))