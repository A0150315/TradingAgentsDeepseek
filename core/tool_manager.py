"""
工具管理模块
提供工具Schema生成、工具执行和工具调用解析功能
"""
import json
import time
import inspect
from typing import Dict, List, Any, Callable, Optional
from utils.logger import get_logger

logger = get_logger()


class ToolManager:
    """工具管理器，负责工具的注册、Schema生成和执行"""
    
    def __init__(self, tools: Optional[List[Callable]] = None):
        """初始化工具管理器
        
        Args:
            tools: 可用工具列表
        """
        self.tools = tools or []
        self.tool_map = {tool.__name__: tool for tool in self.tools}
        self.tool_schemas = self._generate_tool_schemas()
    
    def _generate_tool_schemas(self) -> List[Dict[str, Any]]:
        """生成工具的JSON Schema描述"""
        schemas = []
        
        for tool in self.tools:
            try:
                # 获取函数签名
                sig = inspect.signature(tool)
                
                # 构建参数schema
                parameters = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                for param_name, param in sig.parameters.items():
                    param_info = {
                        "type": "string"  # 默认为字符串，可以根据类型注解改进
                    }
                    
                    # 检查类型注解
                    if param.annotation != inspect.Parameter.empty:
                        annotation_str = str(param.annotation)
                        if param.annotation == int:
                            param_info["type"] = "integer"
                        elif param.annotation == float:
                            param_info["type"] = "number"
                        elif param.annotation == bool:
                            param_info["type"] = "boolean"
                        elif annotation_str.startswith('List') or annotation_str.startswith('list') or 'List[' in annotation_str:
                            param_info["type"] = "array"
                            # 尝试提取数组元素类型
                            if '[' in annotation_str and ']' in annotation_str:
                                element_type = annotation_str.split('[')[1].split(']')[0]
                                if element_type == 'str':
                                    param_info["items"] = {"type": "string"}
                                elif element_type == 'int':
                                    param_info["items"] = {"type": "integer"}
                                elif element_type == 'float':
                                    param_info["items"] = {"type": "number"}
                                elif element_type == 'bool':
                                    param_info["items"] = {"type": "boolean"}
                                else:
                                    param_info["items"] = {"type": "string"}
                        else:
                            param_info["type"] = "string"  # 其他类型默认为字符串
                    
                    parameters["properties"][param_name] = param_info
                    
                    # 如果没有默认值，则为必需参数
                    if param.default == inspect.Parameter.empty:
                        parameters["required"].append(param_name)
                
                # 构建工具schema
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": tool.__doc__ or f"调用 {tool.__name__} 工具",
                        "parameters": parameters
                    }
                }
                
                schemas.append(schema)
                logger.debug(f"工具Schema生成成功: {tool.__name__}")
                
            except Exception as e:
                logger.warning(f"无法为工具 {tool.__name__} 生成schema: {e}")
        
        return schemas
    
    def parse_tool_calls(self, response: str, agent_name: str = "Unknown") -> List[Dict[str, Any]]:
        """解析工具调用
        
        Args:
            response: LLM响应
            agent_name: 智能体名称，用于日志记录
            
        Returns:
            工具调用列表
        """
        tool_calls = []
        
        # 简单的工具调用解析（可以根据需要改进）
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('TOOL_CALL:'):
                try:
                    # 格式: TOOL_CALL: {"tool": "function_name", "args": {...}}
                    tool_data = json.loads(line[10:].strip())
                    tool_calls.append(tool_data)
                except json.JSONDecodeError:
                    logger.warning(f"[{agent_name}] 解析工具调用失败: {line}")
                    continue
        
        return tool_calls
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any], agent_name: str = "Unknown") -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            agent_name: 智能体名称，用于日志记录
            
        Returns:
            工具执行结果
        """
        if tool_name not in self.tool_map:
            error_msg = f"未知工具: {tool_name}"
            logger.error(f"[{agent_name}] {error_msg}")
            raise ValueError(error_msg)
        
        tool = self.tool_map[tool_name]
        try:
            logger.info(f"[{agent_name}] 执行工具: {tool_name}")
            result = tool(**args)
            logger.debug(f"[{agent_name}] 工具执行成功: {tool_name}")
            return result
        except Exception as e:
            error_msg = f"工具执行失败: {str(e)}"
            logger.error(f"[{agent_name}] 工具 {tool_name} 执行失败: {str(e)}")
            return error_msg
    
    def add_tool(self, tool: Callable):
        """添加新工具"""
        self.tools.append(tool)
        self.tool_map[tool.__name__] = tool
        # 重新生成schemas
        self.tool_schemas = self._generate_tool_schemas()
        logger.debug(f"添加工具: {tool.__name__}")
    
    def remove_tool(self, tool_name: str):
        """移除工具"""
        if tool_name in self.tool_map:
            # 从工具列表中移除
            tool = self.tool_map[tool_name]
            if tool in self.tools:
                self.tools.remove(tool)
            
            # 从映射中移除
            del self.tool_map[tool_name]
            
            # 重新生成schemas
            self.tool_schemas = self._generate_tool_schemas()
            logger.debug(f"移除工具: {tool_name}")
        else:
            logger.warning(f"尝试移除不存在的工具: {tool_name}")
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """获取工具Schemas"""
        return self.tool_schemas
    
    def has_tools(self) -> bool:
        """检查是否有可用工具"""
        return len(self.tools) > 0
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self.tool_map.keys())