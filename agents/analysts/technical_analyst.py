"""
技术分析师Agent
负责分析股票技术指标、价格模式、交易量等技术面数据
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
from datetime import date
import json

from core.specialized_agents import AnalystAgent
from core.llm_client import LLMClient
from core.state_manager import AgentRole, AnalysisReport
from tools.result_emitters import emit_technical_analysis
from utils.logger import get_logger

logger = get_logger()


class TechnicalAnalyst(AnalystAgent):
    """技术分析师"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [emit_technical_analysis]
        
        super().__init__(
            role=AgentRole.TECHNICAL_ANALYST,
            name="技术分析师",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        logger.info(f"技术分析师初始化完成，可用工具: {len(tools)}个")
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理技术分析请求
        
        Args:
            context: 包含股票代码、价格数据、技术指标等信息
            
        Returns:
            分析结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_process)
    
    def _do_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的处理逻辑（内部方法）
        
        Args:
            context: 包含股票代码、价格数据、技术指标等信息
            
        Returns:
            分析结果
        """
        symbol = context.get('symbol', '')
        market_data = context
        
        logger.info(f"开始技术分析: {symbol}")
        
        # 检查会话状态
        if not self.state_manager.current_session:
            session_id = self.state_manager.start_session(symbol)
            logger.debug(f"创建新交易会话: {session_id}")
        
        try:
            # 验证市场数据
            if not market_data or 'error' in market_data:
                logger.error(f"市场数据无效: {symbol}")
                return {
                    'success': False,
                    'error': f"无法获取{symbol}的市场数据"
                }
            
            # 从market_data中提取技术指标
            technical_indicators = market_data.get('technical_analysis', {})
            indicators_count = len([v for v in technical_indicators.values() if isinstance(v, (int, float))])
            logger.debug(f"获取到 {indicators_count} 个技术指标")
            
            # 准备分析数据
            price_data = self._prepare_price_data_from_market(market_data)
            volume_data = self._prepare_volume_data_from_market(market_data)
            
            # 构建分析提示
            logger.debug("构建技术分析提示")
            analysis_prompt = self._build_analysis_prompt(
                symbol, price_data, technical_indicators, volume_data, market_data
            )
            
            # 使用工具调用进行技术分析，直接返回工具结果
            logger.debug("使用工具调用进行技术分析")
            result = self.process_with_tools_return_result(
                analysis_prompt, 
                'emit_technical_analysis'
            )
            logger.info("工具流程执行完成，获得技术分析结果")
            
            # 增强分析结果
            result = self._enhance_analysis_with_market_data(result, market_data, technical_indicators)
            
            # 创建分析报告
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
                    'price_data': price_data,
                    'technical_indicators': technical_indicators,
                    'volume_data': volume_data,
                    'key_levels': result.get('key_levels', {}),
                    'trend_analysis': {
                        'direction': result.get('trend_direction', '横盘'),
                        'strength': result.get('trend_strength', '中')
                    },
                    'technical_signals': result.get('technical_signals', {})
                },
                detailed_analysis=result.get('supporting_evidence', '')
            )
            
            # 添加到状态管理器
            self.state_manager.add_analysis_report(report)
            
            # 记录成功日志
            recommendation = result.get('recommendation', 'N/A')
            confidence = result.get('confidence_score', 0)
            trend = result.get('trend_direction', 'N/A')
            
            logger.info(f"技术分析完成: {symbol} | 推荐: {recommendation} | 置信度: {confidence:.2f} | 趋势: {trend}")
            
            return {
                'success': True,
                'report': report,
                'analysis_result': result
            }
            
        except Exception as e:
            logger.error(f"技术分析失败: {symbol} - {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_price_data_from_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """从market_data中准备价格数据"""
        return {
            'current_price': market_data.get('current_price', 0),
            'price_change': market_data.get('price_change', 0),
            'price_change_pct': market_data.get('price_change_pct', 0),
            'high_52w': market_data.get('high_52w', 0),
            'low_52w': market_data.get('low_52w', 0),
            'market_cap': market_data.get('market_cap', 'N/A'),
            'pe_ratio': market_data.get('pe_ratio', 'N/A')
        }
    
    def _prepare_volume_data_from_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """从market_data中准备成交量数据"""
        return {
            'current_volume': market_data.get('volume', 0),
            'avg_volume': market_data.get('avg_volume', 0),
            'volume_ratio': market_data.get('volume', 0) / max(market_data.get('avg_volume', 1), 1)
        }
    
    def _build_analysis_prompt(
        self, 
        symbol: str, 
        price_data: Dict[str, Any], 
        technical_indicators: Dict[str, Any], 
        volume_data: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> str:
        """构建分析提示"""
        return f"""
作为专业的技术分析师，请深入分析股票 {symbol} 的技术面：

=== 市场摘要 ===
公司: {market_data.get('company_name', 'N/A')} ({symbol})
行业: {market_data.get('industry', 'N/A')}
当前价格: ${market_data.get('current_price', 'N/A')}
价格变化: {market_data.get('price_change', 'N/A')} ({market_data.get('price_change_pct', 'N/A')}%)

=== 价格数据 ===
{json.dumps(price_data, indent=2, ensure_ascii=False)}

=== 技术指标 ===
{json.dumps(technical_indicators, indent=2, ensure_ascii=False)}

=== 成交量数据 ===
{json.dumps(volume_data, indent=2, ensure_ascii=False)}

