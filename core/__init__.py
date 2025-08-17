"""
TradingAgents OpenAI Framework
基于OpenAI原生库的多智能体股票交易框架
"""

__version__ = "0.1.0"
__author__ = "TradingAgents Team"

from .config import Config, get_config, set_config
from .state_manager import (
    StateManager, 
    AgentRole, 
    MessageType, 
    Message,
    AnalysisReport,
    DebateState,
    TradingSession,
    get_state_manager
)
from .agent_base import BaseAgent
from .specialized_agents import AnalystAgent, ResearcherAgent, create_agent
from .llm_client import LLMClient, create_llm_client
from .tool_manager import ToolManager
from .conversation_manager import ConversationManager
# 暂时注释掉workflow导入以解决循环导入问题
# from .workflow import WorkflowOrchestrator, create_workflow_orchestrator

__all__ = [
    'Config',
    'get_config', 
    'set_config',
    'StateManager',
    'AgentRole',
    'MessageType',
    'Message',
    'AnalysisReport',
    'DebateState', 
    'TradingSession',
    'get_state_manager',
    'BaseAgent',
    'AnalystAgent',
    'ResearcherAgent', 
    'LLMClient',
    'create_llm_client',
    'ToolManager',
    'ConversationManager',
    'create_agent'
    # 暂时注释掉workflow
    # 'WorkflowOrchestrator',
    # 'create_workflow_orchestrator'
]