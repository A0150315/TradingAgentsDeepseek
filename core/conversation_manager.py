"""
对话管理模块
提供对话历史管理、LLM调用链路记录等功能
"""
import time
import uuid
from typing import Dict, List, Any, Optional
from utils.logger import get_logger

logger = get_logger()


class ConversationManager:
    """对话管理器，负责管理对话历史和LLM调用链路"""
    
    def __init__(self, agent_name: str):
        """初始化对话管理器
        
        Args:
            agent_name: 智能体名称
        """
        self.agent_name = agent_name
        
        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []
        
        # LLM调用链路收集（用于调试和日志记录）
        self.llm_call_chain: List[Dict[str, Any]] = []
        self.current_ticker: str = ""  # 当前处理的ticker
        
        # 对话管理
        self.conversation_id = str(uuid.uuid4())[:8]  # 生成唯一对话ID
        self.conversation_count = 0  # 对话次数计数
        self.is_first_conversation = True  # 标记是否是第一次对话
        
        logger.debug(f"对话管理器初始化完成 - Agent: {self.agent_name}, 对话ID: {self.conversation_id}")
    
    def add_system_message(self, content: str):
        """添加系统消息"""
        self.conversation_history.append({
            "role": "system",
            "content": content
        })
        logger.debug(f"[{self.agent_name}] 添加系统消息")
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.conversation_history.append({
            "role": "user", 
            "content": content
        })
        logger.debug(f"[{self.agent_name}] 添加用户消息")
    
    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.conversation_history.append({
            "role": "assistant",
            "content": content
        })
        logger.debug(f"[{self.agent_name}] 添加助手消息")
    
    def clear_history(self, start_new_session: bool = True):
        """清空对话历史
        
        Args:
            start_new_session: 是否开始新会话
        """
        self.conversation_history = []
            
        if start_new_session:
            self.conversation_id = str(uuid.uuid4())[:8]
            self.conversation_count = 0
            self.is_first_conversation = True
            logger.info(f"[{self.agent_name}] 清空对话历史并开始新会话 - 新对话ID: {self.conversation_id}")
        else:
            logger.info(f"[{self.agent_name}] 清空对话历史")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()
    
    def record_llm_call(self, messages: List[Dict[str, str]], response: Any, metadata: Dict[str, Any]):
        """记录LLM调用信息
        
        Args:
            messages: 发送的消息列表
            response: LLM响应
            metadata: 元数据（模型、token等）
        """
        llm_call_info = {
            'messages': messages.copy(),  # 复制消息以避免引用问题
            'response': response if isinstance(response, str) else str(response),
            'metadata': metadata,
            'tool_results': []  # 工具调用结果，如果有的话
        }
        
        # 添加到调用链路
        self.llm_call_chain.append(llm_call_info)
    
    def add_tool_results_to_last_call(self, tool_results: List[Dict[str, Any]]):
        """将工具结果添加到最后一个LLM调用记录中"""
        if self.llm_call_chain and tool_results:
            self.llm_call_chain[-1]['tool_results'] = tool_results
    
    def save_llm_chain_log(self, ticker: str, final_result: Dict[str, Any], success: bool = True):
        """保存Agent的完整LLM调用链路日志
        
        Args:
            ticker: 股票代码
            final_result: Agent最终执行结果
            success: 是否执行成功
        """
        from utils.logger import log_agent_llm_chain
        
        if self.llm_call_chain:
            log_agent_llm_chain(
                agent_name=self.agent_name,
                ticker=ticker,
                llm_calls=self.llm_call_chain,
                final_result=final_result,
                success=success
            )
    
    def reset_llm_chain(self):
        """重置LLM调用链路收集器"""
        self.llm_call_chain.clear()
    
    def execute_with_llm_logging(self, context: Dict[str, Any], process_func: callable) -> Dict[str, Any]:
        """执行process方法并自动处理LLM调用链路记录
        
        Args:
            context: 输入上下文，必须包含'symbol'字段
            process_func: 实际的处理函数，应该返回包含success字段的字典
            
        Returns:
            处理结果
        """
        # 提取symbol，支持多种可能的位置
        symbol = context.get('symbol', '')
        if not symbol:
            # 尝试从trading_decision中获取symbol
            trading_decision = context.get('trading_decision', {})
            if isinstance(trading_decision, dict):
                symbol = trading_decision.get('symbol', '')
            elif hasattr(trading_decision, 'symbol'):
                symbol = getattr(trading_decision, 'symbol', '')
            
            # 如果还是没找到，再次警告
            if not symbol:
                logger.warning(f"[{self.agent_name}] 执行LLM日志记录时缺少symbol信息")
        
        # 重置LLM调用链路收集器
        self.reset_llm_chain()
        
        try:
            # 执行实际的处理逻辑
            result = process_func(context)
            
            # 记录LLM调用链路（成功情况）
            if symbol:
                self.save_llm_chain_log(
                    ticker=symbol,
                    final_result=result,
                    success=result.get('success', True)
                )
            
            return result
            
        except Exception as e:
            # 记录LLM调用链路（失败情况）
            error_result = {
                'success': False,
                'error': str(e)
            }
            
            if symbol:
                self.save_llm_chain_log(
                    ticker=symbol,
                    final_result=error_result,
                    success=False
                )
            
            # 重新抛出异常
            raise
    
    def execute_debate_with_llm_logging(self, topic: str, opponent_message: str, context: Dict[str, Any], debate_func: callable) -> str:
        """执行debate方法并自动处理LLM调用链路记录
        
        Args:
            topic: 辩论主题
            opponent_message: 对手消息  
            context: 上下文信息，必须包含'symbol'字段
            debate_func: 实际的辩论处理函数，应该返回辩论回应字符串
            
        Returns:
            辩论回应
        """
        # 提取symbol
        symbol = context.get('symbol', '')
        if not symbol:
            logger.warning(f"[{self.agent_name}] 执行debate LLM日志记录时缺少symbol信息")
        
        # 重置LLM调用链路收集器
        self.reset_llm_chain()
        
        try:
            # 执行实际的辩论逻辑
            response = debate_func(topic, opponent_message, context)
            
            # 记录LLM调用链路（成功情况）
            if symbol:
                debate_result = {
                    'success': True,
                    'debate_response': response,
                    'topic': topic,
                    'opponent_message': opponent_message[:200] + "..." if len(opponent_message) > 200 else opponent_message
                }
                self.save_llm_chain_log(
                    ticker=symbol,
                    final_result=debate_result,
                    success=True
                )
            
            return response
            
        except Exception as e:
            # 记录LLM调用链路（失败情况）
            error_result = {
                'success': False,
                'error': str(e),
                'topic': topic,
                'opponent_message': opponent_message[:200] + "..." if len(opponent_message) > 200 else opponent_message
            }
            
            if symbol:
                self.save_llm_chain_log(
                    ticker=symbol,
                    final_result=error_result,
                    success=False
                )
            
            # 重新抛出异常
            raise
    
    def execute_debate_response_with_llm_logging(self, topic: str, opponent_arguments: List[str], context: Dict[str, Any], debate_func: callable) -> str:
        """执行debate_response方法并自动处理LLM调用链路记录
        
        Args:
            topic: 辩论主题
            opponent_arguments: 对手论点列表
            context: 上下文信息，必须包含'trading_decision'且其中包含symbol信息
            debate_func: 实际的辩论处理函数，应该返回辩论回应字符串
            
        Returns:
            辩论回应
        """
        # 尝试从context中提取symbol
        symbol = ''
        if context:
            trading_decision = context.get('trading_decision', {})
            if isinstance(trading_decision, dict):
                symbol = trading_decision.get('symbol', '')
            elif hasattr(trading_decision, '__dict__'):
                symbol = getattr(trading_decision, 'symbol', '')
        
        if not symbol:
            logger.warning(f"[{self.agent_name}] 执行debate_response LLM日志记录时缺少symbol信息")
        
        # 重置LLM调用链路收集器
        self.reset_llm_chain()
        
        try:
            # 执行实际的辩论逻辑
            response = debate_func(topic, opponent_arguments, context)
            
            # 记录LLM调用链路（成功情况）
            if symbol:
                debate_result = {
                    'success': True,
                    'debate_response': response,
                    'topic': topic,
                    'opponent_arguments': opponent_arguments[:3] if len(opponent_arguments) > 3 else opponent_arguments  # 限制长度
                }
                self.save_llm_chain_log(
                    ticker=symbol,
                    final_result=debate_result,
                    success=True
                )
            
            return response
            
        except Exception as e:
            # 记录LLM调用链路（失败情况）
            error_result = {
                'success': False,
                'error': str(e),
                'topic': topic,
                'opponent_arguments': opponent_arguments[:3] if len(opponent_arguments) > 3 else opponent_arguments
            }
            
            if symbol:
                self.save_llm_chain_log(
                    ticker=symbol,
                    final_result=error_result,
                    success=False
                )
            
            # 重新抛出异常
            raise