请从以下角度进行技术分析：

1. **趋势分析**
   - 基于移动平均线(SMA 50/200, EMA 10)判断主要趋势方向
   - 分析当前价格相对于关键均线的位置
   - 识别关键支撑位和阻力位

2. **动量指标分析**
   - RSI超买超卖状况（>70超买，<30超卖）
   - MACD金叉死叉信号和背离
   - 随机指标(%K, %D)和威廉指标分析

3. **波动率和风险评估**
   - 布林带分析（价格相对于带宽位置）
   - ATR波动率评估
   - VIX恐慌指数含义（如果有）

4. **成交量确认**
   - 量价关系分析
   - 成交量异常情况
   - OBV和A/D资金流向

5. **综合技术判断**
   - 多个指标的一致性信号
   - 潜在的买卖点位
   - 风险控制建议

请使用 emit_technical_analysis 工具提供最终的技术分析结果。
"""
    
    def _enhance_analysis_with_market_data(
        self, 
        result: Dict[str, Any], 
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用market_data增强分析结果"""
        
        # 添加市场数据上下文
        result['market_context'] = {
            'market_cap': market_data.get('market_cap', 'N/A'),
            'pe_ratio': market_data.get('pe_ratio', 'N/A'),
            'analyst_recommendation': market_data.get('analyst_recommendation', 'N/A'),
            'sector': market_data.get('sector', 'N/A'),
            'industry': market_data.get('industry', 'N/A')
        }
        
        # 添加技术指标的具体数值
        result['technical_details'] = {}
        for key, value in technical_indicators.items():
            if isinstance(value, (int, float)):
                result['technical_details'][key] = value
        
        # 添加数据质量信息
        result['data_quality'] = {
            'data_period': market_data.get('data_period', 'N/A'),
            'indicators_available': len([v for v in technical_indicators.values() if isinstance(v, (int, float))]),
            'data_source': 'YFinance via Workflow'
        }
        
        return result
    
    def analyze_momentum_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """分析动量指标
        
        Args:
            indicators: 动量指标数据
            
        Returns:
            动量分析结果
        """
        logger.debug("开始动量指标分析")
        momentum_prompt = f"""
请分析以下动量指标：

{json.dumps(indicators, indent=2, ensure_ascii=False)}

请重点分析：
1. RSI指标的超买超卖情况
2. MACD的金叉死叉信号
3. 随机指标的背离情况
4. 威廉指标的反转信号

请提供详细的动量分析和交易信号。
"""
        
        response = self.call_llm(momentum_prompt)
        logger.debug("动量指标分析完成")
        return {'momentum_analysis': response}
    
    def identify_chart_patterns(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """识别图表形态
        
        Args:
            price_data: 价格数据
            
        Returns:
            形态识别结果
        """
        logger.debug("开始图表形态识别")
        pattern_prompt = f"""
请基于以下价格数据识别技术形态：

{json.dumps(price_data, indent=2, ensure_ascii=False)}

请识别：
1. 经典K线形态（十字星、锤子、吊颈等）
2. 价格形态（头肩顶、双顶双底、三角形等）
3. 突破形态
4. 反转形态

请提供形态识别结果和交易含义。
"""
        
        response = self.call_llm(pattern_prompt)
        logger.debug("图表形态识别完成")
        return {'pattern_analysis': response}
    
    def analyze_volume_price_relationship(self, price_data: Dict[str, Any], volume_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析量价关系
        
        Args:
            price_data: 价格数据
            volume_data: 成交量数据
            
        Returns:
            量价关系分析
        """
        logger.debug("开始量价关系分析")
        volume_price_prompt = f"""
请分析量价关系：

价格数据：
{json.dumps(price_data, indent=2, ensure_ascii=False)}

成交量数据：
{json.dumps(volume_data, indent=2, ensure_ascii=False)}

请分析：
1. 价格上涨时的成交量变化
2. 价格下跌时的成交量变化
3. 异常成交量的含义
4. 量价背离信号
5. 资金流入流出情况

请提供量价关系分析和投资含义。
"""
        
        response = self.call_llm(volume_price_prompt)
        logger.debug("量价关系分析完成")
        return {'volume_price_analysis': response}


def create_technical_analyst(llm_client: LLMClient, **kwargs) -> TechnicalAnalyst:
    """创建技术分析师实例"""
    return TechnicalAnalyst(llm_client, **kwargs)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    logger.info("开始技术分析师测试")
    
    try:
        from tools.yfinance_tool import get_market_summary
        market_data = get_market_summary('AAPL')
        
        if 'error' in market_data:
            logger.error(f"获取市场数据失败: {market_data['error']}")
            exit(1)
        
        logger.info(f"成功获取 {market_data.get('symbol', 'N/A')} 的市场数据")
        
        llm_client = LLMClient(provider='deepseek')
        technical_analyst = create_technical_analyst(llm_client)
        
        logger.info("开始技术分析处理")
        result = technical_analyst.process(market_data)
        
        if result['success']:
            analysis = result['analysis_result']
            logger.info(f"技术分析成功完成")
            logger.info(f"推荐: {analysis.get('recommendation', 'N/A')}")
            logger.info(f"置信度: {analysis.get('confidence_score', 0):.2f}")
            logger.info(f"趋势: {analysis.get('trend_direction', 'N/A')}")
        else:
            logger.error(f"技术分析失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        logger.error(f"测试过程中发生异常: {str(e)}", exc_info=True)