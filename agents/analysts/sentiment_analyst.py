"""
情绪分析师Agent
负责分析社交媒体情绪、市场情绪指标、投资者情绪等
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List
from datetime import date, datetime
import json
import time

from core.specialized_agents import AnalystAgent
from core.llm_client import LLMClient
from core.state_manager import AgentRole, AnalysisReport
from tools.tool_wrappers import google_search as unified_google_search
from tools.result_emitters import emit_sentiment_analysis
from utils.logger import get_logger

logger = get_logger()


class SentimentAnalyst(AnalystAgent):
    """情绪分析师"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [unified_google_search, emit_sentiment_analysis]
        
        super().__init__(
            role=AgentRole.SENTIMENT_ANALYST,
            name="情绪分析师",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        logger.info(f"情绪分析师初始化完成，可用工具: {len(tools)}个")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理情绪分析请求
        
        Args:
            context: 包含股票代码、社交媒体数据、情绪指标等信息
            
        Returns:
            分析结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_process)
    
    def _do_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的处理逻辑（内部方法）
        
        Args:
            context: 包含股票代码、社交媒体数据、情绪指标等信息
            
        Returns:
            分析结果
        """
        start_time = time.time()
        symbol = context.get('symbol', '')
        logger.info(f"开始情绪分析流程 - 股票代码: {symbol}")
        self.log_action("开始情绪分析", {'symbol': symbol})
        
        # 检查并创建会话（如果没有活跃会话）
        if not self.state_manager.current_session:
            logger.info("没有活跃会话，创建新的交易会话")
            session_id = self.state_manager.start_session(symbol)
            logger.info(f"创建会话成功: {session_id}")
        
        # 构建分析提示，LLM会自动知道有哪些工具可用
        analysis_prompt = f"""
作为专业的情绪分析师，请深入分析与股票 {symbol} 相关的市场情绪和投资者情绪。

请按以下步骤进行分析：

第一步：获取相关新闻和数据
- 使用google_search工具搜索与 {symbol} 相关的情绪、投资者情绪、市场情绪相关的新闻
- 可以搜索关键词如："{symbol} investor sentiment"、"{symbol} market mood"、"{symbol} social media"、"{symbol} Reddit discussion"等
- 也可以搜索宏观市场情绪相关的新闻，如"VIX fear index"、"market sentiment"、"investor confidence"等

第二步：基于获取的新闻和数据进行深入分析

请从以下角度进行情绪分析：

1. 社交媒体情绪分析
   - 社交平台（Reddit、Twitter、StockTwits等）讨论热度和情绪倾向
   - 散户投资者的情绪表现和关注焦点
   - 热门话题和讨论内容分析
   - 情绪变化趋势和异常波动

2. 市场情绪指标分析
   - VIX恐慌指数和波动率指标
   - 看涨/看跌期权比例（Put/Call Ratio）
   - 投资者情绪调查结果
   - 资金流向和机构行为
   - 融资融券数据

3. 投资者行为分析
   - 机构投资者持仓变化
   - 内部人士交易行为
   - 分析师评级和目标价变化
   - 大股东和董事的买卖行为

4. 情绪极值和拐点识别
   - 极端乐观或悲观情绪信号
   - 情绪反转的早期迹象
   - 群体心理和羊群效应
   - 逆向投资机会识别

5. 情绪风险评估
   - 情绪泡沫或崩盘风险
   - 市场情绪对股价的影响程度
   - 情绪波动的持续性预测
   - 情绪驱动的交易风险

