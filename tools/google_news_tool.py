"""
Google News 工具实现
从原有 tradingagents 系统迁移的 Google News 数据获取功能
现在集成RSS作为备用数据源
"""
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import random
from typing import List, Dict, Any
import feedparser
import urllib.parse
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_result,
    RetryError,
)


def is_rate_limited(response):
    """检查响应是否表示速率限制 (状态代码 429)"""
    return response.status_code == 429


@retry(
    retry=(retry_if_result(is_rate_limited)),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
)
def make_request(url: str, headers: Dict[str, str]):
    """使用重试逻辑发出请求以应对速率限制"""
    # 在每个请求之前随机延迟以避免检测
    time.sleep(random.uniform(2, 6))
    response = requests.get(url, headers=headers)
    print(f"请求URL: {url}")
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 429:
        print("触发429限流，将重试")
    elif response.status_code != 200:
        print(f"异常状态码: {response.status_code}, 响应内容: {response.text[:500]}")
    return response


def get_google_news_data(query: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    抓取给定查询和日期范围的 Google 新闻搜索结果
    直接使用原始 tradingagents/dataflows/googlenews_utils.py 的实现
    
    Args:
        query: 搜索查询
        start_date: 开始日期，格式 yyyy-mm-dd 或 mm/dd/yyyy
        end_date: 结束日期，格式 yyyy-mm-dd 或 mm/dd/yyyy
        
    Returns:
        新闻结果列表
    """
    # 日期格式转换 - 原始实现
    if "-" in start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = start_date.strftime("%m/%d/%Y")
    if "-" in end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = end_date.strftime("%m/%d/%Y")

    print(f"start_date: {start_date}, end_date: {end_date}, query: {query}")    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/101.0.4951.54 Safari/537.36"
        )
    }

    news_results = []
    page = 0
    
    # 使用原始实现的无限分页逻辑
    while True:
        offset = page * 10
        url = (
            f"https://www.google.com/search?q={query}"
            f"&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}"
            f"&tbm=nws&start={offset}"
        )

        try:
            response = make_request(url, headers)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # 调试信息：检查页面内容
            print(f"页面标题: {soup.title.string if soup.title else 'No title'}")
            results_on_page = soup.select("div.SoaBEf")
            print(f"找到的结果数量: {len(results_on_page)}")
            
            # 如果没有找到结果，检查是否有其他指示器
            if not results_on_page:
                # 检查是否有CAPTCHA或其他阻止信息
                captcha_check = soup.find("div", {"id": "captcha-form"})
                if captcha_check:
                    print("检测到CAPTCHA，Google可能识别为机器人")
                
                # 检查是否有"没有结果"的提示
                no_results = soup.find("div", string=lambda text: "没有找到" in text if text else False)
                if no_results:
                    print("Google返回：没有找到相关结果")
                
                # 打印部分页面内容用于调试
                print(f"页面部分内容: {soup.get_text()[:1000]}")
                break  # 没有找到更多结果

            for el in results_on_page:
                try:
                    link = el.find("a")["href"]
                    title = el.select_one("div.MBeuO").get_text()
                    snippet = el.select_one(".GI74Re").get_text()
                    date = el.select_one(".LfVVr").get_text()
                    source = el.select_one(".NUnG9d span").get_text()
                    
                    news_results.append({
                        "link": link,
                        "title": title,
                        "snippet": snippet,
                        "date": date,
                        "source": source,
                    })
                except Exception as e:
                    print(f"处理结果时出错: {e}")
                    # 如果找不到某个字段，跳过该结果
                    continue

            # 检查"下一页"链接（分页）
            next_link = soup.find("a", id="pnnext")
            if not next_link:
                break

            page += 1

        except RetryError as e:
            print(f"重试失败，最后一次尝试的异常: {e.last_attempt.exception()}")
            print(f"重试历史: {e.last_attempt}")
            break
        except Exception as e:
            print(f"其他异常: {type(e).__name__}: {e}")
            break

    return news_results


def get_rss_news_data(query: str, look_back_days: int = 7) -> List[Dict[str, Any]]:
    """
    通过RSS获取Google新闻数据 (无限流)
    
    Args:
        query: 搜索查询
        look_back_days: 回看天数
        
    Returns:
        新闻结果列表
    """
    print(f"RSS搜索: {query}")
    
    # URL编码查询
    encoded_query = urllib.parse.quote(query)
    
    # Google News RSS URL
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        print(f"RSS URL: {rss_url}")
        
        # 解析RSS Feed
        feed = feedparser.parse(rss_url)
        
        if feed.bozo:
            print(f"RSS解析警告: {feed.bozo_exception}")
        
        news_results = []
        cutoff_date = datetime.now() - timedelta(days=look_back_days)
        
        for entry in feed.entries:
            try:
                # 解析日期
                published_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                
                # 只保留指定天数内的新闻
                if published_date < cutoff_date:
                    continue
                
                # 提取源名称 (通常在标题中)
                source = "Google News"
                if hasattr(entry, 'source') and entry.source:
                    source = entry.source.get('title', 'Unknown')
                
                # 构建新闻项
                news_item = {
                    "link": entry.link,
                    "title": entry.title,
                    "snippet": entry.summary if hasattr(entry, 'summary') else entry.title,
                    "date": published_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "source": source,
                    "published": published_date
                }
                
                news_results.append(news_item)
                
            except Exception as e:
                print(f"解析RSS条目时出错: {e}")
                continue
        
        # 按日期排序 (最新的在前面)
        news_results.sort(key=lambda x: x['published'], reverse=True)
        
        print(f"RSS获取到 {len(news_results)} 条新闻")
        return news_results
        
    except Exception as e:
        print(f"RSS获取失败: {e}")
        return []


def get_yahoo_finance_news(symbol: str) -> List[Dict[str, Any]]:
    """
    获取Yahoo Finance新闻 (备用数据源)
    
    Args:
        symbol: 股票代码
        
    Returns:
        新闻结果列表
    """
    print(f"Yahoo Finance新闻搜索: {symbol}")
    
    try:
        # Yahoo Finance新闻URL
        url = f"https://finance.yahoo.com/quote/{symbol}/news"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Yahoo Finance响应状态码: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # 查找新闻条目 (Yahoo Finance的结构)
        news_items = soup.find_all("div", {"class": "Ov(h) Pend(44px) Pstart(25px)"})
        
        news_results = []
        
        for item in news_items[:10]:  # 限制前10条
            try:
                title_elem = item.find("a")
                if not title_elem:
                    continue
                    
                title = title_elem.get_text().strip()
                link = title_elem.get("href", "")
                
                # 补全链接
                if link.startswith("/"):
                    link = "https://finance.yahoo.com" + link
                
                news_item = {
                    "link": link,
                    "title": title,
                    "snippet": title,  # Yahoo Finance通常标题就是摘要
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "Yahoo Finance",
                    "published": datetime.now()
                }
                
                news_results.append(news_item)
                
            except Exception as e:
                print(f"解析Yahoo Finance条目时出错: {e}")
                continue
        
        print(f"Yahoo Finance获取到 {len(news_results)} 条新闻")
        return news_results
        
    except Exception as e:
        print(f"Yahoo Finance获取失败: {e}")
        return []


class GoogleNewsTool:
    """Google News 工具类"""
    
    def __init__(self):
        self.name = "google_news"
        self.description = "获取Google新闻数据"
    
    def get_news(
        self, 
        query: str, 
        curr_date: str, 
        look_back_days: int = 7
    ) -> str:
        """
        获取新闻数据 (RSS优先，Yahoo Finance备用，Google搜索兜底)
        
        Args:
            query: 搜索查询
            curr_date: 当前日期 (yyyy-mm-dd格式)
            look_back_days: 回看天数
            
        Returns:
            格式化的新闻字符串
        """
        print(f"开始获取新闻: {query}")
        
        # 尝试RSS获取
        try:
            print("尝试RSS获取...")
            news_results = get_rss_news_data(query, look_back_days)
            if news_results:
                return self._format_news_results(news_results, query, "RSS", curr_date, look_back_days)
        except Exception as e:
            print(f"RSS获取失败: {e}")
        
        # 如果查询包含股票代码，尝试Yahoo Finance
        if any(char.isupper() for char in query.replace("+", " ")) and len(query.replace("+", "").replace(" ", "")) <= 5:
            try:
                print("尝试Yahoo Finance获取...")
                # 提取可能的股票代码
                potential_symbol = query.replace("+", " ").split()[0].upper()
                news_results = get_yahoo_finance_news(potential_symbol)
                if news_results:
                    return self._format_news_results(news_results, query, "Yahoo Finance", curr_date, look_back_days)
            except Exception as e:
                print(f"Yahoo Finance获取失败: {e}")
        
        # 最后尝试Google搜索 (原始方法)
        try:
            print("尝试Google搜索获取...")
            query_with_plus = query.replace(" ", "+")
            start_date = datetime.strptime(curr_date, "%Y-%m-%d")
            before = start_date - timedelta(days=look_back_days)
            before_str = before.strftime("%Y-%m-%d")
            
            news_results = get_google_news_data(query_with_plus, before_str, curr_date)
            if news_results:
                return self._format_news_results(news_results, query, "Google News", curr_date, look_back_days)
        except Exception as e:
            print(f"Google搜索获取失败: {e}")
        
        # 如果所有方法都失败
        return f"## {query} 新闻\n\n无法获取相关新闻，所有数据源都不可用"
    
    def _format_news_results(self, news_results: List[Dict[str, Any]], query: str, source: str, curr_date: str, look_back_days: int) -> str:
        """格式化新闻结果"""
        if not news_results:
            return f"## {query} 新闻\n\n未找到相关新闻"
        
        # 格式化新闻结果
        news_str = ""
        for news in news_results[:10]:  # 限制为前10条新闻
            news_str += (
                f"### {news['title']} (来源: {news['source']})\n\n"
                f"{news['snippet']}\n\n"
                f"日期: {news['date']}\n"
                f"链接: {news['link']}\n\n"
                "---\n\n"
            )
        
        summary = f"共获取到 {len(news_results)} 条新闻，显示前10条 (数据源: {source})"
        
        return f"## {query} 新闻 (最近{look_back_days}天)\n\n{summary}\n\n{news_str}"
    
    def get_stock_news(
        self, 
        symbol: str, 
        queries: List[str], 
        curr_date: str, 
        look_back_days: int = 7
    ) -> str:
        """
        获取特定股票的新闻
        
        Args:
            queries: 搜索查询列表
            curr_date: 当前日期
            look_back_days: 回看天数
            
        Returns:
            格式化的股票新闻字符串
        """
        
        all_news = []
        for query in queries:
            news = self.get_news(f"{symbol}+{query}", curr_date, look_back_days)
            if "未找到相关新闻" not in news and "出错" not in news:
                all_news.append(news)
        
        if not all_news:
            return f"## {symbol} 股票新闻\n\n未找到相关新闻"
        
        # 合并所有新闻
        combined_news = f"## {symbol} 股票新闻综合报告\n\n"
        for i, news in enumerate(all_news, 1):
            combined_news += f"### 搜索结果 {i}\n{news}\n\n"
        
        return combined_news
    
    def search_market_news(
        self, 
        topics: List[str] = None,
        curr_date: str = datetime.now().strftime("%Y-%m-%d"), 
        look_back_days: int = 7,
    ) -> str:
        """
        搜索市场相关新闻
        
        Args:
            curr_date: 当前日期
            look_back_days: 回看天数
            topics: 搜索主题列表
            
        Returns:
            格式化的市场新闻字符串
        """
        if topics is None:
            topics = [
                "stock market",
                "economy news",
                "federal reserve",
                "inflation",
                "GDP"
            ]
        
        market_news = []
        for topic in topics:
            news = self.get_news(topic, curr_date, look_back_days)
            if "未找到相关新闻" not in news and "出错" not in news:
                market_news.append((topic, news))
        
        if not market_news:
            return "## 市场新闻\n\n未找到相关新闻"
        
        # 格式化市场新闻
        combined_news = "## 市场新闻综合报告\n\n"
        for topic, news in market_news:
            combined_news += f"### {topic.title()} 相关新闻\n{news}\n\n"
        
        return combined_news


def create_google_news_tool() -> GoogleNewsTool:
    """创建Google News工具实例"""
    return GoogleNewsTool()


# 便捷函数
def get_google_news(
    query: str, 
    curr_date: str, 
    look_back_days: int = 7
) -> str:
    """便捷函数：获取Google新闻"""
    tool = create_google_news_tool()
    return tool.get_news(query, curr_date, look_back_days)


def get_stock_news(
    symbol: str, 
    queries: List[str],
    curr_date: str = datetime.now().strftime("%Y-%m-%d"), 
    look_back_days: int = 7
) -> str:
    """便捷函数：获取股票新闻"""
    tool = create_google_news_tool()
    return tool.get_stock_news(symbol, queries, curr_date, look_back_days)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print("get_stock_news:")
    print(get_stock_news("AAPL", ["AAPL"]))