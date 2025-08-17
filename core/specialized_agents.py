"""
专门化智能体类
提供分析师、研究员等专门化的智能体实现
"""
import json
from typing import Dict, List, Any, Optional, Callable

from .agent_base import BaseAgent
from .llm_client import LLMClient
from .state_manager import AgentRole
from utils.logger import get_logger

logger = get_logger()


class AnalystAgent(BaseAgent):
    """分析师智能体基类"""
    
    def __init__(self, role: AgentRole, name: str, llm_client: LLMClient, **kwargs):
        """初始化分析师智能体"""
        system_prompt = f"""你是一个专业的{name}，负责分析股票市场数据并提供深入的见解。

你的职责包括：
1. 收集和分析相关市场数据
2. 识别关键趋势和模式
3. 提供基于数据的见解和建议
4. 生成结构化的分析报告

请保持客观、专业，并基于数据进行分析。你的分析将为后续的投资决策提供重要依据。

输出格式要求：
- 提供清晰的关键发现
- 给出明确的推荐意见
- 包含置信度评分（0-1之间）
- 提供支持数据和证据
"""
        super().__init__(role, name, llm_client, system_prompt, **kwargs)
        logger.info(f"分析师智能体初始化完成: {name}")
    

class ResearcherAgent(BaseAgent):
    """研究员智能体基类"""
    
    def __init__(self, role: AgentRole, name: str, perspective: str, llm_client: LLMClient, **kwargs):
        """初始化研究员智能体
        
        Args:
            perspective: 研究视角（bullish/bearish）
        """
        self.perspective = perspective
        
        system_prompt = f"""你是一个{perspective}研究员，专门从{perspective}角度分析投资机会。

你的职责：
1. 审查分析师报告
2. 从{perspective}角度评估投资机会
3. 参与团队辩论
4. 提供有说服力的论证

请保持你的{perspective}立场，但要基于事实和逻辑进行论证。
在辩论中要尊重对方观点，但坚持用数据和分析支持你的立场。
"""
        super().__init__(role, name, llm_client, system_prompt, **kwargs)
        logger.info(f"研究员智能体初始化完成: {name} ({perspective})")
    
    def debate(self, topic: str, opponent_message: str = "", context: Dict[str, Any] = None) -> str:
        """参与辩论
        
        Args:
            topic: 辩论主题
            opponent_message: 对手消息
            context: 上下文信息
            
        Returns:
            辩论回应
        """
        logger.info(f"[{self.name}] 参与辩论 - 主题: {topic}")
        
        debate_prompt = f"""
辩论主题: {topic}

上下文信息: {json.dumps(context or {}, ensure_ascii=False)}

对手观点: {opponent_message}

请从{self.perspective}角度进行回应，要求：
1. 针对对手观点进行回应
2. 提供强有力的论证
3. 使用数据和事实支持
4. 保持专业和尊重
"""
        
        try:
            response = self.call_llm(debate_prompt)
            
            # 保存研究员的辩论输出到markdown
            if context and context.get('symbol'):
                self.save_output_to_markdown(
                    output=response,
                    ticker=context.get('symbol'),
                    stage="debate",
                    metadata={
                        "agent_role": self.role.value,
                        "perspective": self.perspective,
                        "debate_topic": topic,
                        "opponent_perspective": "对手观点" if opponent_message else "无"
                    }
                )
            
            logger.debug(f"[{self.name}] 辩论回应生成完成")
            return response
        except Exception as e:
            logger.error(f"[{self.name}] 辩论过程发生错误: {str(e)}")
            raise


# 工厂函数
def create_agent(
    agent_type: str,
    role: AgentRole,
    name: str,
    llm_client: LLMClient,
    **kwargs
) -> BaseAgent:
    """创建智能体实例
    
    Args:
        agent_type: 智能体类型 ('analyst', 'researcher', 'trader', 'risk')
        role: 智能体角色
        name: 智能体名称
        llm_client: LLM客户端
        **kwargs: 其他参数
        
    Returns:
        智能体实例
    """
    logger.info(f"创建智能体 - 类型: {agent_type}, 名称: {name}, 角色: {role.value}")
    
    if agent_type == 'analyst':
        return AnalystAgent(role, name, llm_client, **kwargs)
    elif agent_type == 'researcher':
        perspective = kwargs.get('perspective', 'neutral')
        return ResearcherAgent(role, name, perspective, llm_client, **kwargs)
    else:
        return BaseAgent(role, name, llm_client, **kwargs)