"""
基础Agent类
提供所有智能体的通用功能和接口
"""
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable

from .llm_client import LLMClient
from .tool_manager import ToolManager
from .conversation_manager import ConversationManager
from .state_manager import AgentRole, get_state_manager
from utils.logger import get_logger

logger = get_logger()


class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(
        self,
        role: AgentRole,
        name: str,
        llm_client: LLMClient,
        system_prompt: str = "",
        tools: Optional[List[Callable]] = None
    ):
        """初始化智能体
        
        Args:
            role: 智能体角色
            name: 智能体名称
            llm_client: LLM客户端
            system_prompt: 系统提示
            tools: 可用工具列表
        """
        self.role = role
        self.name = name
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.state_manager = get_state_manager()
        
        # 初始化工具管理器
        self.tool_manager = ToolManager(tools)
        
        # 初始化对话管理器
        self.conversation_manager = ConversationManager(self.name)
        
        # 记录智能体初始化
        logger.info(f"智能体初始化成功 - 名称: {self.name}, 角色: {self.role.value}, 工具数量: {len(self.tool_manager.tools)}, 对话ID: {self.conversation_manager.conversation_id}")
    
    # 代理到对话管理器的方法
    def add_system_message(self, content: str):
        """添加系统消息"""
        self.conversation_manager.add_system_message(content)
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.conversation_manager.add_user_message(content)
    
    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.conversation_manager.add_assistant_message(content)
    
    def clear_history(self, start_new_session: bool = True):
        """清空对话历史"""
        self.conversation_manager.clear_history(start_new_session)
        if self.system_prompt:
            self.add_system_message(self.system_prompt)
    
    def call_llm(self, user_message: str, include_history: bool = True, use_tools: bool = False, **kwargs) -> str:
        """调用LLM获取响应
        
        Args:
            user_message: 用户消息
            include_history: 是否包含历史对话
            use_tools: 是否使用工具
            **kwargs: 其他参数
            
        Returns:
            LLM响应
        """
        messages = []
        
        # 添加系统提示
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # 添加历史对话
        if include_history:
            messages.extend(self.conversation_manager.get_conversation_history())
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # 准备工具信息
        tools = None
        if use_tools and self.tool_manager.has_tools():
            tools = self.tool_manager.get_tool_schemas()
        
        # 调用LLM，传递对话记录信息
        logger.debug(f"[{self.name}] 调用LLM - 消息长度: {len(user_message)}, 使用工具: {use_tools}")
        
        # 准备对话记录参数
        is_new_session = self.conversation_manager.is_first_conversation
        self.conversation_manager.conversation_count += 1
        
        # 记录调用开始时间和信息
        call_start_time = time.time()
        
        response = self.llm_client.chat_completion(
            messages, 
            agent_name=self.name,
            conversation_id=self.conversation_manager.conversation_id,
            tools=tools,
            is_new_session=is_new_session,
            **kwargs
        )
        
        # 计算调用延迟
        call_latency = time.time() - call_start_time
        
        # 记录LLM调用信息
        metadata = {
            'model': getattr(self.llm_client, 'model', 'unknown'),
            'provider': getattr(self.llm_client, 'provider', 'unknown'),
            'tokens': 0,  # 需要从LLMClient获取实际token数
            'cost': 0.0,  # 需要从LLMClient获取实际成本
            'latency': call_latency,
            'timestamp': time.time()
        }
        self.conversation_manager.record_llm_call(messages, response, metadata)
        
        # 标记已经不是第一次对话
        if self.conversation_manager.is_first_conversation:
            self.conversation_manager.is_first_conversation = False
        
        # 更新对话历史
        if include_history:
            self.add_user_message(user_message)
            if isinstance(response, dict):
                self.add_assistant_message(response.get('content', ''))
            else:
                self.add_assistant_message(response)
        
        return response
    
    def process_with_tools_return_result(self, user_message: str, target_tool_name: str, max_iterations: int = 10) -> Dict[str, Any]:
        """使用工具处理消息并返回指定工具的调用结果
        
        Args:
            user_message: 用户消息
            target_tool_name: 目标工具名称
            max_iterations: 最大迭代次数
            
        Returns:
            目标工具的执行结果字典
            
        Raises:
            ValueError: 如果未找到目标工具调用或工具执行失败
        """
        messages = []
        
        # 添加系统提示
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # 添加初始用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        logger.info(f"[{self.name}] 开始工具处理流程（返回结果模式）- 目标工具: {target_tool_name}, 最大迭代次数: {max_iterations}")
        
        # 准备对话记录参数
        is_new_session = self.conversation_manager.is_first_conversation
        self.conversation_manager.conversation_count += 1
        
        for iteration in range(max_iterations):
            logger.debug(f"[{self.name}] 工具处理迭代 {iteration + 1}/{max_iterations}")
            
            # 调用LLM，启用工具，传递对话记录信息
            call_start_time = time.time()
            response = self.llm_client.chat_completion(
                messages, 
                agent_name=self.name,
                conversation_id=self.conversation_manager.conversation_id,
                tools=self.tool_manager.get_tool_schemas(),
                is_new_session=is_new_session and iteration == 0,  # 只在第一次迭代时标记为新会话
            )
            
            # 计算调用延迟
            call_latency = time.time() - call_start_time
            
            # 记录LLM调用信息
            metadata = {
                'model': getattr(self.llm_client, 'model', 'unknown'),
                'provider': getattr(self.llm_client, 'provider', 'unknown'),
                'tokens': 0,  # 需要从LLMClient获取实际token数
                'cost': 0.0,  # 需要从LLMClient获取实际成本
                'latency': call_latency,
                'timestamp': time.time()
            }
            self.conversation_manager.record_llm_call(messages, response, metadata)
            
            # 标记已经不是第一次对话
            if self.conversation_manager.is_first_conversation:
                self.conversation_manager.is_first_conversation = False
            
            # 检查响应类型
            if isinstance(response, dict) and response.get('type') == 'tool_calls':
                # 处理工具调用
                tool_calls = response.get('tool_calls', [])
                logger.info(f"[{self.name}] 收到工具调用请求，数量: {len(tool_calls)}")
                
                # 添加助手消息（包含工具调用）
                messages.append({
                    "role": "assistant",
                    "content": response.get('content', ''),
                    "tool_calls": [
                        {
                            "id": call["id"],
                            "type": "function",
                            "function": {
                                "name": call["function"],
                                "arguments": call["arguments"]
                            }
                        } for call in tool_calls
                    ]
                })
                
                # 执行工具调用
                tool_results = []  # 收集当前迭代的工具结果
                target_tool_result = None  # 保存目标工具的执行结果
                
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]
                    try:
                        args = json.loads(tool_call["arguments"])
                    except json.JSONDecodeError:
                        logger.warning(f"[{self.name}] 工具参数解析失败: {tool_call['arguments']}")
                        args = {}
                    
                    try:
                        result = self.tool_manager.execute_tool(tool_name, args, self.name)
                        result_str = str(result)
                        
                        # 如果这是目标工具，保存结果
                        if tool_name == target_tool_name:
                            target_tool_result = result
                            logger.info(f"[{self.name}] 找到目标工具调用: {target_tool_name}")
                        
                        # 收集工具结果用于LLM调用链路记录
                        tool_results.append({
                            'tool_name': tool_name,
                            'arguments': args,
                            'result': result_str,
                            'success': True
                        })
                    except Exception as e:
                        result_str = f"工具执行失败: {str(e)}"
                        logger.error(f"[{self.name}] 工具执行异常: {str(e)}")
                        
                        # 收集工具结果用于LLM调用链路记录
                        tool_results.append({
                            'tool_name': tool_name,
                            'arguments': args,
                            'result': result_str,
                            'success': False
                        })
                    
                    # 添加工具结果消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": result_str
                    })
                
                # 将工具结果添加到对话管理器的最后一个LLM调用记录中
                self.conversation_manager.add_tool_results_to_last_call(tool_results)
                
                # 如果找到了目标工具的结果，直接返回
                if target_tool_result is not None:
                    logger.info(f"[{self.name}] 目标工具调用成功，返回结果")
                    return target_tool_result
                
                # 继续下一轮对话
                continue
            else:
                # 没有工具调用，检查是否是因为达到迭代次数
                if iteration == max_iterations - 1:
                    break
                else:
                    # 如果LLM没有调用工具，继续等待
                    continue
        
        # 如果循环结束都没有找到目标工具调用，抛出异常
        logger.error(f"[{self.name}] 未找到目标工具调用: {target_tool_name}")
        raise ValueError(f"未找到目标工具调用: {target_tool_name}，或工具执行失败")
    
    @abstractmethod
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入并返回结果
        
        Args:
            context: 输入上下文
            
        Returns:
            处理结果
        """
        pass
    
    def log_action(self, action: str, details: Dict[str, Any] = None):
        """记录智能体行动
        
        Args:
            action: 行动描述
            details: 详细信息
        """
        logger.info(f"[{self.name}] {action}")
        if details:
            from .llm_client import safe_json_dumps
            logger.debug(f"[{self.name}] 行动详情: {safe_json_dumps(details)}")
    
    def save_output_to_markdown(
        self, 
        output: str, 
        ticker: str = None, 
        stage: str = "", 
        metadata: Optional[Dict[str, Any]] = None
    ):
        """保存智能体输出到markdown文件
        
        Args:
            output: 智能体输出内容
            ticker: 股票代码（如果为None，尝试从状态管理器获取）
            stage: 阶段描述
            metadata: 额外元数据
        """
        # 如果没有提供ticker，尝试从状态管理器获取
        if not ticker and self.state_manager.current_session:
            ticker = self.state_manager.current_session.symbol
        
        if not ticker:
            logger.warning(f"[{self.name}] 无法保存markdown输出：未找到股票代码")
            return
        
        # 调用logger的markdown输出功能
        logger.log_agent_output(
            agent_name=self.name,
            ticker=ticker,
            output=output,
            stage=stage,
            metadata=metadata
        )
    
    # 代理到对话管理器的LLM日志方法
    def save_llm_chain_log(self, ticker: str, final_result: Dict[str, Any], success: bool = True):
        """保存Agent的完整LLM调用链路日志"""
        self.conversation_manager.save_llm_chain_log(ticker, final_result, success)
    
    def reset_llm_chain(self):
        """重置LLM调用链路收集器"""
        self.conversation_manager.reset_llm_chain()
    
    def execute_with_llm_logging(self, context: Dict[str, Any], process_func: callable) -> Dict[str, Any]:
        """执行process方法并自动处理LLM调用链路记录"""
        return self.conversation_manager.execute_with_llm_logging(context, process_func)
    
    def execute_debate_with_llm_logging(self, topic: str, opponent_message: str, context: Dict[str, Any], debate_func: callable) -> str:
        """执行debate方法并自动处理LLM调用链路记录"""
        return self.conversation_manager.execute_debate_with_llm_logging(topic, opponent_message, context, debate_func)
    
    def execute_debate_response_with_llm_logging(self, topic: str, opponent_arguments: List[str], context: Dict[str, Any], debate_func: callable) -> str:
        """执行debate_response方法并自动处理LLM调用链路记录"""
        return self.conversation_manager.execute_debate_response_with_llm_logging(topic, opponent_arguments, context, debate_func)