"""
记忆系统 - 基于原始TradingAgents的FinancialSituationMemory实现
提供智能体学习和反思能力
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from core.agent_base import LLMClient
from core.config import Config
from utils.logger import get_logger

logger = get_logger()


@dataclass
class MemoryEntry:
    """记忆条目"""
    timestamp: str
    symbol: str
    market_conditions: Dict[str, Any]
    decision: str
    confidence: float
    reasoning: str
    outcome: Optional[Dict[str, Any]] = None
    agent_type: str = ""
    session_id: str = ""
    

class FinancialSituationMemory:
    """
    金融情况记忆系统
    基于LLM的语义相似性检索，而非嵌入向量
    """
    
    def __init__(self, agent_type: str, config: Optional[Config] = None):
        """
        初始化记忆系统
        
        Args:
            agent_type: 智能体类型 (analyst, researcher, trader, risk_manager)
            config: 配置对象
        """
        self.agent_type = agent_type
        self.config = config or Config()
        self.llm_client = LLMClient("deepseek", config)
        
        # 记忆存储路径
        self.memory_dir = Path("memory")
        self.memory_dir.mkdir(exist_ok=True)
        self.memory_file = self.memory_dir / f"{agent_type}_memory.json"
        
        # 加载已有记忆
        self.memories: List[MemoryEntry] = self._load_memories()
        
        logger.info(f"记忆系统初始化完成", 
                   agent_type=agent_type, 
                   memory_count=len(self.memories))
    
    def _load_memories(self) -> List[MemoryEntry]:
        """从文件加载记忆"""
        if not self.memory_file.exists():
            return []
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            memories = []
            for item in data:
                memories.append(MemoryEntry(**item))
            
            logger.debug(f"加载记忆成功", count=len(memories))
            return memories
            
        except Exception as e:
            logger.error(f"加载记忆失败: {e}")
            return []
    
    def _save_memories(self):
        """保存记忆到文件"""
        try:
            data = [asdict(memory) for memory in self.memories]
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"保存记忆成功", count=len(self.memories))
            
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")
    
    def add_memory(
        self,
        symbol: str,
        market_conditions: Dict[str, Any],
        decision: str,
        confidence: float,
        reasoning: str,
        session_id: str,
        outcome: Optional[Dict[str, Any]] = None
    ):
        """
        添加新记忆
        
        Args:
            symbol: 股票代码
            market_conditions: 市场情况
            decision: 决策结果
            confidence: 置信度
            reasoning: 决策理由
            session_id: 会话ID
            outcome: 结果反馈（可选）
        """
        memory = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            market_conditions=market_conditions,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            outcome=outcome,
            agent_type=self.agent_type,
            session_id=session_id
        )
        
        self.memories.append(memory)
        self._save_memories()
        
        logger.info(f"添加新记忆", 
                   symbol=symbol, 
                   decision=decision,
                   confidence=confidence)
    
    def get_relevant_memories(
        self,
        symbol: str,
        current_conditions: Dict[str, Any],
        max_memories: int = 5
    ) -> List[MemoryEntry]:
        """
        使用LLM获取相关记忆
        
        Args:
            symbol: 当前股票代码
            current_conditions: 当前市场条件
            max_memories: 最大返回记忆数量
            
        Returns:
            相关记忆列表
        """
        if not self.memories:
            return []
        
        try:
            # 构建LLM提示
            current_situation = json.dumps(current_conditions, ensure_ascii=False, indent=2)
            
            # 准备候选记忆
            candidates = []
            for i, memory in enumerate(self.memories):
                if symbol and memory.symbol != symbol:
                    continue
                    
                candidates.append({
                    "index": i,
                    "symbol": memory.symbol,
                    "timestamp": memory.timestamp,
                    "market_conditions": memory.market_conditions,
                    "decision": memory.decision,
                    "confidence": memory.confidence,
                    "reasoning": memory.reasoning[:200] + "..." if len(memory.reasoning) > 200 else memory.reasoning,
                    "outcome": memory.outcome
                })
            
            if not candidates:
                return []
            
            candidates_text = json.dumps(candidates, ensure_ascii=False, indent=2)
            
            prompt = f"""作为一个金融分析专家，请分析当前市场情况，并从历史记忆中找出最相关的情况。

当前市场情况：
{current_situation}

历史记忆候选：
{candidates_text}

请分析这些历史记忆与当前情况的相关性，选出最相关的{max_memories}个记忆。
考虑因素：
1. 市场条件的相似性（价格趋势、技术指标、市场情绪等）
2. 时间相关性（较新的记忆更重要）
3. 决策结果和置信度
4. 市场环境的相似性

