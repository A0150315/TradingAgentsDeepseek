"""
保守风险分析师
从风险控制和资产保护角度评估交易决策
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List
import json

from core.agent_base import BaseAgent
from core.llm_client import LLMClient, safe_json_dumps
from core.state_manager import AgentRole, get_state_manager
from tools.result_emitters import emit_conservative_risk_analysis


class ConservativeAnalyst(BaseAgent):
    """保守风险分析师"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [emit_conservative_risk_analysis]
        
        super().__init__(
            role=AgentRole.RISK_MANAGER,
            name="保守风险分析师",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        
        self.system_prompt = f"""你是一位保守的风险分析师，你的核心职责是保护资产、最小化波动性，确保稳定可靠的增长。

核心原则：
1. 优先考虑稳定性、安全性和风险缓解
2. 仔细评估潜在损失、经济衰退和市场波动性
3. 在评估交易决策时，批判性审视高风险元素
4. 指出决策可能使公司面临不当风险的地方
5. 寻找更谨慎的替代方案以确保长期收益

辩论策略：
- 质疑对手的乐观态度
- 强调他们可能忽视的潜在下行风险
- 展示为什么保守立场最终是公司资产最安全的路径
- 使用具体数据和历史案例支持论点
- 关注可持续性和长期价值保护

保持专业但要坚定地捍卫低风险策略的优势。
"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求 - 重定向到风险分析"""
        return self.analyze_risks(context)
    
    def analyze_risks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析风险因素
        
        Args:
            context: 包含交易决策、市场数据等信息
            
        Returns:
            风险分析结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_analyze_risks)
    
    def _do_analyze_risks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的风险分析逻辑（内部方法）
        
        Args:
            context: 包含交易决策、市场数据等信息
            
        Returns:
            风险分析结果
        """
        trading_decision = context.get('trading_decision', {})
        market_data = context.get('market_data', {})
        analysis_reports = context.get('analysis_reports', {})
        
        self.log_action("开始保守风险分析", {
            'decision': trading_decision.get('recommendation', 'UNKNOWN')
        })
        
        risk_prompt = f"""
作为保守风险分析师，请对以下交易决策进行风险评估：

交易决策：
{safe_json_dumps(trading_decision, indent=2, ensure_ascii=False)}

市场数据：
{safe_json_dumps(market_data, indent=2, ensure_ascii=False)}

分析师报告：
{safe_json_dumps(analysis_reports, indent=2, ensure_ascii=False)}

请从保守角度重点分析：

1. 下行风险评估
   - 最坏情况下的潜在损失
   - 市场波动对投资的影响
   - 宏观经济不确定性
   - 行业特定风险

2. 决策风险点
   - 高风险元素识别
   - 过度乐观的假设
   - 忽视的风险因素
   - 时机选择风险

3. 资产保护建议
   - 降低仓位建议
   - 严格止损设置
   - 分散投资重要性
   - 现金保留策略

4. 替代方案
   - 更安全的投资选择
   - 分阶段投资策略
   - 避险资产配置
   - 等待更好时机

5. 长期稳定性
   - 可持续收益考虑
   - 避免短期投机
   - 价值投资原则
   - 风险调整后收益

请提供保守的风险评估和建议：

请使用 emit_conservative_risk_analysis 工具提供最终的保守风险分析结果。
"""
        
        try:
            # 使用工具调用进行保守风险分析，直接返回工具结果
            result = self.process_with_tools_return_result(
                risk_prompt, 
                'emit_conservative_risk_analysis'
            )
            
            self.log_action("保守风险分析完成", {
                'risk_level': result.get('risk_level', 'UNKNOWN'),
                'recommendation': result.get('conservative_recommendation', 'UNKNOWN')
            })
            
            return {
                'success': True,
                'analysis_result': result,
                'analyst_type': 'conservative'
            }
            
        except Exception as e:
            self.log_action("保守风险分析失败", {'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }
    
    def debate_response(self, topic: str, opponent_arguments: List[str], context: Dict[str, Any] = None) -> str:
        """参与风险辩论（保守角度）
        
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

作为保守风险分析师，请针对对手论点进行有力反驳：

1. 指出对手论点的局限性或片面性
2. 强调被忽视的风险因素
3. 提供支持保守立场的数据和案例
4. 展示长期稳定性的重要性
5. 质疑过度乐观的假设

请提供具有说服力的保守观点反驳，要求：
- 使用具体数据和历史案例
- 逻辑清晰、条理分明
- 针对性回应对手观点
- 突出风险控制的重要性
- 展示保守策略的长期优势

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


def create_conservative_analyst(llm_client: LLMClient, **kwargs) -> ConservativeAnalyst:
    """创建保守风险分析师实例"""
    return ConservativeAnalyst(llm_client, **kwargs)