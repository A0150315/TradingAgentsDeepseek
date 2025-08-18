"""
状态管理器
管理整个交易会话的状态和数据流
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import json
from pathlib import Path
import uuid


class AgentRole(Enum):
    """智能体角色枚举"""
    FUNDAMENTAL_ANALYST = "fundamental_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    NEWS_ANALYST = "news_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    BULL_RESEARCHER = "bull_researcher"
    BEAR_RESEARCHER = "bear_researcher"
    DEBATE_COORDINATOR = "debate_coordinator"
    TRADER = "trader"
    RISKY_ANALYST = "risky_analyst"
    NEUTRAL_ANALYST = "neutral_analyst"
    SAFE_ANALYST = "safe_analyst"
    RISK_MANAGER = "risk_manager"
    FUND_MANAGER = "fund_manager"


class MessageType(Enum):
    """消息类型枚举"""
    ANALYSIS_REPORT = "analysis_report"
    DEBATE_MESSAGE = "debate_message"
    TRADING_DECISION = "trading_decision"
    RISK_ASSESSMENT = "risk_assessment"
    FINAL_RECOMMENDATION = "final_recommendation"


@dataclass
class Message:
    """消息结构"""
    id: str
    timestamp: datetime
    sender: AgentRole
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'sender': self.sender.value,
            'message_type': self.message_type.value,
            'content': self.content,
            'metadata': self.metadata
        }


@dataclass
class TradingDecision:
    """交易决策"""
    symbol: str
    recommendation: str  # BUY, SELL, HOLD
    confidence_score: float
    target_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    time_horizon: str
    reasoning: str
    risk_factors: List[str]
    execution_plan: Dict[str, Any]
    decision_timestamp: datetime
    analyst_consensus: Dict[str, Any]
    debate_influence: str
    acceptable_price_min: float = 0.0
    acceptable_price_max: float = 0.0


@dataclass
class AnalysisReport:
    """结构化分析报告
    
    基于论文4.2节要求：分析师编制简洁、组织良好的报告，包含关键指标、
    洞察和基于专业分析的建议，避免信息稀释和数据丢失
    """
    # 核心身份信息
    analyst_role: AgentRole
    symbol: str
    analysis_date: date
    
    # 核心分析结果 (论文要求的"key metrics, insights, and recommendations")
    key_findings: List[str]  # 关键洞察
    recommendation: str  # BUY/SELL/HOLD 建议
    confidence_score: float  # 置信度 0.0-1.0
    
    # 通用分析维度 (支持后续工作流处理)
    risk_factors: List[str] = field(default_factory=list)  # 风险因素
    time_horizon: Dict[str, str] = field(default_factory=dict)  # 时间框架分析
    impact_magnitude: float = 0.5  # 影响程度 0.0-1.0
    
    # 原始支持数据 (保持向后兼容)
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    
    # 处理元数据
    detailed_analysis: str = ""  # 详细分析文本
    processing_time: float = 0.0  # 处理时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，符合结构化通信协议"""
        return {
            'analyst_role': self.analyst_role.value,
            'symbol': self.symbol,
            'analysis_date': self.analysis_date.isoformat(),
            'key_findings': self.key_findings,
            'recommendation': self.recommendation,
            'confidence_score': self.confidence_score,
            'risk_factors': self.risk_factors,
            'time_horizon': self.time_horizon,
            'impact_magnitude': self.impact_magnitude,
            'supporting_data': self.supporting_data,
            'detailed_analysis': self.detailed_analysis,
            'processing_time': self.processing_time
        }
    
    def get_analyst_type(self) -> str:
        """获取分析师类型"""
        return self.analyst_role.value
    
    def get_structured_summary(self) -> Dict[str, Any]:
        """获取结构化摘要，用于其他Agent查询"""
        return {
            'analyst': self.analyst_role.value,
            'recommendation': self.recommendation,
            'confidence': self.confidence_score,
            'key_findings': self.key_findings[:3],  # 限制为最重要的3个发现
            'risk_level': len(self.risk_factors),
            'impact_magnitude': self.impact_magnitude
        }
    
    def is_bullish(self) -> bool:
        """判断是否看涨"""
        return self.recommendation == 'BUY'
    
    def is_bearish(self) -> bool:
        """判断是否看跌"""
        return self.recommendation == 'SELL'
    
    def is_high_confidence(self, threshold: float = 0.7) -> bool:
        """判断是否高置信度"""
        return self.confidence_score >= threshold
    
    def get_weighted_recommendation_score(self) -> float:
        """获取加权建议评分，用于后续决策聚合"""
        recommendation_weights = {'BUY': 1.0, 'HOLD': 0.5, 'SELL': 0.0}
        base_score = recommendation_weights.get(self.recommendation, 0.5)
        return base_score * self.confidence_score * self.impact_magnitude


