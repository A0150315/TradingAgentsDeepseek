"""
空头研究员Agent
从看跌角度分析投资风险，在团队辩论中支持卖出立场
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any
import json

from core.specialized_agents import ResearcherAgent
from core.llm_client import LLMClient
from core.state_manager import AgentRole, AnalysisReport
from tools.result_emitters import emit_bear_research_result


class BearResearcher(ResearcherAgent):
    """空头研究员"""
    
    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [emit_bear_research_result]
        
        super().__init__(
            role=AgentRole.BEAR_RESEARCHER,
            name="空头研究员",
            perspective="空头",
            llm_client=llm_client,
            tools=tools,
            **kwargs
        )
        
        # 增强系统提示
        self.system_prompt += f"""

作为空头研究员，你的特殊职责：
1. 从谨慎角度解读分析师报告
2. 识别和强调投资风险
3. 评估下行风险和负面催化剂
4. 在辩论中提供有力的风险警示
5. 发现被高估的风险

辩论策略：
- 使用具体数据突出风险点
- 关注短中期风险因素
- 强调竞争劣势和威胁
- 指出市场风险和行业挑战
- 质疑多头观点的盲点

保持专业、客观，但要坚定地警示投资风险。
"""
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理空头研究请求
        
        Args:
            context: 包含分析报告、市场数据等信息
                - symbol: str - 股票代码
                - analysis_reports: Dict[str, AnalysisReport] - 分析师报告对象
                - market_context: Dict[str, Any] - 市场环境信息
            
        Returns:
            空头分析结果
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
            空头分析结果
        """
        symbol: str = context.get('symbol', '')
        analysis_reports: Dict[str, AnalysisReport] = context.get('analysis_reports', {})
        market_context: Dict[str, Any] = context.get('market_context', {})
        
        self.log_action("开始空头研究", {'symbol': symbol})
        
        # 将AnalysisReport对象转换为可序列化的字典
        serializable_reports: Dict[str, Dict[str, Any]] = {}
        for analyst_type, report in analysis_reports.items():
            serializable_reports[analyst_type] = report.to_dict()
        
        # 构建空头分析提示，LLM会自动知道有哪些工具可用
        research_prompt = f"""
作为空头研究员，请基于以下信息对股票 {symbol} 进行风险分析：

分析师报告：
{json.dumps(serializable_reports, indent=2, ensure_ascii=False)}

市场环境：
{json.dumps(market_context, indent=2, ensure_ascii=False)}

请从空头角度进行深入的风险分析：

1. 风险因素识别
   - 基本面风险点
   - 技术面风险信号
   - 情绪面泡沫迹象
   - 新闻面负面因素

2. 下行风险评估
   - 收入下滑风险
   - 盈利能力恶化风险
   - 市场份额流失风险
   - 估值回归风险

3. 估值风险分析
   - 相对估值过高
   - 历史估值偏离
   - 同行业比较劣势
   - 成长性与估值不匹配

4. 结构性问题
   - 商业模式缺陷
   - 管理层问题
   - 财务风险
   - 竞争地位弱化

5. 负面催化剂
   - 近期风险事件
   - 预期恶化因素
   - 政策不利
   - 行业逆风

请使用 emit_bear_research_result 工具提供最终的空头风险研究结果。
"""
        
        try:
            # 使用工具调用进行空头研究，直接返回工具结果
            result = self.process_with_tools_return_result(
                research_prompt, 
                'emit_bear_research_result'
            )
            
            self.log_action("空头研究完成", {
                'target_price': result.get('target_price'),
                'downside_risk': result.get('downside_risk'),
                'confidence': result.get('confidence_level')
            })
            
            return {
                'success': True,
                'research_result': result,
                'perspective': 'bear'
            }
            
        except Exception as e:
            self.log_action("空头研究失败", {'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }
    
    def debate(self, topic: str, opponent_message: str = "", context: Dict[str, Any] = None) -> str:
        """参与辩论（空头角度）
        
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

对手（多头）观点: {opponent_message}

上下文信息: {json.dumps(context or {}, ensure_ascii=False)}

作为空头研究员，请针对多头观点进行风险警示：

1. 指出多头观点忽视的风险因素
2. 提供支持空头立场的风险证据
3. 强调短中期下行风险
4. 识别负面催化剂和结构性问题
5. 保持专业但谨慎的立场

请提供具有说服力的风险分析，要求：
- 使用具体数据和风险案例
- 逻辑清晰、风险导向
- 针对性质疑多头观点
- 突出投资风险
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
    
def create_bear_researcher(llm_client: LLMClient, **kwargs) -> BearResearcher:
    """创建空头研究员实例"""
    return BearResearcher(llm_client, **kwargs)