"""
多头研究员Agent
从看涨角度分析投资机会，在团队辩论中支持买入立场
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
import json

from core.specialized_agents import ResearcherAgent
from core.llm_client import LLMClient
from core.state_manager import AgentRole, AnalysisReport
from tools.result_emitters import emit_bull_research_result


class BullResearcher(ResearcherAgent):
    """多头研究员"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [emit_bull_research_result]
        
        super().__init__(
            role=AgentRole.BULL_RESEARCHER,
            name="多头研究员",
            perspective="多头",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        
        # 增强系统提示
        self.system_prompt += f"""

作为多头研究员，你的特殊职责：
1. 从乐观角度解读分析师报告
2. 寻找和强调投资机会
3. 评估增长潜力和正面催化剂
4. 在辩论中提供有力的买入论证
5. 识别被低估的价值

辩论策略：
- 使用具体数据支持你的论点
- 关注长期增长前景
- 强调公司竞争优势
- 指出市场机会和行业趋势
- 反驳空头观点的局限性

保持专业、客观，但要坚定地支持你的多头立场。
"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理多头研究请求
        
        Args:
            context: 包含分析报告、市场数据等信息
                - symbol: str - 股票代码
                - analysis_reports: Dict[str, AnalysisReport] - 分析师报告对象
                - market_context: Dict[str, Any] - 市场环境信息
            
        Returns:
            多头分析结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_process)
    
    def _do_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的处理逻辑（内部方法）
        
        Args:
            context: 包含分析报告、市场数据等信息
                - symbol: str - 股票代码
                - analysis_reports: Dict[str, AnalysisReport] - 分析师报告对象
                - market_context: Dict[str, Any] - 市场环境信息
            
        Returns:
            多头分析结果
        """
        symbol: str = context.get('symbol', '')
        analysis_reports: Dict[str, AnalysisReport] = context.get('analysis_reports', {})
        market_context: Dict[str, Any] = context.get('market_context', {})
        
        self.log_action("开始多头研究", {'symbol': symbol})
        
        # 将AnalysisReport对象转换为可序列化的字典
        serializable_reports: Dict[str, Dict[str, Any]] = {}
        for analyst_type, report in analysis_reports.items():
            serializable_reports[analyst_type] = report.to_dict()
        
        # 构建多头分析提示，LLM会自动知道有哪些工具可用
        research_prompt = f"""
作为多头研究员，请基于以下信息对股票 {symbol} 进行投资机会分析：

分析师报告：
{json.dumps(serializable_reports, indent=2, ensure_ascii=False)}

市场环境：
{json.dumps(market_context, indent=2, ensure_ascii=False)}

请从多头角度进行深入分析：

1. 投资亮点识别
   - 基本面优势
   - 技术面机会
   - 情绪面转机
   - 新闻面催化剂

2. 增长潜力评估
   - 收入增长驱动因素
   - 盈利能力改善空间
   - 市场份额扩张机会
   - 新产品/服务前景

3. 估值吸引力
   - 相对估值优势
   - 历史估值比较
   - 同行业对比
   - 成长性vs估值匹配度

4. 风险缓释因素
   - 管理层执行力
   - 财务稳健性
   - 行业地位稳固性
   - 多元化经营优势

5. 催化剂事件
   - 近期正面事件
   - 预期改善因素
   - 政策利好
   - 行业拐点

请使用 emit_bull_research_result 工具提供最终的多头研究结果。
"""
        
        try:
            # 使用工具调用进行多头研究，直接返回工具结果
            result = self.process_with_tools_return_result(
                research_prompt, 
                'emit_bull_research_result'
            )
            
            self.log_action("多头研究完成", {
                'target_price': result.get('target_price'),
                'upside_potential': result.get('upside_potential'),
                'confidence': result.get('confidence_level')
            })
            
            return {
                'success': True,
                'research_result': result,
                'perspective': 'bull'
            }
            
        except Exception as e:
            self.log_action("多头研究失败", {'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }
    
    def debate(self, topic: str, opponent_message: str = "", context: Dict[str, Any] = None) -> str:
        """参与辩论（多头角度）
        
        Args:
            topic: 辩论主题
            opponent_message: 对手消息
            context: 上下文信息
            
        Returns:
            辩论回应
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_debate_with_llm_logging(topic, opponent_message, context or {}, self._do_debate)
    
    def _do_debate(self, topic: str, opponent_message: str, context: Dict[str, Any]) -> str:
        """实际的辩论逻辑（内部方法）
        
        Args:
            topic: 辩论主题
            opponent_message: 对手消息
            context: 上下文信息
            
        Returns:
            辩论回应
        """
        debate_prompt = f"""
辩论主题: {topic}

对手（空头）观点: {opponent_message}

上下文信息: {json.dumps(context or {}, ensure_ascii=False)}

作为多头研究员，请针对空头观点进行有力反驳：

1. 指出空头观点的局限性或片面性
2. 提供支持多头立场的新数据或角度
3. 强调长期价值和增长潜力
4. 识别市场机会和正面催化剂
5. 保持专业但坚定的立场

请提供具有说服力的多头论证，要求：
- 使用具体数据和事实
- 逻辑清晰、条理分明
- 针对性回应对手观点
- 突出投资机会
"""
        
        response = self.call_llm(debate_prompt)
        
        # 记录辩论消息
        self.state_manager.add_debate_message(
            'research', 
            self.role, 
            response,
            {'topic': topic, 'opponent_message': opponent_message}
        )
        
        return response
    
def create_bull_researcher(llm_client: LLMClient, **kwargs) -> BullResearcher:
    """创建多头研究员实例"""
    return BullResearcher(llm_client, **kwargs)