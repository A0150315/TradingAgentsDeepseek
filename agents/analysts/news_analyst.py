"""
新闻分析师Agent
负责分析新闻事件、宏观经济数据、政策变化等对股票价格的影响
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
from tools.tool_wrappers import get_stock_news_tool as unified_get_stock_news, google_search as unified_google_search
from tools.result_emitters import emit_news_analysis
from utils.logger import get_logger

logger = get_logger()


class NewsAnalyst(AnalystAgent):
    """新闻分析师"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [unified_get_stock_news, unified_google_search, emit_news_analysis]
        
        super().__init__(
            role=AgentRole.NEWS_ANALYST,
            name="新闻分析师",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        logger.info(f"新闻分析师初始化完成，可用工具: {len(tools)}个")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理新闻分析请求
        
        Args:
            context: 包含股票代码、新闻数据、经济数据等信息
            
        Returns:
            分析结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_process)
    
    def _do_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的处理逻辑（内部方法）
        
        Args:
            context: 包含股票代码、新闻数据、经济数据等信息
            
        Returns:
            分析结果
        """
        start_time = time.time()
        symbol = context.get('symbol', '')
        logger.info(f"开始新闻分析流程 - 股票代码: {symbol}")
        self.log_action("开始新闻分析", {'symbol': symbol})
        
        # 检查并创建会话（如果没有活跃会话）
        if not self.state_manager.current_session:
            logger.info("没有活跃会话，创建新的交易会话")
            session_id = self.state_manager.start_session(symbol)
            logger.info(f"创建会话成功: {session_id}")
        
        # 构建分析提示，LLM会自动知道有哪些工具可用
        analysis_prompt = f"""
作为专业的新闻分析师，请深入分析与股票 {symbol} 相关的新闻和宏观环境。

请按以下步骤进行分析：

第一步：获取最新新闻数据
- 使用工具获取 {symbol} 的相关股票新闻（包括公司公告、财务报告、行业动态等）
- 使用工具获取宏观市场和经济新闻

第二步：基于获取的新闻数据进行深入分析

请从以下角度进行新闻分析：

1. 公司层面新闻
   - 重大公司公告
   - 管理层变动
   - 业务扩展或收缩
   - 产品发布或技术突破
   - 法律诉讼或监管问题

2. 行业层面新闻
   - 行业政策变化
   - 竞争对手动态
   - 行业增长前景
   - 技术变革影响
   - 市场需求变化

3. 宏观经济分析
   - GDP增长率变化
   - 通胀率和利率政策
   - 就业市场状况
   - 消费者信心指数
   - 国际贸易环境

4. 政策影响分析
   - 货币政策变化
   - 财政政策调整
   - 监管政策更新
   - 税收政策变化
   - 国际政策影响

5. 风险评估
   - 新闻事件风险等级
   - 短期和长期影响
   - 市场反应预期
   - 不确定性因素
   - 连锁反应可能

请使用 emit_news_analysis 工具提供最终的新闻分析结果。
"""
        
        try:
            logger.info("开始执行新闻分析工具流程")
            # 使用工具调用进行新闻分析，直接返回工具结果
            result = self.process_with_tools_return_result(
                analysis_prompt, 
                'emit_news_analysis'
            )
            logger.info("工具流程执行完成，获得新闻分析结果")
            
            logger.info(f"新闻分析结果解析完成 - 影响: {result.get('news_impact', 'N/A')}, 置信度: {result.get('confidence_score', 'N/A')}")
            
            # 创建分析报告
            logger.debug("创建新闻分析报告")
            report = AnalysisReport(
                analyst_role=self.role,
                symbol=symbol,
                analysis_date=date.today(),
                key_findings=result.get('key_findings', []),
                recommendation=self._news_impact_to_recommendation(result.get('news_impact', '中性')),
                confidence_score=result.get('confidence_score', 0.5),
                risk_factors=result.get('risk_factors', []),
                time_horizon=result.get('time_frame', {}),  # 使用 time_frame 匹配结果结构
                impact_magnitude=result.get('impact_magnitude', 0.5),
                supporting_data={
                    'news_impact': result.get('news_impact', '中性'),
                    'market_reaction_prediction': result.get('market_reaction_prediction', ''),
                    'catalyst_events': result.get('catalyst_events', [])
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
            logger.info(f"新闻分析流程完成 - 处理时间: {processing_time:.2f}秒")
            
            self.log_action("新闻分析完成", {
                'news_impact': result.get('news_impact'),
                'impact_magnitude': result.get('impact_magnitude'),
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
            logger.error(f"新闻分析流程失败 - 错误: {str(e)}, 处理时间: {processing_time:.2f}秒")
            self.log_action("新闻分析失败", {
                'error': str(e),
                'processing_time': processing_time,
                'symbol': symbol
            })
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    
    def _news_impact_to_recommendation(self, news_impact: str) -> str:
        """将新闻影响转换为投资建议"""
        impact_mapping = {
            '非常利好': 'BUY',
            '利好': 'BUY',
            '中性': 'HOLD',
            '利空': 'SELL',
            '非常利空': 'SELL'
        }
        recommendation = impact_mapping.get(news_impact, 'HOLD')
        logger.debug(f"新闻影响转换: {news_impact} -> {recommendation}")
        return recommendation
    
    def analyze_company_news(self, company_news: Dict[str, Any]) -> Dict[str, Any]:
        """分析公司新闻
        
        Args:
            company_news: 公司新闻数据
            
        Returns:
            公司新闻分析结果
        """
        logger.info("开始分析公司新闻")
        company_prompt = f"""