@dataclass
class DebateState:
    """辩论状态"""
    participants: List[AgentRole]
    current_round: int
    max_rounds: int
    messages: List[Message] = field(default_factory=list)
    consensus_reached: bool = False
    final_decision: Optional[str] = None
    topic: Optional[str] = None  # 辩论主题
    
    def add_message(self, message: Message):
        """添加消息"""
        self.messages.append(message)
    
    def get_history_for_role(self, role: AgentRole) -> List[Message]:
        """获取特定角色的历史消息"""
        return [msg for msg in self.messages if msg.sender == role]
    
    def get_conversation_history(self) -> str:
        """获取对话历史的文本格式"""
        history = []
        for msg in self.messages:
            history.append(f"{msg.sender.value}: {msg.content}")
        return "\n".join(history)


@dataclass
class TradingSession:
    """交易会话"""
    session_id: str
    symbol: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # 分析报告
    fundamental_report: Optional[AnalysisReport] = None
    sentiment_report: Optional[AnalysisReport] = None
    news_report: Optional[AnalysisReport] = None
    technical_report: Optional[AnalysisReport] = None
    
    # 辩论状态
    research_debate: Optional[DebateState] = None
    risk_debate: Optional[DebateState] = None
    
    # 决策结果
    trader_decision: Optional[TradingDecision] = None
    risk_management_decision: Optional[Dict[str, Any]] = None
    final_recommendation: Optional[Dict[str, Any]] = None
    
    # 执行结果
    executed_trades: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class StateManager:
    """状态管理器"""
    
    def __init__(self):
        """初始化状态管理器"""
        self.current_session: Optional[TradingSession] = None
        self.session_history: List[TradingSession] = []
        self.message_counter = 0
    
    def start_session(self, symbol: str) -> str:
        """开始新的交易会话
        
        Args:
            symbol: 交易标的
            
        Returns:
            会话ID
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{symbol}"
        
        self.current_session = TradingSession(
            session_id=session_id,
            symbol=symbol,
            start_time=datetime.now()
        )
        
        return session_id
    
    def end_session(self):
        """结束当前交易会话"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.session_history.append(self.current_session)
            self.current_session = None
    
    def add_analysis_report(self, report: AnalysisReport):
        """添加分析报告"""
        if not self.current_session:
            return  # 忽略操作，不抛出异常
        
        role = report.analyst_role
        if role == AgentRole.FUNDAMENTAL_ANALYST:
            self.current_session.fundamental_report = report
        elif role == AgentRole.SENTIMENT_ANALYST:
            self.current_session.sentiment_report = report
        elif role == AgentRole.NEWS_ANALYST:
            self.current_session.news_report = report
        elif role == AgentRole.TECHNICAL_ANALYST:
            self.current_session.technical_report = report
    
    def get_analysis_reports(self) -> Dict[str, AnalysisReport]:
        """获取所有分析报告"""
        if not self.current_session:
            return {}
        
        reports = {}
        if self.current_session.fundamental_report:
            reports['fundamental'] = self.current_session.fundamental_report
        if self.current_session.sentiment_report:
            reports['sentiment'] = self.current_session.sentiment_report
        if self.current_session.news_report:
            reports['news'] = self.current_session.news_report
        if self.current_session.technical_report:
            reports['technical'] = self.current_session.technical_report
        
        return reports
    
    def start_research_debate(self, participants: List[AgentRole], max_rounds: int = 3) -> DebateState:
        """开始研究团队辩论"""
        if not self.current_session:
            # 返回一个临时的辩论状态
            return DebateState(
                participants=participants,
                current_round=0,
                max_rounds=max_rounds
            )
        
        debate_state = DebateState(
            participants=participants,
            current_round=0,
            max_rounds=max_rounds
        )
        
        self.current_session.research_debate = debate_state
        return debate_state
    
    def start_risk_debate(self, participants: List[AgentRole], max_rounds: int = 3) -> DebateState:
        """开始风险管理团队辩论"""
        if not self.current_session:
            # 返回一个临时的辩论状态
            return DebateState(
                participants=participants,
                current_round=0,
                max_rounds=max_rounds
            )
        
        debate_state = DebateState(
            participants=participants,
            current_round=0,
            max_rounds=max_rounds
        )
        
        self.current_session.risk_debate = debate_state
        return debate_state
    
    def add_debate_message(self, debate_type: str, sender: AgentRole, content: str, metadata: Dict[str, Any] = None) -> Message:
        """添加辩论消息
        
        Args:
            debate_type: 辩论类型 ('research' 或 'risk')
            sender: 发送者角色
            content: 消息内容
            metadata: 元数据
            
        Returns:
            消息对象
        """
        if not self.current_session:
            # 创建临时消息但不存储
            self.message_counter += 1
            return Message(
                id=f"msg_{self.message_counter}",
                timestamp=datetime.now(),
                sender=sender,
                message_type=MessageType.DEBATE_MESSAGE,
                content=content,
                metadata=metadata or {}
            )
        
        self.message_counter += 1
        message = Message(
            id=f"msg_{self.message_counter}",
            timestamp=datetime.now(),
            sender=sender,
            message_type=MessageType.DEBATE_MESSAGE,
            content=content,
            metadata=metadata or {}
        )
        
        if debate_type == 'research' and self.current_session.research_debate:
            self.current_session.research_debate.add_message(message)
        elif debate_type == 'risk' and self.current_session.risk_debate:
            self.current_session.risk_debate.add_message(message)
        
        return message
    
    def set_trader_decision(self, decision: Dict[str, Any]):
        """设置交易员决策"""
        if not self.current_session:
            return  # 忽略操作，不抛出异常
        
        self.current_session.trader_decision = decision
    
    def set_final_recommendation(self, recommendation: Dict[str, Any]):
        """设置最终推荐"""
        if not self.current_session:
            return  # 忽略操作，不抛出异常
        
        self.current_session.final_recommendation = recommendation
    
    def add_executed_trade(self, trade: Dict[str, Any]):
        """添加已执行交易"""
        if not self.current_session:
            return  # 忽略操作，不抛出异常
        
        trade['timestamp'] = datetime.now().isoformat()
        self.current_session.executed_trades.append(trade)
    
    def update_performance_metrics(self, metrics: Dict[str, float]):
        """更新性能指标"""
        if not self.current_session:
            return  # 忽略操作，不抛出异常
        
        self.current_session.performance_metrics.update(metrics)
    
    def set_trading_decision(self, decision: TradingDecision):
        """设置交易决策"""
        if not self.current_session:
            return  # 忽略操作，不抛出异常
        
        self.current_session.trader_decision = decision
    
    def set_risk_management_decision(self, decision: Dict[str, Any]):
        """设置风险管理决策"""
        if not self.current_session:
            return  # 忽略操作，不抛出异常
        
        self.current_session.risk_management_decision = decision
    
    def get_current_session_state(self) -> Dict[str, Any]:
        """获取当前会话状态"""
        if not self.current_session:
            return {}
        
        session = self.current_session
        return {
            'session_id': session.session_id,
            'symbol': session.symbol,
            'start_time': session.start_time.isoformat(),
            'analysis_reports': {
                'fundamental': session.fundamental_report.to_dict() if session.fundamental_report else None,
                'sentiment': session.sentiment_report.to_dict() if session.sentiment_report else None,
                'news': session.news_report.to_dict() if session.news_report else None,
                'technical': session.technical_report.to_dict() if session.technical_report else None,
            },
            'research_debate': {
                'participants': [p.value for p in session.research_debate.participants] if session.research_debate else [],
                'messages': [msg.to_dict() for msg in session.research_debate.messages] if session.research_debate else [],
                'consensus_reached': session.research_debate.consensus_reached if session.research_debate else False,
                'final_decision': session.research_debate.final_decision if session.research_debate else None
            } if session.research_debate else None,
            'risk_debate': {
                'participants': [p.value for p in session.risk_debate.participants] if session.risk_debate else [],
                'messages': [msg.to_dict() for msg in session.risk_debate.messages] if session.risk_debate else [],
                'consensus_reached': session.risk_debate.consensus_reached if session.risk_debate else False,
                'final_decision': session.risk_debate.final_decision if session.risk_debate else None
            } if session.risk_debate else None,
            'trader_decision': session.trader_decision,
            'final_recommendation': session.final_recommendation,
            'executed_trades': session.executed_trades,
            'performance_metrics': session.performance_metrics
        }
    
    def save_session(self, file_path: str):
        """保存会话到文件"""
        if not self.current_session:
            return  # 忽略操作，不保存
        
        state = self.get_current_session_state()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def load_session(self, file_path: str):
        """从文件加载会话"""
        with open(file_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        # 重建会话状态
        # 这里可以根据需要实现更详细的状态恢复逻辑
        pass


# 全局状态管理器实例
global_state_manager = StateManager()


def get_state_manager() -> StateManager:
    """获取全局状态管理器实例"""
    return global_state_manager