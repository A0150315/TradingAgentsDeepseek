"""
风险辩论协调器
管理风险管理团队的辩论流程
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from core.llm_client import LLMClient, safe_json_dumps
from core.state_manager import get_state_manager, DebateState, AgentRole
from .conservative_analyst import ConservativeAnalyst
from .aggressive_analyst import AggressiveAnalyst
from .neutral_analyst import NeutralAnalyst
from .risk_manager import RiskManager


class RiskDebateCoordinator:
    """风险辩论协调器"""
    
    def __init__(
        self,
        conservative_analyst: ConservativeAnalyst,
        aggressive_analyst: AggressiveAnalyst,
        neutral_analyst: NeutralAnalyst,
        risk_manager: RiskManager,
        llm_client: LLMClient,
        max_rounds: int = 3
    ):
        self.conservative_analyst = conservative_analyst
        self.aggressive_analyst = aggressive_analyst
        self.neutral_analyst = neutral_analyst
        self.risk_manager = risk_manager
        self.llm_client = llm_client
        self.max_rounds = max_rounds
        self.state_manager = get_state_manager()
        
        print(f"风险辩论协调器初始化完成，最大轮数：{max_rounds}")
    
    def conduct_risk_debate(
        self,
        trading_decision: Any,
        market_data: Dict[str, Any],
        analysis_reports: Dict[str, Any],
        historical_memories: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """开展风险管理辩论
        
        Args:
            trading_decision: 交易决策（原始对象）
            market_data: 市场数据
            analysis_reports: 分析师报告（原始对象）
            historical_memories: 历史记忆
            
        Returns:
            辩论结果
        """
        # 处理 trading_decision 的格式转换
        if hasattr(trading_decision, '__dict__'):
            decision_dict = trading_decision.__dict__
        elif hasattr(trading_decision, 'to_dict'):
            decision_dict = trading_decision.to_dict()
        else:
            decision_dict = trading_decision
            
        print(f"\\n🎯 开始风险管理辩论：{decision_dict.get('symbol', 'UNKNOWN')}")
        
        # 初始化辩论状态
        debate_state = DebateState(
            participants=[
                AgentRole.SAFE_ANALYST,
                AgentRole.RISKY_ANALYST,
                AgentRole.NEUTRAL_ANALYST
            ],
            current_round=0,
            max_rounds=self.max_rounds,
            topic=f"交易决策风险评估: {decision_dict.get('recommendation', decision_dict.get('symbol', 'UNKNOWN'))}"
        )
        
        # 创建分析上下文
        analysis_context = {
            'trading_decision': decision_dict,
            'market_data': market_data,
            'analysis_reports': analysis_reports,
            'historical_memories': historical_memories or []
        }
        
        try:
            # 第一阶段：独立分析
            print("  📊 第一阶段：独立风险分析")
            conservative_analysis = self.conservative_analyst.analyze_risks(analysis_context)
            aggressive_analysis = self.aggressive_analyst.analyze_opportunities(analysis_context)
            neutral_analysis = self.neutral_analyst.analyze_balance({
                **analysis_context,
                'conservative_analysis': conservative_analysis.get('analysis_result', {}),
                'aggressive_analysis': aggressive_analysis.get('analysis_result', {})
            })
            
            # 第二阶段：辩论轮次
            print("  💬 第二阶段：风险辩论")
            debate_history = []
            
            for round_num in range(1, self.max_rounds + 1):
                print(f"    🔄 辩论轮次 {round_num}/{self.max_rounds}")
                
                # 保守分析师发言 - 获取所有已有的对手发言
                opponent_args = self._get_opponent_arguments('conservative', debate_history, round_num,
                                                          conservative_analysis, aggressive_analysis, neutral_analysis)
                
                conservative_response = self.conservative_analyst.debate_response(
                    debate_state.topic,
                    opponent_args,
                    analysis_context
                )
                
                # 添加到结构化历史
                debate_history.append({
                    'round': round_num,
                    'speaker': 'conservative',
                    'speaker_name': '保守分析师',
                    'content': conservative_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 激进分析师发言 - 获取所有已有的对手发言（包括刚才保守分析师的发言）
                opponent_args = self._get_opponent_arguments('aggressive', debate_history, round_num,
                                                          conservative_analysis, aggressive_analysis, neutral_analysis)
                
                aggressive_response = self.aggressive_analyst.debate_response(
                    debate_state.topic,
                    opponent_args,
                    analysis_context
                )
                
                # 添加到结构化历史
                debate_history.append({
                    'round': round_num,
                    'speaker': 'aggressive',
                    'speaker_name': '激进分析师',
                    'content': aggressive_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 中性分析师发言 - 获取所有已有的对手发言（包括前两位分析师的发言）
                opponent_args = self._get_opponent_arguments('neutral', debate_history, round_num,
                                                          conservative_analysis, aggressive_analysis, neutral_analysis)
                
                neutral_response = self.neutral_analyst.debate_response(
                    debate_state.topic,
                    opponent_args,
                    analysis_context
                )
                
                # 添加到结构化历史
                debate_history.append({
                    'round': round_num,
                    'speaker': 'neutral',
                    'speaker_name': '中性分析师', 
                    'content': neutral_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 检查是否需要继续辩论
                if self._should_end_debate(debate_history, round_num):
                    print(f"    ✅ 辩论在第{round_num}轮后结束")
                    break
            
            # 第三阶段：风险管理决策
            print("  📋 第三阶段：风险管理决策")
            final_decision = self.risk_manager.evaluate_risk_debate({
                'debate_history': debate_history,
                'trading_decision': decision_dict,
                'conservative_analysis': conservative_analysis.get('analysis_result', {}),
                'aggressive_analysis': aggressive_analysis.get('analysis_result', {}),
                'neutral_analysis': neutral_analysis.get('analysis_result', {}),
                'historical_memories': historical_memories or [],
                'market_data': market_data
            })
            
            # 更新辩论状态
            debate_state.current_round = round_num
            debate_state.is_concluded = True
            debate_state.conclusion = final_decision.get('evaluation_result', {}).get('decision_rationale', '')
            
            # 保存辩论状态
            self.state_manager.current_session.risk_debate = debate_state
            
            print("  ✅ 风险管理辩论完成")
            
            return {
                'success': True,
                'debate_type': 'risk_management',
                'topic': debate_state.topic,
                'rounds_completed': round_num,
                'debate_history': debate_history,
                'conservative_analysis': conservative_analysis,
                'aggressive_analysis': aggressive_analysis,
                'neutral_analysis': neutral_analysis,
                'final_decision': final_decision,
                'risk_assessment': final_decision.get('evaluation_result', {}),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ❌ 风险辩论失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'debate_type': 'risk_management'
            }
    
    def _get_opponent_arguments(self, current_speaker: str, debate_history: List[Dict], current_round: int,
                              conservative_analysis: Dict, aggressive_analysis: Dict, neutral_analysis: Dict) -> List[str]:
        """获取对手论点，按照辩论的时间顺序组织
        
        Args:
            current_speaker: 当前发言者类型（conservative/aggressive/neutral）
            debate_history: 辩论历史记录
            current_round: 当前轮次
            conservative_analysis: 保守分析结果
            aggressive_analysis: 激进分析结果 
            neutral_analysis: 中性分析结果
            
        Returns:
            对手论点列表，按时间顺序
        """
        arguments = []
        
        # 如果是第一轮且没有辩论历史，使用初始分析结果
        if current_round == 1 and not debate_history:
            if current_speaker == 'conservative':
                # 保守分析师看到激进和中性的初始分析
                arguments = [
                    f"激进观点（初始分析）: {safe_json_dumps(aggressive_analysis.get('analysis_result', {}), ensure_ascii=False)}",
                    f"中性观点（初始分析）: {safe_json_dumps(neutral_analysis.get('analysis_result', {}), ensure_ascii=False)}"
                ]
            elif current_speaker == 'aggressive':
                # 激进分析师看到保守的初始分析和第一轮发言，以及中性的初始分析
                if debate_history:
                    # 获取保守分析师刚才的发言（如果有的话）
                    conservative_entries = [entry for entry in debate_history if entry['speaker'] == 'conservative']
                    if conservative_entries:
                        arguments.append(f"保守观点（第{conservative_entries[-1]['round']}轮）：{conservative_entries[-1]['content']}")
                    else:
                        arguments.append(f"保守观点（初始分析）: {safe_json_dumps(conservative_analysis.get('analysis_result', {}), ensure_ascii=False)}")
                else:
                    arguments.append(f"保守观点（初始分析）: {safe_json_dumps(conservative_analysis.get('analysis_result', {}), ensure_ascii=False)}")
                
                arguments.append(f"中性观点（初始分析）: {safe_json_dumps(neutral_analysis.get('analysis_result', {}), ensure_ascii=False)}")
            elif current_speaker == 'neutral':
                # 中性分析师看到保守和激进的最新发言
                if debate_history:
                    # 按时间顺序获取保守和激进的最新发言
                    for entry in debate_history:
                        if entry['speaker'] in ['conservative', 'aggressive']:
                            arguments.append(f"{entry['speaker_name']}（第{entry['round']}轮）：{entry['content']}")
                else:
                    # 如果没有辩论历史，使用初始分析
                    arguments = [
                        f"保守观点（初始分析）: {safe_json_dumps(conservative_analysis.get('analysis_result', {}), ensure_ascii=False)}",
                        f"激进观点（初始分析）: {safe_json_dumps(aggressive_analysis.get('analysis_result', {}), ensure_ascii=False)}"
                    ]
        else:
            # 非第一轮，获取所有对手的历史发言，按时间顺序
            for entry in debate_history:
                if entry['speaker'] != current_speaker:
                    arguments.append(f"{entry['speaker_name']}（第{entry['round']}轮）：{entry['content']}")
        
        return arguments
    
    def _get_recent_arguments(self, analyst_type: str, debate_history: List[Dict]) -> List[str]:
        """获取指定分析师的所有论点"""
        arguments = []
        
        for entry in debate_history:
            if entry['speaker'] == analyst_type:
                arguments.append(f"{entry['speaker_name']}（轮次{entry['round']}）：{entry['content']}")
        
        return arguments
    
    def _should_end_debate(self, debate_history: List[Dict], current_round: int) -> bool:
        """判断是否应该结束辩论"""
        # 如果达到最大轮数，结束辩论
        if current_round >= self.max_rounds:
            return True
        
        # 如果辩论历史过短，继续辩论
        total_content_length = sum(len(entry['content']) for entry in debate_history)
        if total_content_length < 500:
            return False
        
        # 简单的共识检测（可以进一步优化）
        if len(debate_history) >= 6:  # 至少有6条发言
            recent_entries = debate_history[-6:]  # 最近的6条发言
            recent_content = ' '.join([entry['content'] for entry in recent_entries])
            
            # 检查是否有重复的观点
            if self._detect_repetition(recent_content):
                return True
        
        return False
    
    def _detect_repetition(self, text: str) -> bool:
        """检测观点重复"""
        # 简单的重复检测逻辑
        lines = text.split('\\n')
        recent_lines = [line.strip() for line in lines[-6:] if line.strip()]
        
        # 如果最近的发言中有很多相似的关键词，可能是重复
        keywords = ['风险', '收益', '建议', '认为', '应该']
        keyword_counts = {}
        
        for line in recent_lines:
            for keyword in keywords:
                if keyword in line:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # 如果某个关键词出现次数过多，可能是重复
        max_count = max(keyword_counts.values()) if keyword_counts else 0
        return max_count > 3
    
    def generate_risk_summary(self, debate_result: Dict[str, Any]) -> str:
        """生成风险辩论摘要"""
        summary_prompt = f"""