请使用 emit_sentiment_analysis 工具提供最终的情绪分析结果。
"""
        
        try:
            logger.info("开始执行情绪分析工具流程")
            # 使用工具调用进行情绪分析，直接返回工具结果
            result = self.process_with_tools_return_result(
                analysis_prompt, 
                'emit_sentiment_analysis'
            )
            logger.info("工具流程执行完成，获得情绪分析结果")
            
            logger.info(f"情绪分析结果解析完成 - 情绪: {result.get('sentiment_level', 'N/A')}, 置信度: {result.get('confidence_score', 'N/A')}")
            
            # 创建分析报告
            logger.debug("创建情绪分析报告")
            report = AnalysisReport(
                analyst_role=self.role,
                symbol=symbol,
                analysis_date=date.today(),
                key_findings=result.get('key_findings', []),
                recommendation=self._sentiment_to_recommendation(result.get('sentiment_level', '中性')),
                confidence_score=result.get('confidence_score', 0.5),
                risk_factors=result.get('risk_factors', []),
                time_horizon=result.get('time_frame', {}),  # 使用 time_frame 匹配结果结构
                impact_magnitude=result.get('sentiment_magnitude', 0.5),
                supporting_data={
                    'sentiment_score': result.get('sentiment_score', 0.5),
                    'sentiment_level': result.get('sentiment_level', '中性'),
                    'turning_points': result.get('turning_points', []),
                    'contrarian_signals': result.get('contrarian_signals', []),
                    'market_mood_indicators': result.get('market_mood_indicators', {})
                },
                detailed_analysis=result.get('supporting_evidence', ''),
                processing_time=time.time() - start_time
            )
            
            # 添加到状态管理器
            logger.debug("将分析报告添加到状态管理器")
            try:
                self.state_manager.add_analysis_report(report)
                logger.info("分析报告成功添加到状态管理器")
            except ValueError as e:
                logger.warning(f"无法添加到状态管理器: {str(e)}，但分析结果仍然有效")
            
            processing_time = time.time() - start_time
            logger.info(f"情绪分析流程完成 - 处理时间: {processing_time:.2f}秒")
            
            self.log_action("情绪分析完成", {
                'sentiment_level': result.get('sentiment_level'),
                'sentiment_score': result.get('sentiment_score'),
                'confidence': result.get('confidence_score'),
                'processing_time': processing_time,
                'key_findings_count': len(result.get('key_findings', []))
            })
            
            return {
                'success': True,
                'report': report,
                'analysis_result': result,
                'processing_time': processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"情绪分析流程失败 - 错误: {str(e)}, 处理时间: {processing_time:.2f}秒")
            self.log_action("情绪分析失败", {
                'error': str(e),
                'processing_time': processing_time,
                'symbol': symbol
            })
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    
    def _sentiment_to_recommendation(self, sentiment_level: str) -> str:
        """将情绪水平转换为投资建议"""
        sentiment_mapping = {
            '极度乐观': 'SELL',  # 逆向投资
            '乐观': 'HOLD',
            '中性': 'HOLD',
            '悲观': 'HOLD',
            '极度悲观': 'BUY'  # 逆向投资
        }
        return sentiment_mapping.get(sentiment_level, 'HOLD')
    
def create_sentiment_analyst(llm_client: LLMClient, **kwargs) -> SentimentAnalyst:
    """创建情绪分析师实例"""
    logger.info("创建情绪分析师实例")
    try:
        analyst = SentimentAnalyst(llm_client, **kwargs)
        logger.info("情绪分析师实例创建成功")
        return analyst
    except Exception as e:
        logger.error(f"情绪分析师实例创建失败: {str(e)}")
        raise

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from tools.yfinance_tool import YFinanceTool
    
    symbol = "AAPL"
    
    logger.info(f"开始测试情绪分析师 - 股票代码: {symbol}")
    
    yfinance_tool = YFinanceTool()
    market_data = yfinance_tool.get_market_summary(symbol)
    logger.info(f"获取市场数据完成: {symbol}")

    llm_client = LLMClient(provider='deepseek')
    sentiment_analyst = create_sentiment_analyst(llm_client=llm_client)
    result = sentiment_analyst.process(market_data)
    
    logger.info(f"情绪分析测试完成 - 成功: {result.get('success', False)}")
    logger.debug(f"分析结果: {json.dumps(result.get('analysis_result', {}), ensure_ascii=False, indent=2)}")