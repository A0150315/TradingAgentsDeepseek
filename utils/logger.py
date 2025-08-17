"""
日志系统配置
提供结构化日志记录功能，用于调试和监控
"""
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
from loguru import logger

# 创建日志目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str = "TradingAgents"):
        self.name = name
        self._setup_logger()
        # 全局调用序号计数器，按会话重置
        self._session_call_counter = 0
        self._current_session_ticker = None
    
    def _setup_logger(self):
        """配置日志系统"""
        # 移除默认处理器
        logger.remove()
        
        # 控制台输出 - 彩色格式
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level="INFO",
            colorize=True
        )
        
        # 文件输出 - 详细日志
        logger.add(
            LOG_DIR / "trading_agents.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="100 MB",
            retention="30 days",
            compression="zip"
        )
        
        # 错误日志单独文件
        logger.add(
            LOG_DIR / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="50 MB",
            retention="60 days"
        )
        
        # 交易决策日志
        logger.add(
            LOG_DIR / "trading_decisions.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
            level="INFO",
            filter=lambda record: "TRADING_DECISION" in record["extra"],
            rotation="10 MB",
            retention="90 days"
        )
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        logger.bind(**kwargs).info(message)
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        logger.bind(**kwargs).debug(message)
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        logger.bind(**kwargs).warning(message)
    
    def error(self, message: str, **kwargs):
        """错误日志"""
        logger.bind(**kwargs).error(message)
    
    def critical(self, message: str, **kwargs):
        """严重错误日志"""
        logger.bind(**kwargs).critical(message)
    
    def log_trading_decision(
        self, 
        symbol: str, 
        decision: str, 
        confidence: float,
        reasoning: str,
        agent_type: str,
        session_id: str
    ):
        """记录交易决策"""
        decision_data = {
            "symbol": symbol,
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "agent_type": agent_type,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.bind(TRADING_DECISION=True).info(
            f"交易决策: {symbol} -> {decision} (置信度: {confidence:.2%})",
            **decision_data
        )
    
    def log_agent_performance(
        self, 
        agent_name: str, 
        execution_time: float,
        success: bool,
        error: Optional[str] = None
    ):
        """记录Agent性能"""
        perf_data = {
            "agent_name": agent_name,
            "execution_time": execution_time,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        level = "info" if success else "error"
        message = f"Agent {agent_name} 执行完成 (耗时: {execution_time:.2f}s)"
        if not success and error:
            message += f" - 错误: {error}"
        
        getattr(logger, level)(message, **perf_data)
    
    def log_api_call(
        self, 
        provider: str, 
        model: str,
        tokens_used: int,
        cost: float,
        latency: float,
        success: bool
    ):
        """记录API调用信息"""
        api_data = {
            "provider": provider,
            "model": model,
            "tokens_used": tokens_used,
            "cost": cost,
            "latency": latency,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        self.info(
            f"API调用: {provider}/{model} (tokens: {tokens_used}, 成本: ${cost:.4f}, 延迟: {latency:.2f}s)",
            **api_data
        )
    
    def log_data_source(
        self, 
        source: str, 
        symbol: str,
        data_type: str,
        records_count: int,
        success: bool,
        error: Optional[str] = None
    ):
        """记录数据源访问"""
        data_info = {
            "source": source,
            "symbol": symbol,
            "data_type": data_type,
            "records_count": records_count,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        level = "info" if success else "warning"
        message = f"数据获取: {source} -> {symbol} ({data_type}, {records_count} 条记录)"
        if not success and error:
            message += f" - 错误: {error}"
        
        getattr(logger, level)(message, **data_info)
    
    def log_workflow_step(
        self, 
        step_name: str, 
        symbol: str,
        session_id: str,
        step_data: Dict[str, Any]
    ):
        """记录工作流步骤"""
        workflow_data = {
            "step_name": step_name,
            "symbol": symbol,
            "session_id": session_id,
            "step_data": step_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.info(
            f"工作流步骤: {step_name} (股票: {symbol})",
            **workflow_data
        )
    
    def log_agent_output(
        self,
        agent_name: str,
        ticker: str,
        output: str,
        stage: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录智能体输出到markdown文件
        
        Args:
            agent_name: 智能体名称
            ticker: 股票代码
            output: 智能体输出内容
            stage: 阶段描述（可选）
            metadata: 额外元数据（可选）
        """
        try:
            # 创建日期/ticker目录结构
            today = datetime.now().strftime("%Y-%m-%d")
            log_dir = LOG_DIR / "markdown" / today / ticker.upper()
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 文件名格式: [agent].md
            agent_filename = agent_name.lower().replace(' ', '_').replace('师', '').replace('员', '')
            if stage:
                agent_filename += f"_{stage}"
            file_path = log_dir / f"{agent_filename}.md"
            
            # 构建markdown内容
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            markdown_content = []
            
            # 判断是否是新文件
            is_new_file = not file_path.exists()
            
            if is_new_file:
                markdown_content.append(f"# {agent_name} - {ticker.upper()}")
                markdown_content.append(f"**日期**: {today}")
                if metadata:
                    for key, value in metadata.items():
                        markdown_content.append(f"**{key}**: {value}")
                markdown_content.append("")
                markdown_content.append("---")
                markdown_content.append("")
            
            # 添加时间戳和内容
            markdown_content.append(f"## {timestamp}")
            if stage:
                markdown_content.append(f"**阶段**: {stage}")
                markdown_content.append("")
            
            # 添加输出内容
            markdown_content.append(output)
            markdown_content.append("")
            markdown_content.append("---")
            markdown_content.append("")
            
            # 写入文件
            with open(file_path, "a" if not is_new_file else "w", encoding="utf-8") as f:
                f.write("\n".join(markdown_content))
            
            # 只记录基本信息到控制台，不记录详细输出
            self.info(f"[{agent_name}] 输出已保存 -> {file_path.relative_to(LOG_DIR)}")
            
        except Exception as e:
            self.error(f"记录智能体输出失败: {str(e)}")

    def log_workflow_stage(
        self,
        ticker: str,
        stage: str,
        content: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录工作流阶段到markdown文件
        
        Args:
            ticker: 股票代码
            stage: 工作流阶段名称
            content: 阶段内容
            success: 是否成功
            metadata: 额外元数据
        """
        try:
            # 创建日期/ticker目录结构
            today = datetime.now().strftime("%Y-%m-%d")
            log_dir = LOG_DIR / "markdown" / today / ticker.upper()
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 工作流总览文件
            file_path = log_dir / "workflow.md"
            
            # 构建markdown内容
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            markdown_content = []
            
            # 判断是否是新文件
            is_new_file = not file_path.exists()
            
            if is_new_file:
                markdown_content.append(f"# 交易工作流 - {ticker.upper()}")
                markdown_content.append(f"**日期**: {today}")
                markdown_content.append("")
                markdown_content.append("## 执行流程")
                markdown_content.append("")
            
            # 添加阶段内容
            status_emoji = "✅" if success else "❌"
            markdown_content.append(f"### {status_emoji} {stage} ({timestamp})")
            
            if metadata:
                for key, value in metadata.items():
                    markdown_content.append(f"**{key}**: {value}")
                markdown_content.append("")
            
            markdown_content.append(content)
            markdown_content.append("")
            markdown_content.append("---")
            markdown_content.append("")
            
            # 写入文件
            with open(file_path, "a" if not is_new_file else "w", encoding="utf-8") as f:
                f.write("\n".join(markdown_content))
            
            # 记录到控制台
            status_text = "完成" if success else "失败"
            self.info(f"工作流阶段 [{stage}] {status_text} -> {file_path.relative_to(LOG_DIR)}")
            
        except Exception as e:
            self.error(f"记录工作流阶段失败: {str(e)}")

    def log_agent_llm_chain(
        self,
        agent_name: str,
        ticker: str,
        llm_calls: List[Dict[str, Any]],
        final_result: Dict[str, Any],
        success: bool = True
    ):
        """记录Agent的完整LLM调用链路
        
        Args:
            agent_name: 智能体名称
            ticker: 股票代码
            llm_calls: LLM调用记录列表，每个元素包含messages、response、metadata等
            final_result: Agent最终执行结果
            success: 是否执行成功
        """
        try:
            # 重置计数器（如果是新的ticker会话）
            if self._current_session_ticker != ticker.upper():
                self._current_session_ticker = ticker.upper()
                self._session_call_counter = 0
            
            # 递增调用序号
            self._session_call_counter += 1
            
            # 创建日期/ticker目录结构
            today = datetime.now().strftime("%Y-%m-%d")
            log_dir = LOG_DIR / "llm" / today / ticker.upper()
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 文件名格式: 序号.agent_name.md
            agent_filename = agent_name.lower().replace(' ', '_').replace('师', '').replace('员', '')
            file_path = log_dir / f"{self._session_call_counter:02d}.{agent_filename}.md"
            
            # 构建markdown内容
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_emoji = "✅" if success else "❌"
            
            markdown_content = []
            markdown_content.append(f"# {status_emoji} {agent_name} - LLM调用链路 #{self._session_call_counter}")
            markdown_content.append(f"**股票**: {ticker.upper()}")
            markdown_content.append(f"**时间**: {today} {timestamp}")
            markdown_content.append(f"**状态**: {'成功' if success else '失败'}")
            markdown_content.append(f"**LLM调用次数**: {len(llm_calls)}")
            markdown_content.append("")
            
            # 执行结果摘要
            markdown_content.append("## 📋 执行结果")
            if success:
                recommendation = final_result.get('recommendation', 'N/A')
                confidence = final_result.get('confidence_score', 'N/A')
                markdown_content.append(f"- **推荐**: {recommendation}")
                markdown_content.append(f"- **置信度**: {confidence}")
            else:
                error = final_result.get('error', 'Unknown error')
                markdown_content.append(f"- **错误**: {error}")
            markdown_content.append("")
            markdown_content.append("---")
            markdown_content.append("")
            
            # 记录每次LLM调用
            for i, llm_call in enumerate(llm_calls, 1):
                messages = llm_call.get('messages', [])
                response = llm_call.get('response', '')
                metadata = llm_call.get('metadata', {})
                tool_results = llm_call.get('tool_results', [])
                
                markdown_content.append(f"## 🔄 LLM调用 {i}")
                
                # API调用信息
                if metadata:
                    markdown_content.append(f"**模型**: {metadata.get('model', 'N/A')}")
                    markdown_content.append(f"**Token数**: {metadata.get('tokens', 'N/A')}")
                    markdown_content.append(f"**成本**: ${metadata.get('cost', 0):.4f}")
                    markdown_content.append(f"**延迟**: {metadata.get('latency', 'N/A')}s")
                    markdown_content.append("")
                
                # 记录对话消息
                for message in messages:
                    role = message.get('role', 'unknown')
                    content = message.get('content', '')
                    
                    if role == 'system':
                        markdown_content.append(f"### 🔧 System Prompt")
                        markdown_content.append("```text")
                        markdown_content.append(content)
                        markdown_content.append("```")
                    elif role == 'user':
                        markdown_content.append(f"### 👤 User Input")
                        markdown_content.append("```text")
                        markdown_content.append(content)
                        markdown_content.append("```")
                    elif role == 'assistant':
                        markdown_content.append(f"### 🤖 Assistant Response")
                        markdown_content.append("```text")
                        markdown_content.append(content)
                        markdown_content.append("```")
                    markdown_content.append("")
                
                # LLM最终响应
                markdown_content.append("### 🎯 LLM Response")
                markdown_content.append("```text")
                markdown_content.append(response)
                markdown_content.append("```")
                markdown_content.append("")
                
                # 工具调用结果
                if tool_results:
                    markdown_content.append("### 🛠️ Tool Results")
                    for k, tool_result in enumerate(tool_results, 1):
                        markdown_content.append(f"#### Tool Result {k}")
                        markdown_content.append("```json")
                        markdown_content.append(json.dumps(tool_result, indent=2, ensure_ascii=False))
                        markdown_content.append("```")
                    markdown_content.append("")
                
                markdown_content.append("---")
                markdown_content.append("")
            
            # 调用统计
            total_tokens = sum(call.get('metadata', {}).get('tokens', 0) for call in llm_calls)
            total_cost = sum(call.get('metadata', {}).get('cost', 0) for call in llm_calls)
            total_latency = sum(call.get('metadata', {}).get('latency', 0) for call in llm_calls)
            
            markdown_content.append("## 📊 调用统计")
            markdown_content.append(f"- **调用序号**: {self._session_call_counter}")
            markdown_content.append(f"- **智能体**: {agent_name}")
            markdown_content.append(f"- **LLM调用次数**: {len(llm_calls)}")
            markdown_content.append(f"- **总Token数**: {total_tokens}")
            markdown_content.append(f"- **总成本**: ${total_cost:.4f}")
            markdown_content.append(f"- **总延迟**: {total_latency:.2f}s")
            markdown_content.append("")
            
            markdown_content.append("---")
            markdown_content.append(f"*记录时间: {datetime.now().isoformat()}*")
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(markdown_content))
            
            # 记录到控制台
            status_text = "成功" if success else "失败"
            self.info(f"[{agent_name}] {status_text} - LLM调用链路已记录 -> {file_path.relative_to(LOG_DIR)}")
            
        except Exception as e:
            self.error(f"记录Agent LLM调用链路失败: {str(e)}")

    def reset_session_counter(self, ticker: str = None):
        """重置会话计数器
        
        Args:
            ticker: 新的股票代码，如果提供则更新当前会话ticker
        """
        self._session_call_counter = 0
        if ticker:
            self._current_session_ticker = ticker.upper()
        self.info(f"会话计数器已重置，当前ticker: {self._current_session_ticker}")
    
    def get_current_call_number(self) -> int:
        """获取当前调用序号"""
        return self._session_call_counter

    def get_session_dir(self, ticker: str) -> Path:
        """获取当前会话的markdown目录
        
        Args:
            ticker: 股票代码
            
        Returns:
            markdown目录路径
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return LOG_DIR / "markdown" / today / ticker.upper()


# 全局日志实例
trading_logger = StructuredLogger("TradingAgents")


def get_logger() -> StructuredLogger:
    """获取全局日志实例"""
    return trading_logger


# 便捷函数
def log_agent_llm_chain(
    agent_name: str,
    ticker: str,
    llm_calls: List[Dict[str, Any]],
    final_result: Dict[str, Any],
    success: bool = True
):
    """记录Agent的完整LLM调用链路"""
    trading_logger.log_agent_llm_chain(
        agent_name=agent_name,
        ticker=ticker,
        llm_calls=llm_calls,
        final_result=final_result,
        success=success
    )

def reset_session_counter(ticker: str = None):
    """重置会话计数器"""
    trading_logger.reset_session_counter(ticker)

def get_current_call_number() -> int:
    """获取当前调用序号"""
    return trading_logger.get_current_call_number()

# 便捷函数
def log_info(message: str, **kwargs):
    """记录信息日志"""
    trading_logger.info(message, **kwargs)


def log_debug(message: str, **kwargs):
    """记录调试日志"""
    trading_logger.debug(message, **kwargs)


def log_warning(message: str, **kwargs):
    """记录警告日志"""
    trading_logger.warning(message, **kwargs)


def log_error(message: str, **kwargs):
    """记录错误日志"""
    trading_logger.error(message, **kwargs)


def log_trading_decision(
    symbol: str, 
    decision: str, 
    confidence: float,
    reasoning: str,
    agent_type: str,
    session_id: str
):
    """记录交易决策"""
    trading_logger.log_trading_decision(
        symbol=symbol,
        decision=decision,
        confidence=confidence,
        reasoning=reasoning,
        agent_type=agent_type,
        session_id=session_id
    )