"""
基金经理Agent
负责整合所有团队的分析结果，做出最终的投资决策
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
from datetime import datetime

from core.agent_base import BaseAgent
from core.llm_client import LLMClient, safe_json_dumps
from core.state_manager import AgentRole
from tools.result_emitters import emit_fund_manager_decision


class FundManager(BaseAgent):
    """基金经理Agent"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [emit_fund_manager_decision]
        
        super().__init__(
            role=AgentRole.FUND_MANAGER,
            name="基金经理",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        
        # 基金经理特殊系统提示
        self.system_prompt = f"""你是一位资深的基金经理，具有丰富的投资管理经验和卓越的决策能力。

核心职责：
1. 整合所有团队的专业分析和建议
2. 综合考虑风险与收益的平衡
3. 做出最终的投资决策（买入/持有/卖出）
4. 对投资决策承担最终责任
5. 确保决策符合基金的投资策略和风险偏好

决策原则：
- 以保护投资者利益为首要目标
- 基于全面的风险评估做出决策
- 综合考虑短期机会和长期价值
- 严格遵循风险管理原则
- 保持投资纪律和一致性

团队结构理解：
- 分析师团队：提供基本面、技术面、情绪面、新闻面的专业分析
- 研究团队：通过多空辩论深入探讨投资机会和风险
- 交易员：基于分析结果提供具体的交易建议和执行计划  
- 风险管理团队：评估和控制投资风险，提供风险管理建议

你需要基于所有团队的输入，做出最终的投资决策，并提供详细的决策逻辑和风险控制措施。
"""
        
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理最终投资决策请求
        
        Args:
            context: 包含所有团队的分析和建议
            
        Returns:
            最终投资决策结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_process)
    
    def _do_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的处理逻辑（内部方法）
        
        Args:
            context: 包含所有团队的分析和建议
            
        Returns:
            最终投资决策结果
        """
        symbol = context.get('symbol', '')
        analysis_reports = context.get('analysis_reports', {})
        debate_result = context.get('debate_result', {})
        trading_decision = context.get('trading_decision', {})
        risk_assessment = context.get('risk_assessment', {})
        market_context = context.get('market_context', {})
        
        self.log_action("开始最终投资决策", {'symbol': symbol})
        
        # 构建最终决策提示
        decision_prompt = self._build_decision_prompt(
            symbol, analysis_reports, debate_result, 
            trading_decision, risk_assessment, market_context
        )
        
        try:
            final_decision = self.process_with_tools_return_result(
                decision_prompt, 
                'emit_fund_manager_decision'
            )
            
            
            # 创建最终投资决策对象
            investment_decision = {
                'symbol': symbol,
                'final_recommendation': final_decision.get('recommendation', 'HOLD'),
                'confidence_score': final_decision.get('confidence_score', 0.5),
                'position_size': final_decision.get('position_size', 0.0),
                'reasoning': final_decision.get('reasoning', ''),
                'risk_factors': final_decision.get('risk_factors', []),
                'expected_return': final_decision.get('expected_return', 0.0),
                'max_drawdown': final_decision.get('max_drawdown', 0.0),
                'time_horizon': final_decision.get('time_horizon', '中期'),
                'decision_timestamp': datetime.now().isoformat(),
                'team_consensus': final_decision.get('team_consensus', {}),
                'decision_rationale': final_decision.get('decision_rationale', ''),
                'contingency_plans': final_decision.get('contingency_plans', [])
            }
            
            self.log_action("最终投资决策完成", {
                'recommendation': final_decision.get('recommendation'),
                'confidence': final_decision.get('confidence_score'),
                'position_size': final_decision.get('position_size')
            })
            
            return {
                'success': True,
                'investment_decision': investment_decision,
                'decision_details': final_decision,
                'summary': f"基金经理最终决策：{final_decision.get('recommendation', 'HOLD')}"
            }
            
        except Exception as e:
            self.log_action("最终投资决策失败", {'error': str(e)})
            return {
                'success': False,
                'error': str(e),
                'investment_decision': {
                    'symbol': symbol,
                    'final_recommendation': 'HOLD',
                    'confidence_score': 0.3,
                    'reasoning': f"决策过程出现错误：{str(e)}，采用保守策略",
                    'decision_timestamp': datetime.now().isoformat()
                }
            }
    
    def _serialize_team_inputs(self, data: Any) -> Any:
        """序列化团队输入数据，处理各种对象类型"""
        if hasattr(data, 'to_dict'):
            return data.to_dict()
        elif hasattr(data, '__dict__'):
            return data.__dict__
        elif isinstance(data, dict):
            return {k: self._serialize_team_inputs(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_team_inputs(item) for item in data]
        else:
            return data
    
    def _build_decision_prompt(
        self, 
        symbol: str,
        analysis_reports: Dict[str, Any],
        debate_result: Dict[str, Any],
        trading_decision: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> str:
        """构建最终决策提示"""
        
        # 序列化所有输入数据
        serialized_analysis = self._serialize_team_inputs(analysis_reports)
        serialized_debate = self._serialize_team_inputs(debate_result)
        serialized_trading = self._serialize_team_inputs(trading_decision)
        serialized_risk = self._serialize_team_inputs(risk_assessment)
        serialized_market = self._serialize_team_inputs(market_context)
        
        prompt = f"""
