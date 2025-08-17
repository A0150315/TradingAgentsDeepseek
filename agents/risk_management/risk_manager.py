"""
风险管理总监
协调风险辩论并做出最终风险管理决策
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List
import json
from datetime import datetime

from core.agent_base import BaseAgent
from core.llm_client import LLMClient, safe_json_dumps
from core.state_manager import AgentRole, get_state_manager
from tools.result_emitters import emit_risk_management_decision


class RiskManager(BaseAgent):
    """风险管理总监"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [emit_risk_management_decision]
        
        super().__init__(
            role=AgentRole.RISK_MANAGER,
            name="风险管理总监",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        
        self.system_prompt = f"""你是风险管理总监和辩论协调者，你的目标是评估三位风险分析师（激进、中性、保守）之间的辩论，并确定最佳的风险管理策略。

核心职责：
1. 评估各位分析师的观点和论证质量
2. 综合考虑所有风险因素和机会
3. 做出明确的风险管理决策
4. 为交易决策提供风险调整建议
5. 从历史经验中学习，避免重复错误

决策准则：
- 总结各方关键论点，关注与当前情况的相关性
- 提供理由支持，直接引用辩论中的观点和反驳
- 基于分析师的洞察调整交易计划
- 从历史错误中学习，改进决策质量
- 确保每个决策都朝着更好的结果前进

你必须提供明确、可执行的风险管理建议，包括具体的仓位调整、风险控制措施和应急预案。
"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求 - 重定向到风险辩论评估"""
        return self.evaluate_risk_debate(context)
    
    def evaluate_risk_debate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险辩论并做出决策
        
        Args:
            context: 包含辩论历史、交易决策等信息
            
        Returns:
            风险管理决策
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_evaluate_risk_debate)
    
    def _do_evaluate_risk_debate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的风险辩论评估逻辑（内部方法）
        
        Args:
            context: 包含辩论历史、交易决策等信息
            
        Returns:
            风险管理决策
        """
        debate_history = context.get('debate_history', '')
        trading_decision = context.get('trading_decision', {})
        conservative_analysis = context.get('conservative_analysis', {})
        aggressive_analysis = context.get('aggressive_analysis', {})
        neutral_analysis = context.get('neutral_analysis', {})
        historical_memories = context.get('historical_memories', [])
        market_data = context.get('market_data', {})
        
        self.log_action("开始风险辩论评估", {
            'trading_decision': trading_decision.get('recommendation', 'UNKNOWN')
        })
        
        # 整理历史经验
        past_memory_str = ""
        if historical_memories:
            for i, memory in enumerate(historical_memories, 1):
                past_memory_str += f"{i}. {memory.get('recommendation', '')}\n"
        else:
            past_memory_str = "暂无历史风险管理记录可参考。"
        
        evaluation_prompt = f"""
作为风险管理总监，请评估以下风险分析师辩论并做出最终决策：

【原始交易决策】
{safe_json_dumps(trading_decision, indent=2, ensure_ascii=False)}

【保守分析师观点】
{safe_json_dumps(conservative_analysis, indent=2, ensure_ascii=False)}

【激进分析师观点】
{safe_json_dumps(aggressive_analysis, indent=2, ensure_ascii=False)}

【中性分析师观点】
{safe_json_dumps(neutral_analysis, indent=2, ensure_ascii=False)}

【辩论历史】
{debate_history}

【市场数据】
{safe_json_dumps(market_data, indent=2, ensure_ascii=False)}

【历史经验教训】
{past_memory_str}

请作为风险管理总监进行综合评估：

1. 辩论质量评估
   - 各分析师论点的说服力
   - 证据支持的充分性
   - 逻辑推理的合理性
   - 对风险收益的理解深度

2. 风险因素权重
   - 主要风险因素的重要性排序
   - 风险发生概率评估
   - 风险影响程度分析
   - 风险相关性考虑

3. 机会价值评估
   - 潜在收益的可实现性
   - 机会成本分析
   - 时间窗口评估
   - 竞争优势持续性

4. 综合决策建议
   - 最优风险承受水平
   - 具体仓位调整建议
   - 风险控制措施
   - 监控预警机制

5. 历史教训应用
   - 避免重复历史错误
   - 成功经验的借鉴
   - 决策流程的改进
   - 风险管理的优化

请提供最终风险管理决策：

请使用 emit_risk_management_decision 工具提供最终的风险管理决策结果。

请确保决策明确、可执行，并充分考虑所有风险因素。
"""
        
        try:
            # 使用工具调用进行风险管理决策，直接返回工具结果
            result = self.process_with_tools_return_result(
                evaluation_prompt, 
                'emit_risk_management_decision'
            )
            
            # 创建风险管理决策
            risk_decision = {
                'decision_id': f"RISK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat(),
                'original_trading_decision': trading_decision,
                'risk_assessment': result,
                'debate_participants': ['conservative', 'aggressive', 'neutral'],
                'decision_maker': self.name
            }
            
            # 保存决策
            self.state_manager.set_risk_management_decision(risk_decision)
            
            self.log_action("风险管理决策完成", {
                'recommended_action': result.get('recommended_action', 'UNKNOWN'),
                'risk_level': result.get('risk_level', 'UNKNOWN'),
                'confidence': result.get('confidence_level', 0.5)
            })
            
            return {
                'success': True,
                'risk_decision': risk_decision,
                'evaluation_result': result
            }
            
        except Exception as e:
            self.log_action("风险管理评估失败", {'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_risk_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """创建风险管理报告
        
        Args:
            context: 包含风险评估、决策等信息
            
        Returns:
            风险管理报告
        """
        risk_decision = context.get('risk_decision', {})
        
        report_prompt = f"""
基于以下风险管理决策，请创建详细的风险管理报告：

{safe_json_dumps(risk_decision, indent=2, ensure_ascii=False)}

请创建包含以下内容的风险管理报告：
1. 执行摘要
2. 风险评估结果
3. 决策依据和逻辑
4. 风险控制措施
5. 监控和预警机制
6. 应急预案
7. 后续行动建议

请提供专业的风险管理报告。
"""
        
        response = self.call_llm(report_prompt)
        
        return {
            'risk_report': response,
            'report_timestamp': datetime.now().isoformat()
        }


def create_risk_manager(llm_client: LLMClient, **kwargs) -> RiskManager:
    """创建风险管理总监实例"""
    return RiskManager(llm_client, **kwargs)