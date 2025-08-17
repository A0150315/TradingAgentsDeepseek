"""
中性风险分析师
提供平衡的风险收益分析，权衡各种因素
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List
import json

from core.agent_base import BaseAgent
from core.llm_client import LLMClient, safe_json_dumps
from core.state_manager import AgentRole, get_state_manager
from tools.result_emitters import emit_neutral_balance_analysis


class NeutralAnalyst(BaseAgent):
    """中性风险分析师"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [emit_neutral_balance_analysis]
        
        super().__init__(
            role=AgentRole.RISK_MANAGER,
            name="中性风险分析师",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        
        self.system_prompt = f"""你是一位中性风险分析师，你的角色是提供平衡的视角，权衡投资决策的潜在收益和风险。

核心原则：
1. 优先考虑全面的方法，评估上行空间和下行风险
2. 考虑更广泛的市场趋势、潜在经济变化和多元化策略
3. 挑战激进和保守分析师的观点
4. 指出每种观点可能过于乐观或过于谨慎的地方
5. 倡导适度、可持续的策略

辩论策略：
- 分析双方观点，指出各自的弱点
- 提供平衡的数据支持适度策略
- 展示平衡观点如何提供两全其美的结果
- 挑战极端立场，展示中间路线的价值
- 强调可持续性和风险调整后的收益

专注于辩论而非仅仅呈现数据，旨在展示平衡观点能够带来最可靠的结果。
"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求 - 重定向到平衡分析"""
        return self.analyze_balance(context)
    
    def analyze_balance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """进行平衡分析
        
        Args:
            context: 包含交易决策、市场数据等信息
            
        Returns:
            平衡分析结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_analyze_balance)
    
    def _do_analyze_balance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的平衡分析逻辑（内部方法）
        
        Args:
            context: 包含交易决策、市场数据等信息
            
        Returns:
            平衡分析结果
        """
        trading_decision = context.get('trading_decision', {})
        market_data = context.get('market_data', {})
        analysis_reports = context.get('analysis_reports', {})
        conservative_view = context.get('conservative_analysis', {})
        aggressive_view = context.get('aggressive_analysis', {})
        
        self.log_action("开始中性平衡分析", {
            'decision': trading_decision.get('recommendation', 'UNKNOWN')
        })
        
        balance_prompt = f"""
作为中性风险分析师，请对以下交易决策进行平衡评估：

交易决策：
{safe_json_dumps(trading_decision, indent=2, ensure_ascii=False)}

市场数据：
{safe_json_dumps(market_data, indent=2, ensure_ascii=False)}

分析师报告：
{safe_json_dumps(analysis_reports, indent=2, ensure_ascii=False)}

保守观点：
{safe_json_dumps(conservative_view, indent=2, ensure_ascii=False)}

激进观点：
{safe_json_dumps(aggressive_view, indent=2, ensure_ascii=False)}

请从中性角度进行平衡分析：

1. 风险收益平衡
   - 客观评估上行和下行空间
   - 概率加权的收益预期
   - 风险调整后的回报分析
   - 最优风险承受水平

2. 市场环境综合评估
   - 宏观经济因素影响
   - 行业周期性考虑
   - 市场情绪的合理性
   - 长期趋势vs短期波动

3. 投资组合整体考虑
   - 与现有持仓的相关性
   - 分散化效应
   - 流动性需求
   - 总体风险暴露

4. 时机和执行策略
   - 入场时机的合理性
   - 分批投资的必要性
   - 动态调整机制
   - 退出策略的完整性

5. 极端情况分析
   - 压力测试结果
   - 黑天鹅事件影响
   - 应急预案充分性
   - 恢复能力评估

请提供平衡的风险收益评估：

请使用 emit_neutral_balance_analysis 工具提供最终的中性平衡分析结果。
"""
        
        try:
            # 使用工具调用进行中性平衡分析，直接返回工具结果
            result = self.process_with_tools_return_result(
                balance_prompt, 
                'emit_neutral_balance_analysis'
            )
            
            self.log_action("中性平衡分析完成", {
                'risk_reward_ratio': result.get('risk_reward_ratio', 'UNKNOWN'),
                'recommendation': result.get('balanced_recommendation', 'UNKNOWN')
            })
            
            return {
                'success': True,
                'analysis_result': result,
                'analyst_type': 'neutral'
            }
            
        except Exception as e:
            self.log_action("中性平衡分析失败", {'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }
    
    def debate_response(self, topic: str, opponent_arguments: List[str], context: Dict[str, Any] = None) -> str:
        """参与风险辩论（中性角度）
        
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

作为中性风险分析师，请针对对手的极端观点提供平衡视角：

1. 分析保守和激进观点的合理性
2. 指出双方可能的偏见和局限性
3. 提供客观的数据支持平衡策略
4. 展示适度策略的优势
5. 寻找双方观点的结合点

请提供平衡的观点论证，要求：
- 客观分析各方观点的优缺点
- 使用数据支持中庸策略的有效性
- 逻辑清晰、公正合理
- 寻求最优的风险收益平衡
- 展示可持续发展的重要性

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


def create_neutral_analyst(llm_client: LLMClient, **kwargs) -> NeutralAnalyst:
    """创建中性风险分析师实例"""
    return NeutralAnalyst(llm_client, **kwargs)