请分析以下公司新闻：

{json.dumps(company_news, indent=2, ensure_ascii=False)}

请分析：
1. 新闻的重要性等级
2. 对公司基本面的影响
3. 对股价的短期和长期影响
4. 投资者可能的反应
5. 需要关注的后续发展

请提供详细的公司新闻分析。
"""
        
        try:
            response = self.call_llm(company_prompt)
            logger.info("公司新闻分析完成")
            return {'company_news_analysis': response}
        except Exception as e:
            logger.error(f"公司新闻分析失败: {str(e)}")
            return {'company_news_analysis': f"分析失败: {str(e)}"}
    
    def analyze_economic_indicators(self, economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析经济指标
        
        Args:
            economic_data: 经济指标数据
            
        Returns:
            经济指标分析结果
        """
        logger.info("开始分析经济指标")
        economic_prompt = f"""
请分析以下经济指标数据：

{json.dumps(economic_data, indent=2, ensure_ascii=False)}

请分析：
1. 经济增长趋势
2. 通胀压力状况
3. 就业市场健康度
4. 货币政策影响
5. 对股市的整体影响

请提供经济指标的投资含义分析。
"""
        
        try:
            response = self.call_llm(economic_prompt)
            logger.info("经济指标分析完成")
            return {'economic_analysis': response}
        except Exception as e:
            logger.error(f"经济指标分析失败: {str(e)}")
            return {'economic_analysis': f"分析失败: {str(e)}"}
    
    def analyze_policy_impact(self, policy_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """分析政策影响
        
        Args:
            policy_data: 政策数据
            symbol: 股票代码
            
        Returns:
            政策影响分析结果
        """
        logger.info(f"开始分析政策影响 - 股票: {symbol}")
        policy_prompt = f"""
请分析以下政策对股票 {symbol} 的影响：

{json.dumps(policy_data, indent=2, ensure_ascii=False)}

请分析：
1. 政策的直接影响
2. 政策的间接影响
3. 实施时间和强度
4. 行业影响差异
5. 投资机会和风险

请提供政策影响的投资分析。
"""
        
        try:
            response = self.call_llm(policy_prompt)
            logger.info(f"政策影响分析完成 - 股票: {symbol}")
            return {'policy_analysis': response}
        except Exception as e:
            logger.error(f"政策影响分析失败 - 股票: {symbol}, 错误: {str(e)}")
            return {'policy_analysis': f"分析失败: {str(e)}"}
    
    def identify_market_catalysts(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """识别市场催化剂
        
        Args:
            news_data: 新闻数据
            
        Returns:
            市场催化剂分析
        """
        logger.info("开始识别市场催化剂")
        catalyst_prompt = f"""
请从以下新闻中识别潜在的市场催化剂：

{json.dumps(news_data, indent=2, ensure_ascii=False)}

请识别：
1. 近期催化剂事件
2. 中期催化剂预期
3. 长期结构性变化
4. 催化剂的影响强度
5. 催化剂的时间窗口

请提供市场催化剂分析和投资时机建议。
"""
        
        try:
            response = self.call_llm(catalyst_prompt)
            logger.info("市场催化剂识别完成")
            return {'catalyst_analysis': response}
        except Exception as e:
            logger.error(f"市场催化剂识别失败: {str(e)}")
            return {'catalyst_analysis': f"分析失败: {str(e)}"}


def create_news_analyst(llm_client: LLMClient, **kwargs) -> NewsAnalyst:
    """创建新闻分析师实例"""
    logger.info("创建新闻分析师实例")
    try:
        analyst = NewsAnalyst(llm_client, **kwargs)
        logger.info("新闻分析师实例创建成功")
        return analyst
    except Exception as e:
        logger.error(f"新闻分析师实例创建失败: {str(e)}")
        raise

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from tools.yfinance_tool import YFinanceTool
    
    symbol = "AAPL"
    
    logger.info(f"开始测试新闻分析师 - 股票代码: {symbol}")
    
    yfinance_tool = YFinanceTool()
    market_data = yfinance_tool.get_market_summary(symbol)
    logger.info(f"获取市场数据完成: {symbol}")

    llm_client = LLMClient(provider='deepseek')
    news_analyst = create_news_analyst(llm_client=llm_client)
    result = news_analyst.process(market_data)
    
    logger.info(f"新闻分析测试完成 - 成功: {result.get('success', False)}")