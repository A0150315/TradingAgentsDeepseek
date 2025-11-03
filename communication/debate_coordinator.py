"""
辩论协调器
管理研究团队之间的辩论流程，确保充分讨论和决策达成
"""
from typing import Dict, Any, List, Optional
import random
import json
from datetime import datetime

from core.agent_base import BaseAgent
from core.llm_client import LLMClient
from core.state_manager import (
    AgentRole, 
    DebateState, 
    get_state_manager,
    MessageType
)
from agents.researchers import BullResearcher, BearResearcher
from utils.logger import get_logger
from tools.result_emitters import emit_debate_quality_evaluation, emit_debate_judgment

logger = get_logger()


class DebateCoordinator(BaseAgent):
    """辩论协调器"""
    
    def __init__(
        self, 
        bull_researcher: BullResearcher,
        bear_researcher: BearResearcher,
        judge_llm: LLMClient,
        max_rounds: int = 3,
        consensus_threshold: float = 0.6,
        debate_llm_pool: Optional[List[LLMClient]] = None,
        randomize_models: bool = False
    ):
        """初始化辩论协调器
        
        Args:
            bull_researcher: 多头研究员
            bear_researcher: 空头研究员
            judge_llm: 判断LLM客户端
            max_rounds: 最大辩论轮数
            consensus_threshold: 共识阈值
        """
        # 初始化BaseAgent
        tools = [emit_debate_quality_evaluation, emit_debate_judgment]
        super().__init__(
            role=AgentRole.DEBATE_COORDINATOR,
            name="辩论协调器",
            llm_client=judge_llm,
            tools=tools
        )
        
        self.bull_researcher = bull_researcher
        self.bear_researcher = bear_researcher
        self.judge_llm = judge_llm
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        self.state_manager = get_state_manager()
        self.debate_llm_pool = debate_llm_pool or [judge_llm]
        self.randomize_models = randomize_models and len(self.debate_llm_pool) > 1
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理辩论请求（BaseAgent抽象方法实现）
        
        Args:
            context: 包含symbol、analysis_reports、market_context的上下文
            
        Returns:
            辩论结果
        """
        # 委托给conduct_research_debate方法
        symbol = context.get('symbol', '')
        analysis_reports = context.get('analysis_reports', {})
        market_context = context.get('market_context', {})
        
        return self.conduct_research_debate(symbol, analysis_reports, market_context)
    
    def _serialize_analysis_reports(self, analysis_reports: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """将AnalysisReport对象序列化为可JSON化的字典
        
        Args:
            analysis_reports: 包含AnalysisReport对象的字典
            
        Returns:
            序列化后的字典
        """
        serializable_reports = {}
        for analyst_type, report in analysis_reports.items():
            if hasattr(report, 'to_dict'):
                serializable_reports[analyst_type] = report.to_dict()
            else:
                serializable_reports[analyst_type] = report
        return serializable_reports
    
    def _serialize_context_for_debate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """为辩论序列化上下文，处理其中的AnalysisReport对象
        
        Args:
            context: 原始上下文
            
        Returns:
            可序列化的上下文
        """
        safe_context = context.copy()
        if 'analysis_reports' in safe_context:
            safe_context['analysis_reports'] = self._serialize_analysis_reports(safe_context['analysis_reports'])
        return safe_context
    
    def conduct_research_debate(
        self, 
        symbol: str, 
        analysis_reports: Dict[str, Any],
        market_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """进行研究辩论
        
        Args:
            symbol: 股票代码
            analysis_reports: 分析师报告（原始对象）
            market_context: 市场环境
            
        Returns:
            辩论结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        context = {
            'symbol': symbol,
            'analysis_reports': analysis_reports,
            'market_context': market_context or {}
        }
        return self.execute_with_llm_logging(context, self._do_conduct_research_debate)

    def _select_llm_for_researcher(self, researcher: BaseAgent, label: str) -> LLMClient:
        """为研究员选择LLM客户端，支持随机切换"""
        if not self.randomize_models:
            return researcher.llm_client

        selected = random.choice(self.debate_llm_pool)
        if researcher.llm_client is not selected:
            researcher.llm_client = selected
            logger.info(
                f"辩论模型切换 -> {label}: {getattr(selected, 'provider', 'unknown')}/{getattr(selected, 'model', 'unknown')}"
            )
        return selected
    
    def _do_conduct_research_debate(
        self, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """实际的辩论处理逻辑（内部方法）
        
        Args:
            context: 包含symbol、analysis_reports、market_context的上下文
            
        Returns:
            辩论结果
        """
        symbol = context['symbol']
        analysis_reports = context['analysis_reports']
        market_context = context.get('market_context', {})
        print(f"开始 {symbol} 的研究团队辩论...")
        
        # 初始化辩论状态
        debate_state = self.state_manager.start_research_debate(
            participants=[AgentRole.BULL_RESEARCHER, AgentRole.BEAR_RESEARCHER],
            max_rounds=self.max_rounds
        )
        
        context = {
            'symbol': symbol,
            'analysis_reports': analysis_reports,
            'market_context': market_context or {}
        }
        
        # 让双方先进行初始研究
        bull_research = self.bull_researcher.process(context)
        bear_research = self.bear_researcher.process(context)
        
        if not (bull_research['success'] and bear_research['success']):
            return {
                'success': False,
                'error': 'Initial research failed'
            }
        
        # 获取初始立场
        from core.llm_client import safe_json_dumps
        bull_thesis = safe_json_dumps(bull_research['research_result'], indent=2, ensure_ascii=False)
        bear_thesis = safe_json_dumps(bear_research['research_result'], indent=2, ensure_ascii=False)
        
        topic = f"是否应该投资股票 {symbol}"
        
        # 进行多轮辩论
        debate_history = []
        
        for round_num in range(self.max_rounds):
            print(f"辩论第 {round_num + 1} 轮:")
            
            # 多头发言
            opponent_msg = debate_history[-1]['message'] if debate_history and debate_history[-1]['speaker'] == 'bear' else bear_thesis
            bull_llm = self._select_llm_for_researcher(self.bull_researcher, 'bull')
            # 序列化context以避免JSON序列化错误
            safe_context = self._serialize_context_for_debate(context)
            bull_response = self.bull_researcher.debate(
                topic=topic,
                opponent_message=opponent_msg,
                context=safe_context
            )
            
            debate_history.append({
                'round': round_num + 1,
                'speaker': 'bull',
                'message': bull_response,
                'timestamp': datetime.now().isoformat(),
                'model': getattr(bull_llm, 'model', None),
                'provider': getattr(bull_llm, 'provider', None)
            })
            
            print(
                f"  多头[{getattr(bull_llm, 'provider', 'unknown')}/{getattr(bull_llm, 'model', 'unknown')}]: {bull_response[:200]}..."
            )
            
            # 空头回应
            bear_llm = self._select_llm_for_researcher(self.bear_researcher, 'bear')
            safe_context = self._serialize_context_for_debate(context)
            bear_response = self.bear_researcher.debate(
                topic=topic,
                opponent_message=bull_response,
                context=safe_context
            )
            
            debate_history.append({
                'round': round_num + 1,
                'speaker': 'bear', 
                'message': bear_response,
                'timestamp': datetime.now().isoformat(),
                'model': getattr(bear_llm, 'model', None),
                'provider': getattr(bear_llm, 'provider', None)
            })
            
            print(
                f"  空头[{getattr(bear_llm, 'provider', 'unknown')}/{getattr(bear_llm, 'model', 'unknown')}]: {bear_response[:200]}..."
            )
            
            # 检查是否应该提前结束辩论（可选功能）
            # 这里可以添加收敛条件检查
        
        
        # 判断辩论结果
        debate_result = self._judge_debate(
            symbol=symbol,
            bull_thesis=bull_thesis,
            bear_thesis=bear_thesis,
            debate_history=debate_history,
            analysis_reports=analysis_reports
        )
        
        # 更新辩论状态
        debate_state.consensus_reached = True
        debate_state.final_decision = debate_result['decision']
        
        print(f"辩论结论: {debate_result['decision']}")
        print(f"决策置信度: {debate_result['confidence']}")
        
        return {
            'success': True,
            'debate_result': debate_result,
            'debate_history': debate_history,
            'bull_research': bull_research,
            'bear_research': bear_research
        }
    
    def _judge_debate(
        self,
        symbol: str,
        bull_thesis: str,
        bear_thesis: str,
        debate_history: List[Dict[str, Any]],
        analysis_reports: Dict[str, Any]
    ) -> Dict[str, Any]:
        """判断辩论结果
        
        Args:
            symbol: 股票代码
            bull_thesis: 多头观点
            bear_thesis: 空头观点
            debate_history: 辩论历史
            analysis_reports: 分析报告（原始对象）
            
        Returns:
            判断结果
        """
        # 构建判断历史文本
        history_text = "\n\n".join([
            f"第{item['round']}轮 - {item['speaker']}: {item['message']}"
            for item in debate_history
        ])
        
        # 使用统一的序列化方法
        formatted_reports = self._serialize_analysis_reports(analysis_reports)
        
        judge_prompt = f"""
作为专业的投资决策判官，请基于以下信息对股票 {symbol} 的投资决策进行最终判断：

分析师报告摘要：
{json.dumps(formatted_reports, indent=2, ensure_ascii=False)}

多头观点：
{bull_thesis}

空头观点：
{bear_thesis}

辩论过程：
{history_text}

请进行综合评估并做出最终决策：

1. 评估双方论证的质量和说服力
2. 考虑分析师报告的客观数据
3. 权衡投资机会和风险
4. 考虑市场时机和环境因素
5. 做出平衡的投资建议

请使用 emit_debate_judgment 工具提供最终的辩论判断结果。
"""
        
        try:
            # 使用工具调用进行辩论判断，直接返回工具结果
            result = self.process_with_tools_return_result(
                judge_prompt, 
                'emit_debate_judgment'
            )
            
        except Exception as e:
            # 如果解析失败，提供默认判断
            print(f"判断解析失败，使用默认逻辑: {e}")
            logger.error(f"辩论判断失败: {str(e)}")
            result = self._default_judgment(analysis_reports)
        
        return result
    
    def _default_judgment(self, analysis_reports: Dict[str, Any]) -> Dict[str, Any]:
        """默认判断逻辑（当LLM判断失败时使用）"""
        
        # 简单的评分逻辑
        buy_signals = 0
        sell_signals = 0
        total_confidence = 0
        
        for _, report in analysis_reports.items():
            if not report:
                continue
                
            recommendation = report.get('recommendation', 'HOLD')
            confidence = report.get('confidence_score', 0.5)
            
            if recommendation == 'BUY':
                buy_signals += confidence
            elif recommendation == 'SELL':
                sell_signals += confidence
            
            total_confidence += confidence
        
        avg_confidence = total_confidence / len(analysis_reports) if analysis_reports else 0.5
        
        if buy_signals > sell_signals:
            decision = 'BUY'
            winner = 'bull'
        elif sell_signals > buy_signals:
            decision = 'SELL'  
            winner = 'bear'
        else:
            decision = 'HOLD'
            winner = 'draw'
        
        return {
            'decision': decision,
            'confidence': min(avg_confidence, 0.8),
            'reasoning': f'基于分析师报告的综合评估，买入信号{buy_signals:.2f}，卖出信号{sell_signals:.2f}',
            'supporting_factors': ['分析师报告综合评估'],
            'risk_factors': ['市场波动风险'],
            'investment_strategy': '谨慎投资，密切关注市场变化',
            'winner': winner,
            'winning_arguments': ['数据支持的客观分析']
        }
    
    def evaluate_debate_quality(self, debate_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估辩论质量
        
        Args:
            debate_history: 辩论历史
            
        Returns:
            质量评分
        """
        if not debate_history:
            return {
                'debate_quality': '较差',
                'quality_score': 0.0,
                'argument_strengths': {'bull': '无辩论', 'bear': '无辩论'},
                'key_insights': [],
                'consensus_level': '无共识',
                'decision_confidence': 0.0,
                'evaluation_summary': '空辩论历史，无法评估质量'
            }
        
        quality_prompt = f"""
请评估以下辩论的质量：

{json.dumps(debate_history, indent=2, ensure_ascii=False)}

请从以下角度进行评估：

1. 辩论质量评级
   - 论证逻辑性
   - 数据支撑度
   - 观点清晰度
   - 反驳有效性
   - 专业水准

2. 论证强度分析
   - 多头论证强度和优劣势
   - 空头论证强度和优劣势

3. 关键洞察
   - 辩论中揭示的重要问题
   - 新的视角和观点

4. 共识水平
   - 评估双方在哪些问题上有共识
   - 分歧的主要领域

5. 决策置信度
   - 基于辩论质量的决策可靠性

请使用 emit_debate_quality_evaluation 工具返回最终的辩论质量评估结果。
"""
        
        try:
            # 使用工具调用进行辩论质量评估，直接返回工具结果
            result = self.process_with_tools_return_result(
                quality_prompt, 
                'emit_debate_quality_evaluation'
            )
            return result
        except Exception as e:
            logger.error(f"辩论质量评估失败: {str(e)}")
            return {
                'debate_quality': '较差',
                'quality_score': 0.5,
                'argument_strengths': {'bull': '评估失败', 'bear': '评估失败'},
                'key_insights': ['评估过程中发生错误'],
                'consensus_level': '不明',
                'decision_confidence': 0.5,
                'evaluation_summary': f'评估失败: {str(e)}'
            }


def create_debate_coordinator(
    bull_researcher: BullResearcher,
    bear_researcher: BearResearcher,
    judge_llm: LLMClient,
    **kwargs
) -> DebateCoordinator:
    """创建辩论协调器实例"""
    return DebateCoordinator(
        bull_researcher=bull_researcher,
        bear_researcher=bear_researcher,
        judge_llm=judge_llm,
        **kwargs
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # 创建测试用的模拟数据
    test_analysis_reports = {
        'fundamental': {
            'recommendation': 'BUY',
            'confidence_score': 0.8,
            'key_findings': ['强劲财报', '估值合理', '增长前景良好'],
            'target_price': 200.0,
            'pe_ratio': 25.5,
            'revenue_growth': 0.12
        },
        'technical': {
            'recommendation': 'HOLD', 
            'confidence_score': 0.6,
            'key_findings': ['技术指标中性', 'RSI偏高'],
            'target_price': 185.0,
            'trend_direction': '横盘',
            'support_level': 170.0,
            'resistance_level': 190.0
        },
        'sentiment': {
            'sentiment_level': '乐观',
            'confidence_score': 0.7,
            'key_findings': ['市场情绪积极', '机构增持'],
            'social_sentiment_score': 0.75,
            'institutional_sentiment': '买入'
        }
    }
    
    test_market_context = {
        'market_trend': '上涨',
        'volatility': '中等',
        'economic_indicators': {
            'gdp_growth': 2.1,
            'inflation': 3.2,
            'interest_rate': 5.25
        },
        'sector_performance': '科技股领涨',
        'market_cap': 3000000000000  # 3万亿
    }
    
    print("🔥 开始测试辩论协调器逻辑...")
    print("=" * 50)
    print(f"📱 测试股票: AAPL")
    print(f"📊 模拟分析报告: {len(test_analysis_reports)} 个")
    print(f"🌍 市场环境: {test_market_context['market_trend']}")
    
    try:
        # 创建LLM客户端和组件
        from core.llm_client import LLMClient
        from agents.researchers import create_bull_researcher, create_bear_researcher
        from core.state_manager import get_state_manager
        
        llm_client = LLMClient(provider='deepseek')
        bull_researcher = create_bull_researcher(llm_client)
        bear_researcher = create_bear_researcher(llm_client)
        
        # 创建辩论协调器 - 设置2轮便于验证
        coordinator = create_debate_coordinator(
            bull_researcher=bull_researcher,
            bear_researcher=bear_researcher,
            judge_llm=llm_client,
            max_rounds=2  # 2轮 = 4次发言 (bull->bear->bull->bear)
        )
        
        print(f"📋 辩论设置: {coordinator.max_rounds} 轮完整辩论")
        print(f"🎯 预期发言: {coordinator.max_rounds * 2} 次 (每轮Bull+Bear各1次)")
        
        # 启动session - 这是必需的！
        state_manager = get_state_manager()
        session_id = state_manager.start_session('AAPL')
        print(f"📝 启动测试会话: {session_id}")
        
        try:
            # 执行辩论
            result = coordinator.conduct_research_debate(
                symbol='AAPL',
                analysis_reports=test_analysis_reports,
                market_context=test_market_context
            )
            
            if result['success']:
                print("\n✅ 辩论成功完成!")
                
                # 验证发言次数和轮次逻辑
                debate_history = result['debate_history']
                actual_speeches = len(debate_history)
                expected_speeches = coordinator.max_rounds * 2
                
                print(f"\n📊 辩论统计:")
                print(f"  实际发言次数: {actual_speeches}")
                print(f"  预期发言次数: {expected_speeches}")
                print(f"  逻辑正确性: {'✅ 正确' if actual_speeches == expected_speeches else '❌ 错误'}")
                
                # 显示发言顺序
                print(f"\n📢 发言序列验证:")
                for i, entry in enumerate(debate_history):
                    expected = 'bull' if i % 2 == 0 else 'bear'
                    actual = entry['speaker']
                    status = '✅' if expected == actual else '❌'
                    print(f"  第{i+1}次: 预期{expected} 实际{actual} {status} (第{entry['round']}轮)")
                
                # 显示最终结果
                debate_result = result['debate_result']
                print(f"\n🏆 辩论结果:")
                print(f"  最终决策: {debate_result.get('decision', 'N/A')}")
                print(f"  置信度: {debate_result.get('confidence', 0.0):.2f}")
                
            else:
                print(f"❌ 辩论失败: {result.get('error')}")
                
        finally:
            # 确保结束session
            state_manager.end_session()
            print(f"📝 结束测试会话")
            
    except Exception as e:
        print(f"💥 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()