请为以下风险管理辩论生成简洁的摘要：

辩论主题：{debate_result.get('topic', '')}
辩论轮数：{debate_result.get('rounds_completed', 0)}

保守分析师观点：
{safe_json_dumps(debate_result.get('conservative_analysis', {}), ensure_ascii=False)}

激进分析师观点：
{safe_json_dumps(debate_result.get('aggressive_analysis', {}), ensure_ascii=False)}

中性分析师观点：
{safe_json_dumps(debate_result.get('neutral_analysis', {}), ensure_ascii=False)}

最终决策：
{safe_json_dumps(debate_result.get('final_decision', {}), ensure_ascii=False)}

请生成一个简洁的摘要，包括：
1. 主要争议点
2. 各方核心观点
3. 最终决策理由
4. 关键风险因素
"""
        
        response = self.llm_client.chat_completion(
            messages=[{"role": "user", "content": summary_prompt}],
            agent_name="风险辩论协调器"
        )
        return response


def create_risk_debate_coordinator(
    conservative_analyst: ConservativeAnalyst,
    aggressive_analyst: AggressiveAnalyst,
    neutral_analyst: NeutralAnalyst,
    risk_manager: RiskManager,
    llm_client: LLMClient,
    max_rounds: int = 3
) -> RiskDebateCoordinator:
    """创建风险辩论协调器实例"""
    return RiskDebateCoordinator(
        conservative_analyst,
        aggressive_analyst,
        neutral_analyst,
        risk_manager,
        llm_client,
        max_rounds
    )