请返回JSON格式的结果，包含选中记忆的索引和相关性评分：
{{"selected_memories": [{{"index": 0, "relevance_score": 0.85, "reason": "市场条件高度相似"}}]}}"""

            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.chat_completion(messages, agent_name="记忆系统")
            
            # 解析LLM响应
            try:
                # 尝试提取JSON
                response_clean = response.strip()
                if "```json" in response_clean:
                    json_start = response_clean.find("```json") + 7
                    json_end = response_clean.find("```", json_start)
                    response_clean = response_clean[json_start:json_end]
                elif "{" in response_clean:
                    json_start = response_clean.find("{")
                    json_end = response_clean.rfind("}") + 1
                    response_clean = response_clean[json_start:json_end]
                
                result = json.loads(response_clean)
                selected_indices = [item["index"] for item in result.get("selected_memories", [])]
                
                relevant_memories = [self.memories[i] for i in selected_indices if i < len(self.memories)]
                
                logger.info(f"检索相关记忆成功", 
                           symbol=symbol,
                           found_count=len(relevant_memories))
                
                return relevant_memories[:max_memories]
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"解析LLM记忆检索响应失败: {e}, 使用备用方案")
                # 备用方案：返回最近的记忆
                symbol_memories = [m for m in self.memories if not symbol or m.symbol == symbol]
                return symbol_memories[-max_memories:] if symbol_memories else []
        
        except Exception as e:
            logger.error(f"检索相关记忆失败: {e}")
            return []
    
    def reflect_on_outcomes(self, days_back: int = 30) -> str:
        """
        反思最近的决策结果
        
        Args:
            days_back: 回顾天数
            
        Returns:
            反思总结
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_memories = [
            m for m in self.memories 
            if datetime.fromisoformat(m.timestamp) >= cutoff_date and m.outcome
        ]
        
        if not recent_memories:
            return "暂无足够的历史决策结果进行反思。"
        
        try:
            # 准备反思数据
            reflection_data = []
            for memory in recent_memories:
                reflection_data.append({
                    "symbol": memory.symbol,
                    "decision": memory.decision,
                    "confidence": memory.confidence,
                    "reasoning": memory.reasoning,
                    "outcome": memory.outcome,
                    "timestamp": memory.timestamp
                })
            
            reflection_text = json.dumps(reflection_data, ensure_ascii=False, indent=2)
            
            prompt = f"""作为一个金融分析专家，请对最近{days_back}天的投资决策进行反思分析。

决策历史：
{reflection_text}

请分析：
1. 决策成功率和准确性
2. 常见的错误模式
3. 成功决策的共同特征
4. 需要改进的方面
5. 未来决策的建议

提供具体、可操作的见解和建议。"""

            messages = [{"role": "user", "content": prompt}]
            reflection = self.llm_client.chat_completion(messages, agent_name="记忆反思")
            
            logger.info(f"生成反思报告", 
                       memories_analyzed=len(recent_memories),
                       days_back=days_back)
            
            return reflection
            
        except Exception as e:
            logger.error(f"生成反思报告失败: {e}")
            return f"反思分析过程中出现错误：{str(e)}"
    
    def update_outcome(self, session_id: str, outcome: Dict[str, Any]):
        """
        更新决策结果
        
        Args:
            session_id: 会话ID
            outcome: 结果数据
        """
        updated = 0
        for memory in self.memories:
            if memory.session_id == session_id:
                memory.outcome = outcome
                updated += 1
        
        if updated > 0:
            self._save_memories()
            logger.info(f"更新决策结果", session_id=session_id, updated_count=updated)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        if not self.memories:
            return {"total_memories": 0}
        
        stats = {
            "total_memories": len(self.memories),
            "symbols_covered": len(set(m.symbol for m in self.memories)),
            "avg_confidence": sum(m.confidence for m in self.memories) / len(self.memories),
            "decision_distribution": {},
            "memories_with_outcomes": len([m for m in self.memories if m.outcome]),
            "date_range": {
                "earliest": min(m.timestamp for m in self.memories),
                "latest": max(m.timestamp for m in self.memories)
            }
        }
        
        # 决策分布
        for memory in self.memories:
            decision = memory.decision
            stats["decision_distribution"][decision] = stats["decision_distribution"].get(decision, 0) + 1
        
        return stats
    
    def clear_old_memories(self, days_to_keep: int = 180):
        """清理旧记忆"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        initial_count = len(self.memories)
        
        self.memories = [
            m for m in self.memories 
            if datetime.fromisoformat(m.timestamp) >= cutoff_date
        ]
        
        removed_count = initial_count - len(self.memories)
        if removed_count > 0:
            self._save_memories()
            logger.info(f"清理旧记忆", removed_count=removed_count)


class MemoryManager:
    """记忆管理器 - 统一管理所有Agent的记忆"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.memories: Dict[str, FinancialSituationMemory] = {}
    
    def get_memory(self, agent_type: str) -> FinancialSituationMemory:
        """获取指定Agent的记忆系统"""
        if agent_type not in self.memories:
            self.memories[agent_type] = FinancialSituationMemory(agent_type, self.config)
        return self.memories[agent_type]
    
    def clear_all_old_memories(self, days_to_keep: int = 180):
        """清理所有Agent的旧记忆"""
        for memory_system in self.memories.values():
            memory_system.clear_old_memories(days_to_keep)
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """获取整体记忆统计"""
        stats = {}
        for agent_type, memory_system in self.memories.items():
            stats[agent_type] = memory_system.get_statistics()
        return stats


# 全局记忆管理器
_memory_manager = None

def get_memory_manager() -> MemoryManager:
    """获取全局记忆管理器"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager