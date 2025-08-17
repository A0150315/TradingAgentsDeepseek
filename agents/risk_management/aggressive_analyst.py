"""
激进风险分析师
从高风险高收益角度评估交易决策，寻找成长机会
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List
import json

from core.agent_base import BaseAgent
from core.llm_client import LLMClient, safe_json_dumps
from core.state_manager import AgentRole, get_state_manager
from tools.result_emitters import emit_aggressive_opportunity_analysis


class AggressiveAnalyst(BaseAgent):
    """激进风险分析师"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [emit_aggressive_opportunity_analysis]
        
        super().__init__(
            role=AgentRole.RISK_MANAGER,
            name="激进风险分析师",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        
        self.system_prompt = f"""你是一位激进的风险分析师，你的角色是积极支持高收益、高风险机会，强调大胆策略和竞争优势。

核心原则：
1. 专注于潜在上行空间、增长潜力和创新收益
2. 即使面临较高风险，也要寻找高回报机会
3. 使用市场数据和情绪分析强化论点
4. 挑战保守和中性观点的局限性
5. 强调风险承担如何超越市场常规表现

辩论策略：
- 质疑保守态度可能错失的关键机会
- 强调假设过于保守的地方
- 反驳保守逻辑的弱点
- 断言风险承担的好处以超越市场常规
- 积极应对任何特定担忧
- 保持专注于辩论和说服，而非仅仅呈现数据

你要为高风险方法的最优性提供令人信服的论证。
"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求 - 重定向到机会分析"""
        return self.analyze_opportunities(context)
    
    def analyze_opportunities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析投资机会
        
        Args:
            context: 包含交易决策、市场数据等信息
            
        Returns:
            机会分析结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_analyze_opportunities)
    
    def _do_analyze_opportunities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的机会分析逻辑（内部方法）
        
        Args:
            context: 包含交易决策、市场数据等信息
            
        Returns:
            机会分析结果
        """
        trading_decision = context.get('trading_decision', {})
        market_data = context.get('market_data', {})
        analysis_reports = context.get('analysis_reports', {})
        
        self.log_action("开始激进机会分析", {
            'decision': trading_decision.get('recommendation', 'UNKNOWN')
        })
        
        opportunity_prompt = f"""
作为激进风险分析师，请对以下交易决策进行机会评估：

交易决策：
{safe_json_dumps(trading_decision, indent=2, ensure_ascii=False)}

市场数据：
{safe_json_dumps(market_data, indent=2, ensure_ascii=False)}

分析师报告：
{safe_json_dumps(analysis_reports, indent=2, ensure_ascii=False)}

请从激进角度重点分析：

1. 上行潜力评估
   - 最佳情况下的收益空间
   - 突破性增长可能性
   - 市场领先机会
   - 创新价值发现

2. 增长驱动因素
   - 行业变革机遇
   - 技术创新优势
   - 市场扩张潜力
   - 竞争壁垒建立

3. 时机优势
   - 先发优势获取
   - 市场周期把握
   - 估值洼地发现
   - 催化剂效应

4. 风险收益比优化
   - 高收益机会识别
   - 风险可控性分析
   - 资金效率最大化
   - 复合增长潜力

5. 竞争优势
   - 差异化投资策略
   - 超越市场表现
   - 长期价值创造
   - 品牌价值提升

请提供激进的机会评估和建议：

请使用 emit_aggressive_opportunity_analysis 工具提供最终的激进机会分析结果。
"""
        
        try:
            # 使用工具调用进行激进机会分析，直接返回工具结果
            result = self.process_with_tools_return_result(
                opportunity_prompt, 
                'emit_aggressive_opportunity_analysis'
            )
            
            self.log_action("激进机会分析完成", {
                'upside_potential': result.get('upside_potential', 'UNKNOWN'),
                'recommendation': result.get('aggressive_recommendation', 'UNKNOWN')
            })
            
            return {
                'success': True,
                'analysis_result': result,
                'analyst_type': 'aggressive'
            }
            
        except Exception as e:
            self.log_action("激进机会分析失败", {'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }
    
    def debate_response(self, topic: str, opponent_arguments: List[str], context: Dict[str, Any] = None) -> str:
        """参与风险辩论（激进角度）
        
        Args:
            topic: 辩论主题
            opponent_arguments: 对手论点
            context: 上下文信息
            
        Returns:
            辩论回应
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_debate_response_with_llm_logging(topic, opponent_arguments, context or {}, self._do_debate_response)
    
    def _do_debate_response(self, topic: str, opponent_arguments: List[str], context: Dict[str, Any]) -> str:
        """实际的辩论回应逻辑（内部方法）
        
        Args:
            topic: 辩论主题
            opponent_arguments: 对手论点
            context: 上下文信息
            
        Returns:
            辩论回应
        """
        debate_prompt = f"""
辩论主题：{topic}

对手论点：
{chr(10).join([f"- {arg}" for arg in opponent_arguments])}

上下文信息：
{safe_json_dumps(context or {}, indent=2, ensure_ascii=False)}

作为激进风险分析师，请针对对手论点进行有力反驳：

1. 指出保守态度可能错失的关键机会
2. 强调过度谨慎的局限性
3. 提供支持激进策略的成功案例和数据
4. 展示风险承担带来的竞争优势
5. 质疑保守假设的合理性

请提供具有说服力的激进观点论证，要求：
- 使用具体的增长数据和市场案例
- 逻辑清晰、富有说服力
- 针对性反驳保守观点
- 突出高收益机会的价值
- 展示激进策略的长期优势

以对话方式回应，无需特殊格式。
"""
        
        response = self.call_llm(debate_prompt)
        
        # 记录辩论消息
        self.state_manager.add_debate_message(
            'risk_management',
            self.role,
            response,
            {'topic': topic, 'opponent_arguments': opponent_arguments}
        )
        
        return response


def create_aggressive_analyst(llm_client: LLMClient, **kwargs) -> AggressiveAnalyst:
    """创建激进风险分析师实例"""
    return AggressiveAnalyst(llm_client, **kwargs)