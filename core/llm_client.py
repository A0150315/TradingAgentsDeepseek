"""
LLM客户端模块
提供统一的LLM API调用接口，支持不同的API提供者
"""
import json
import time
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import openai
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log

from .config import Config, get_config
from utils.logger import get_logger

logger = get_logger()
retry_logger = logging.getLogger("tenacity.retry")

# 配置重试日志输出
retry_handler = logging.StreamHandler()
retry_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
))
retry_logger.addHandler(retry_handler)
retry_logger.setLevel(logging.WARNING)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """安全的JSON序列化，处理datetime和其他不可序列化对象"""
    def json_serializer(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    return json.dumps(obj, default=json_serializer, **kwargs)


class LLMClient:
    """LLM客户端，支持不同的API提供者"""
    
    def __init__(self, provider: str = 'openai', config: Optional[Config] = None):
        """初始化LLM客户端
        
        Args:
            provider: 提供者类型 ('openai' 或 'deepseek')
            config: 配置对象
        """
        self.provider = provider.lower()
        self.config = config or get_config()
        
        llm_config = self.config.get_llm_config(provider)
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=llm_config['api_key'],
            base_url=llm_config['base_url']
        )
        
        self.model = llm_config['model']
        self.max_tokens = llm_config['max_tokens']
        self.temperature = llm_config['temperature']
        self.timeout = llm_config['timeout']
        
        logger.info(f"LLM客户端初始化成功 - Provider: {self.provider}, Model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),  # 最多重试3次  
        wait=wait_exponential(multiplier=1, min=4, max=10),  # 指数退避，4-10秒之间
        retry=retry_if_exception_type((
            openai.RateLimitError, 
            openai.APITimeoutError, 
            openai.InternalServerError,
            openai.APIConnectionError,
            openai.APIError,
            ConnectionError,
            TimeoutError,
            Exception
        )),
        before_sleep=before_sleep_log(retry_logger, logging.WARNING),  # 重试前记录日志  
        reraise=True
    )
    def chat_completion(self, messages: List[Dict[str, str]], agent_name: str = "Unknown", conversation_id: str = None, **kwargs) -> str:
        """调用聊天完成API
        
        Args:
            messages: 消息列表
            agent_name: 智能体名称，用于日志记录
            conversation_id: 对话ID，用于跟踪对话链路
            **kwargs: 其他参数
            
        Returns:
            响应内容
        """
        # 重试计数器
        retry_attempt = getattr(self, '_retry_attempt', 0)
        
        try:
            start_time = time.time()
            
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())[:8]
            
            # 记录重试信息
            if retry_attempt > 0:
                logger.warning(f"LLM API 重试第 {retry_attempt} 次 - Provider: {self.provider}, Model: {self.model}, Agent: {agent_name}")
            
            # 构建请求参数
            request_params = {
                'model': self.model,
                'messages': messages,
                'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                'temperature': kwargs.get('temperature', self.temperature),
                'timeout': kwargs.get('timeout', self.timeout),
            }
            
            # 如果有工具，添加到请求中
            if kwargs.get('tools'):
                request_params['tools'] = kwargs.get('tools')
                request_params['tool_choice'] = 'auto'  # 让模型自动决定是否调用工具
                logger.debug(f"启用工具调用 - 工具数量: {len(kwargs.get('tools'))}")
            
            response = self.client.chat.completions.create(**request_params)
            
            latency = time.time() - start_time
            
            # 处理响应
            choice = response.choices[0]
            
            if choice.message.tool_calls:
                # 如果有工具调用，返回特殊格式
                tool_calls_info = []
                for tool_call in choice.message.tool_calls:
                    logger.debug(f"工具调用请求: {tool_call.function.name}")
                    tool_calls_info.append({
                        'id': tool_call.id,
                        'function': tool_call.function.name,
                        'arguments': tool_call.function.arguments
                    })
                
                response_content = {
                    'type': 'tool_calls',
                    'content': choice.message.content or '',
                    'tool_calls': tool_calls_info
                }
                
                # 记录工具调用（简化版）
                logger.debug(f"[{agent_name}] 工具调用: {[call['function'] for call in tool_calls_info]}")
                
                return response_content
            else:
                content = choice.message.content
            
            # 简化API调用记录，不记录详细对话
            logger.debug(f"[{agent_name}] LLM响应长度: {len(content) if content else 0}字符")
            
            # 记录API调用日志
            success_msg = f"API调用成功: {self.provider}/{self.model} (tokens: {response.usage.total_tokens if hasattr(response, 'usage') else 0}, 延迟: {latency:.2f}s)"
            if retry_attempt > 0:
                success_msg += f" [重试{retry_attempt}次后成功]"
            
            logger.info(success_msg)
            logger.log_api_call(
                provider=self.provider,
                model=self.model,
                tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else 0,
                cost=0.0,  # 可以根据provider和token计算
                latency=latency,
                success=True
            )
            
            # 重置重试计数器
            if hasattr(self, '_retry_attempt'):
                delattr(self, '_retry_attempt')
            
            return content
            
        except Exception as e:
            # 增加重试计数器
            self._retry_attempt = getattr(self, '_retry_attempt', 0) + 1
            
            error_msg = f"LLM API调用失败 - Provider: {self.provider}, Model: {self.model}, Agent: {agent_name}, 尝试次数: {self._retry_attempt}, Error: {str(e)}"
            logger.error(error_msg)
            logger.log_api_call(
                provider=self.provider,
                model=self.model,
                tokens_used=0,
                cost=0.0,
                latency=0.0,
                success=False
            )
            raise Exception(f"LLM API调用失败: {str(e)}")


def create_llm_client(provider: str = 'openai', config: Optional[Config] = None) -> LLMClient:
    """创建LLM客户端"""
    logger.debug(f"创建LLM客户端 - Provider: {provider}")
    return LLMClient(provider, config)