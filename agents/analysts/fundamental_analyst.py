"""
基础分析师Agent
负责分析公司基本面数据，包括财务报表、估值指标、行业地位等
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
from tools.result_emitters import emit_fundamental_analysis
from utils.logger import get_logger

logger = get_logger()


class FundamentalAnalyst(AnalystAgent):
    """基础分析师"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [unified_google_search, emit_fundamental_analysis]
        
        super().__init__(
            role=AgentRole.FUNDAMENTAL_ANALYST,
            name="基础分析师",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        logger.info(f"基础分析师初始化完成，可用工具: {len(tools)}个")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理基础分析请求
        
        Args:
            context: 包含股票代码、财务数据等信息
            
        Returns:
            分析结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_process)
    
    def _do_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的处理逻辑（内部方法）
        
        Args:
            context: 包含股票代码、财务数据等信息
            
        Returns:
            分析结果
        """
        start_time = time.time()
        symbol = context.get('symbol', '')
        logger.info(f"开始基础分析流程 - 股票代码: {symbol}")
        self.log_action("开始基础分析", {'symbol': symbol})
        
        # 检查并创建会话（如果没有活跃会话）
        if not self.state_manager.current_session:
            logger.info("没有活跃会话，创建新的交易会话")
            session_id = self.state_manager.start_session(symbol)
            logger.info(f"创建会话成功: {session_id}")
        
        # 从context中提取市场数据（类似technical_analyst.py）
        market_data = context
        
        # 验证市场数据
        if not market_data or 'error' in market_data:
            logger.error(f"市场数据无效: {symbol}")
            return {
                'success': False,
                'error': f"无法获取{symbol}的市场数据",
                'processing_time': time.time() - start_time
            }
        
        # 从market_data中准备基本面数据
        fundamental_data = self._prepare_fundamental_data_from_market(market_data)
        financial_metrics = self._prepare_financial_metrics_from_market(market_data)
        
        # 构建分析提示，LLM会自动知道有哪些工具可用
        analysis_prompt = f"""
作为专业的基础分析师，请深入分析与股票 {symbol} 相关的公司基本面和财务状况。

请按以下步骤进行分析：

第一步：获取相关新闻和数据
- 使用google_search工具搜索与 {symbol} 相关的财务、基本面、公司业绩相关的新闻
- 可以搜索关键词如："{symbol} earnings"、"{symbol} financial results"、"{symbol} revenue"、"{symbol} profit"等
- 也可以搜索行业和竞争对手的新闻，如"{symbol} competitors"、"{symbol} industry analysis"等

第二步：基于获取的新闻和市场数据进行深入分析

=== 当前市场摘要 ===
公司: {market_data.get('company_name', 'N/A')} ({symbol})
行业: {market_data.get('industry', 'N/A')}
板块: {market_data.get('sector', 'N/A')}
当前价格: ${market_data.get('current_price', 'N/A')}
价格变化: {market_data.get('price_change', 'N/A')} ({market_data.get('price_change_pct', 'N/A')}%)

=== 基本面数据 ===
{json.dumps(fundamental_data, indent=2, ensure_ascii=False)}

=== 财务指标 ===
{json.dumps(financial_metrics, indent=2, ensure_ascii=False)}

请从以下角度进行基本面分析：

1. **盈利能力分析**
   - 营收增长趋势和质量
   - 净利润率和毛利率变化
   - ROE和ROA表现
   - 营业利润率和EBITDA分析

2. **财务健康状况**
   - 流动比率和速动比率
   - 资产负债率和偿债能力
   - 现金流状况和现金储备
   - 债务结构和利息覆盖率

3. **估值分析**
   - P/E比率的合理性（相对历史和行业）
   - P/B比率和账面价值分析
   - PEG比率和成长性估值
   - EV/EBITDA和企业价值分析
   - 与同行业公司对比

4. **成长性和竞争力分析**
   - 营收和利润增长率
   - 市场份额和竞争地位
   - 护城河和竞争优势
   - 管理层质量和公司治理
   - 业务多元化和市场扩张

5. **行业和宏观分析**
   - 行业增长前景和周期性
   - 宏观经济环境影响
   - 政策环境和监管风险
   - 技术变革和行业趋势

6. **风险评估**
   - 财务风险和流动性风险
   - 经营风险和市场风险
   - 行业风险和宏观风险
   - 管理风险和公司治理风险

请使用 emit_fundamental_analysis 工具提供最终的基本面分析结果。
"""
        
        try:
            logger.info("开始执行基础分析工具流程")
            # 使用工具调用处理分析请求，直接返回工具结果
            result = self.process_with_tools_return_result(
                analysis_prompt, 
                'emit_fundamental_analysis'
            )
            logger.info("工具流程执行完成，获得分析结果")
            
            logger.info(f"基础分析结果获得 - 推荐: {result.get('recommendation', 'N/A')}, 置信度: {result.get('confidence_score', 'N/A')}")
            
            # 增强分析结果
            result = self._enhance_analysis_with_market_data(result, market_data, fundamental_data, financial_metrics)
            
            # 创建分析报告
            logger.debug("创建基础分析报告")
            report = AnalysisReport(
                analyst_role=self.role,
                symbol=symbol,
                analysis_date=date.today(),
                key_findings=result.get('key_findings', []),
                recommendation=result.get('recommendation', 'HOLD'),
                confidence_score=result.get('confidence_score', 0.5),
                risk_factors=result.get('risk_factors', []),
                time_horizon=result.get('time_horizon', {}),
                impact_magnitude=result.get('confidence_score', 0.5),  # 使用置信度作为影响强度
                supporting_data={
                    'market_data': market_data,
                    'fundamental_data': fundamental_data,
                    'financial_metrics': financial_metrics,
                    'valuation_assessment': result.get('valuation_assessment', {}),
                    'financial_health': result.get('financial_health', {}),
                    'growth_prospects': result.get('growth_prospects', {}),
                    'catalysts': result.get('catalysts', [])
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
            logger.info(f"基础分析流程完成 - 处理时间: {processing_time:.2f}秒")
            
            self.log_action("基础分析完成", {
                'recommendation': result.get('recommendation'),
                'confidence': result.get('confidence_score'),
                'valuation': result.get('valuation_assessment', {}).get('current_valuation'),
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
            logger.error(f"基础分析流程失败 - 错误: {str(e)}, 处理时间: {processing_time:.2f}秒")
            self.log_action("基础分析失败", {
                'error': str(e),
                'processing_time': processing_time,
                'symbol': symbol
            })
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    def _prepare_fundamental_data_from_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """从market_data中准备基本面数据"""
        return {
            'current_price': market_data.get('current_price', 0),
            'market_cap': market_data.get('market_cap', 'N/A'),
            'pe_ratio': market_data.get('pe_ratio', 'N/A'),
            'company_name': market_data.get('company_name', 'N/A'),
            'sector': market_data.get('sector', 'N/A'),
            'industry': market_data.get('industry', 'N/A'),
            'high_52w': market_data.get('high_52w', 0),
            'low_52w': market_data.get('low_52w', 0),
            'volume': market_data.get('volume', 0),
            'avg_volume': market_data.get('avg_volume', 0)
        }
    
    def _prepare_financial_metrics_from_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """从market_data中准备财务指标数据"""
        # 注意：从yfinance_tool.py我们可以看到有这些财务指标可用
        return {
            'pe_ratio': market_data.get('pe_ratio', 'N/A'),
            'market_cap': market_data.get('market_cap', 'N/A'),
            'analyst_recommendation': market_data.get('analyst_recommendation', 'N/A'),
            'analyst_votes': market_data.get('analyst_votes', 0),
            'price_change_pct': market_data.get('price_change_pct', 0),
            'data_period': market_data.get('data_period', 'N/A')
        }
    
    def _enhance_analysis_with_market_data(
        self, 
        result: Dict[str, Any], 
        market_data: Dict[str, Any],
        fundamental_data: Dict[str, Any],
        financial_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用market_data增强分析结果"""
        
        # 添加市场数据上下文
        result['market_context'] = {
            'current_price': market_data.get('current_price', 'N/A'),
            'market_cap': market_data.get('market_cap', 'N/A'),
            'pe_ratio': market_data.get('pe_ratio', 'N/A'),
            'sector': market_data.get('sector', 'N/A'),
            'industry': market_data.get('industry', 'N/A'),
            'analyst_recommendation': market_data.get('analyst_recommendation', 'N/A')
        }
        
        # 添加基本面指标的具体数值
        result['fundamental_details'] = fundamental_data
        result['financial_details'] = financial_metrics
        
        # 添加数据质量信息
        result['data_quality'] = {
            'data_period': market_data.get('data_period', 'N/A'),
            'data_source': 'YFinance via Workflow',
            'analysis_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        return result
    
def create_fundamental_analyst(llm_client: LLMClient, **kwargs) -> FundamentalAnalyst:
    """创建基础分析师实例"""
    logger.info("创建基础分析师实例")
    try:
        analyst = FundamentalAnalyst(llm_client, **kwargs)
        logger.info("基础分析师实例创建成功")
        return analyst
    except Exception as e:
        logger.error(f"基础分析师实例创建失败: {str(e)}")
        raise

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from tools.yfinance_tool import YFinanceTool
    
    symbol = "AAPL"
    
    logger.info(f"开始测试基础分析师 - 股票代码: {symbol}")
    
    yfinance_tool = YFinanceTool()
    market_data = yfinance_tool.get_market_summary(symbol)
    logger.info(f"获取市场数据完成: {symbol}")

    llm_client = LLMClient(provider='deepseek')
    fundamental_analyst = create_fundamental_analyst(llm_client=llm_client)
    result = fundamental_analyst.process(market_data)
    
    logger.info(f"基础分析测试完成 - 成功: {result.get('success', False)}")
    
    # 只输出分析结果，不包含不可序列化的对象
    if result.get('success'):
        analysis_result = result.get('analysis_result', {})
        logger.info(f"分析推荐: {analysis_result.get('recommendation', 'N/A')}")
        logger.info(f"置信度: {analysis_result.get('confidence_score', 'N/A')}")
        logger.info(f"估值评估: {analysis_result.get('valuation_assessment', {}).get('current_valuation', 'N/A')}")
        logger.info(f"关键发现数量: {len(analysis_result.get('key_findings', []))}")
        logger.info(f"处理时间: {result.get('processing_time', 0):.2f}秒")
    else:
        logger.error(f"分析失败: {result.get('error', '未知错误')}")