作为基金经理，请基于以下所有团队的专业分析对股票 {symbol} 做出最终投资决策：

【分析师团队报告】
{safe_json_dumps(serialized_analysis, indent=2, ensure_ascii=False)}

【研究团队辩论结果】
{safe_json_dumps(serialized_debate, indent=2, ensure_ascii=False)}

【交易员建议】
{safe_json_dumps(serialized_trading, indent=2, ensure_ascii=False)}

【风险管理评估】
{safe_json_dumps(serialized_risk, indent=2, ensure_ascii=False)}

【市场环境分析】
{safe_json_dumps(serialized_market, indent=2, ensure_ascii=False)}

作为基金经理，请从以下维度进行综合决策分析：

1. 团队观点整合
   - 分析师团队的核心观点和分歧
   - 研究团队辩论的关键结论
   - 交易员的具体建议和执行计划
   - 风险管理团队的风险评估和建议
   - 各团队观点的权重分配和可信度评估

2. 风险收益评估
   - 潜在收益空间和实现概率
   - 主要风险因素和影响程度
   - 风险调整后的预期收益
   - 最大可容忍损失和回撤控制
   - 与基金整体风险偏好的匹配度

3. 投资决策制定
   - 明确的买入/持有/卖出决策
   - 具体的仓位配置建议
   - 投资时间周期和退出条件
   - 分批建仓或减仓的策略
   - 动态调整的触发条件

4. 风险管理措施
   - 止损止盈的具体设置
   - 仓位控制和资金管理
   - 市场变化的应对预案
   - 定期评估和调整机制
   - 与基金整体风险管理的协调

5. 决策责任和问责
   - 决策的核心逻辑和关键假设
   - 预期结果和成功标准
   - 失败情况下的责任归因
   - 持续跟踪和优化措施
   - 投资者利益保护措施

请使用 emit_fund_manager_decision 工具提供最终的投资决策，确保所有参数都被正确填充。

注意事项：
- contingency_plans 参数是字符串数组，每个元素应为包含 scenario 和 action 的 JSON 字符串
""" + '- 例如: [\'{"scenario": "市场下跌", "action": "逐步减仓至50%"}\', \'{"scenario": "基本面恶化", "action": "立即清仓"}\']' + """
- team_*_weight 参数之和应接近 1.0
- 所有参数都是必填的，请确保提供所有字段的值

请确保决策逻辑清晰、风险可控，充分体现基金经理的专业判断和对投资者的责任。最终必须给出明确且可执行的投资决策。
"""
        return prompt


def create_fund_manager(llm_client: LLMClient, **kwargs) -> FundManager:
    """创建基金经理实例"""
    return FundManager(llm_client, **kwargs)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # 创建测试用的模拟数据
    test_context = {
        'symbol': 'AAPL',
        'analysis_reports': {
            'fundamental_analyst': {
                'recommendation': 'BUY',
                'confidence_score': 0.8,
                'key_findings': ['强劲财报', '估值合理']
            },
            'technical_analyst': {
                'recommendation': 'BUY', 
                'confidence_score': 0.7,
                'key_findings': ['技术面突破', 'RSI正常']
            },
            'news_analyst': {
                'news_impact': '利好',
                'confidence_score': 0.75,
                'key_findings': ['正面新闻', '管理层指引积极']
            },
            'sentiment_analyst': {
                'sentiment_level': '乐观',
                'confidence_score': 0.65,
                'key_findings': ['市场情绪积极', '机构看好']
            }
        },
        'debate_result': {
            'final_consensus': 'BUY',
            'consensus_strength': 0.8,
            'key_arguments': ['基本面强劲', '技术面确认']
        },
        'trading_decision': {
            'recommendation': 'BUY',
            'entry_strategy': '分批买入',
            'position_size': 0.6
        },
        'risk_assessment': {
            'overall_risk': 'medium',
            'max_drawdown': 0.15,
            'risk_factors': ['市场波动', '宏观风险']
        },
        'market_context': {
            'market_trend': 'bull',
            'volatility': 'normal',
            'economic_outlook': 'positive'
        }
    }
    
    print("开始测试基金经理工具调用...")
    
    try:
        # 创建LLM客户端和基金经理实例
        llm_client = LLMClient(provider='deepseek')
        fund_manager = create_fund_manager(llm_client)
        
        result = fund_manager.process(test_context)
        
        if result.get('success'):
            print(result)
        else:
            print(f"- 错误: {result.get('error')}")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")