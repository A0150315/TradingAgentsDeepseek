"""
工作流编排器 - 重构优化版本
协调整个交易决策流程，管理各个智能体的执行顺序和数据流转
"""
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
import time

from core import (
    Config, 
    LLMClient, 
    create_llm_client,
    get_state_manager,
    AgentRole
)
from agents.analysts import (
    create_fundamental_analyst,
    create_technical_analyst,
    create_sentiment_analyst,
    create_news_analyst
)
from agents.researchers import (
    create_bull_researcher,
    create_bear_researcher
)
from agents.trader import create_trader
from agents.fund_manager import create_fund_manager
from agents.risk_management import (
    create_conservative_analyst,
    create_aggressive_analyst,
    create_neutral_analyst,
    create_risk_manager,
    create_risk_debate_coordinator
)
from communication.debate_coordinator import create_debate_coordinator


class WorkflowStage(Enum):
    """工作流阶段枚举"""
    INITIALIZATION = "初始化"
    ANALYSIS = "分析师团队分析"
    DEBATE = "研究团队辩论"
    TRADING = "交易员决策"
    RISK_MANAGEMENT = "风险管理评估"
    FINAL_DECISION = "基金经理最终决策"
    COMPLETION = "工作流完成"


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    success: bool
    session_id: str
    symbol: str
    stage: WorkflowStage
    error: Optional[str] = None
    analysis_results: Optional[Dict[str, Any]] = None
    debate_results: Optional[Dict[str, Any]] = None
    trading_decision: Optional[Dict[str, Any]] = None
    risk_management: Optional[Dict[str, Any]] = None
    fund_manager_result: Optional[Dict[str, Any]] = None
    final_decision: Optional[Dict[str, Any]] = None
    execution_time: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # 快速模式专用属性
    recommendation: Optional[str] = None
    confidence_score: Optional[float] = None
    target_price: Optional[float] = None
    acceptable_price_min: Optional[float] = None
    acceptable_price_max: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: Optional[float] = None
    time_horizon: Optional[str] = None
    reasoning: Optional[str] = None
    mode: Optional[str] = None


@dataclass
class AnalystConfig:
    """分析师配置"""
    name: str
    emoji: str
    display_name: str
    enabled: bool = True
    special_context_builder: Optional[callable] = None


class WorkflowOrchestrator:
    """工作流编排器 - 优化版"""
    
    # 分析师配置映射
    ANALYST_CONFIGS = {
        'fundamental': AnalystConfig("fundamental", "📈", "基础分析师"),
        'technical': AnalystConfig("technical", "📊", "技术分析师"),
        'sentiment': AnalystConfig("sentiment", "😊", "情绪分析师", 
                                 special_context_builder=lambda self, context, market_data: {
                                     **context,
                                     'social_media_data': market_data.get('social_media_data', {
                                         'reddit_posts': 150,
                                         'twitter_mentions': 300,
                                         'positive_ratio': 0.65
                                     }),
                                     'sentiment_indicators': market_data.get('sentiment_indicators', {
                                         'vix': 18.5,
                                         'put_call_ratio': 0.8,
                                         'fear_greed_index': 70
                                     })
                                 }),
        'news': AnalystConfig("news", "📰", "新闻分析师"),
    }
    
    def __init__(self, config: Optional[Config] = None):
        """初始化工作流编排器"""
        self.config = config or Config()
        self.state_manager = get_state_manager()
        self.logger = self._setup_logger()
        
        # 创建LLM客户端
        self._llm_clients = self._create_llm_clients()
        
        # 创建所有智能体
        self._agents = self._create_agents()
        
        self.logger.info("工作流编排器初始化完成")
    
    def _setup_logger(self):
        """设置日志记录器"""
        from utils.logger import get_logger
        return get_logger()
    
    def _create_llm_clients(self) -> Dict[str, LLMClient]:
        """创建LLM客户端"""
        return {
            'quick': create_llm_client('deepseek', self.config),
            'deep': create_llm_client('deepseek', self.config)
        }
    
    def _create_agents(self) -> Dict[str, Any]:
        """创建所有智能体"""
        quick_llm = self._llm_clients['quick']
        deep_llm = self._llm_clients['deep']
        
        agents = {}
        
        # 分析师团队
        agents.update({
            'fundamental_analyst': create_fundamental_analyst(quick_llm),
            'technical_analyst': create_technical_analyst(quick_llm),
            'sentiment_analyst': create_sentiment_analyst(quick_llm),
            'news_analyst': create_news_analyst(quick_llm),
        })
        
        # 研究团队
        agents.update({
            'bull_researcher': create_bull_researcher(deep_llm),
            'bear_researcher': create_bear_researcher(deep_llm),
        })
        
        # 交易和风险管理团队
        agents.update({
            'trader': create_trader(deep_llm),
            'fund_manager': create_fund_manager(deep_llm),
            'conservative_analyst': create_conservative_analyst(quick_llm),
            'aggressive_analyst': create_aggressive_analyst(quick_llm),
            'neutral_analyst': create_neutral_analyst(quick_llm),
            'risk_manager': create_risk_manager(deep_llm),
        })
        
        # 辩论协调器
        agents.update({
            'debate_coordinator': create_debate_coordinator(
                agents['bull_researcher'],
                agents['bear_researcher'],
                deep_llm,
                max_rounds=self.config.debate.research_team_max_rounds
            ),
            'risk_debate_coordinator': create_risk_debate_coordinator(
                agents['conservative_analyst'],
                agents['aggressive_analyst'],
                agents['neutral_analyst'],
                agents['risk_manager'],
                deep_llm,
                max_rounds=self.config.debate.research_team_max_rounds
            )
        })
        
        return agents
    
    def execute_trading_workflow(
        self,
        symbol: str,
        market_data: Optional[Dict[str, Any]] = None,
        selected_analysts: Optional[List[str]] = None,
        quick_mode: bool = False,
        current_position_size: float = 0.0
    ) -> WorkflowResult:
        """执行完整的交易工作流"""
        
        # 初始化
        session_id = self._initialize_workflow(symbol, selected_analysts)
        market_data = market_data or {}
        market_data['current_position_size'] = current_position_size
        selected_analysts = selected_analysts or ['fundamental', 'technical', 'sentiment', 'news']
        
        try:
            # 根据模式选择工作流执行阶段
            if quick_mode:
                workflow_stages = [
                    (WorkflowStage.ANALYSIS, self._execute_analysis_stage),
                    (WorkflowStage.DEBATE, self._execute_debate_stage),
                    (WorkflowStage.TRADING, self._execute_trading_stage),
                ]
            else:
                workflow_stages = [
                    (WorkflowStage.ANALYSIS, self._execute_analysis_stage),
                    (WorkflowStage.DEBATE, self._execute_debate_stage),
                    (WorkflowStage.TRADING, self._execute_trading_stage),
                    (WorkflowStage.RISK_MANAGEMENT, self._execute_risk_stage),
                    (WorkflowStage.FINAL_DECISION, self._execute_final_stage),
                ]
            
            results = {}
            for stage, executor in workflow_stages:
                print(f"\n{self._get_stage_emoji(stage)} {stage.value}")
                
                stage_result = executor(symbol, market_data, selected_analysts, results)
                if not stage_result['success']:
                    return self._create_failure_result(session_id, symbol, stage, stage_result['error'])
                
                results[stage] = stage_result
                self._log_stage_completion(symbol, stage, stage_result)
            
            # 创建成功结果
            return self._create_success_result(session_id, symbol, results, quick_mode)
            
        except Exception as e:
            return self._handle_workflow_exception(session_id, symbol, e)
        
        finally:
            self.state_manager.end_session()
    
    def _initialize_workflow(self, symbol: str, selected_analysts: Optional[List[str]]) -> str:
        """初始化工作流"""
        print(f"\n开始执行 {symbol} 的交易工作流...")
        print("=" * 50)
        
        session_id = self.state_manager.start_session(symbol)
        
        self.logger.log_workflow_stage(
            ticker=symbol,
            stage="工作流开始",
            content=f"开始执行 {symbol} 的完整交易决策工作流\n\n**会话ID**: {session_id}\n**选择的分析师**: {', '.join(selected_analysts or ['fundamental', 'technical', 'sentiment', 'news'])}",
            success=True,
            metadata={"session_id": session_id, "selected_analysts": selected_analysts}
        )
        
        return session_id
    
    def _execute_analysis_stage(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        selected_analysts: List[str],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行分析师团队分析阶段"""
        return self._run_analyst_team_parallel(symbol, market_data, selected_analysts)
    
    def _execute_debate_stage(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        selected_analysts: List[str],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行研究团队辩论阶段"""
        analysis_results = results[WorkflowStage.ANALYSIS]
        return self._run_research_debate(symbol, analysis_results['reports'], market_data)
    
    def _execute_trading_stage(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        selected_analysts: List[str],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行交易员决策阶段"""
        analysis_results = results[WorkflowStage.ANALYSIS]
        debate_results = results[WorkflowStage.DEBATE]
        
        return self._run_trader_decision(
            symbol,
            analysis_results['reports'],
            debate_results['debate_result'],
            debate_results.get('investment_plan', ''),
            market_data
        )
    
    def _execute_risk_stage(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        selected_analysts: List[str],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行风险管理评估阶段"""
        analysis_results = results[WorkflowStage.ANALYSIS]
        trading_decision = results[WorkflowStage.TRADING]
        
        return self._run_risk_management(
            symbol,
            trading_decision['trading_decision'],
            analysis_results['reports'],
            market_data
        )
    
    def _execute_final_stage(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        selected_analysts: List[str],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行基金经理最终决策阶段"""
        analysis_results = results[WorkflowStage.ANALYSIS]
        debate_results = results[WorkflowStage.DEBATE]
        trading_decision = results[WorkflowStage.TRADING]
        risk_management = results[WorkflowStage.RISK_MANAGEMENT]
        
        context = {
            'symbol': symbol,
            'analysis_reports': analysis_results['reports'],
            'debate_result': debate_results['debate_result'],
            'trading_decision': trading_decision['trading_decision'],
            'risk_assessment': risk_management['final_decision'],
            'market_context': market_data
        }
        
        return self._agents['fund_manager'].process(context)
    
    def _run_analyst_team_parallel(
        self, 
        symbol: str, 
        market_data: Dict[str, Any],
        selected_analysts: List[str]
    ) -> Dict[str, Any]:
        """并行运行分析师团队"""
        
        # 准备任务
        tasks = self._prepare_analyst_tasks(symbol, market_data, selected_analysts)
        if not tasks:
            return {'success': False, 'error': "没有选择任何分析师", 'reports': {}}
        
        print(f"  🚀 并行启动 {len(tasks)} 个分析师...")
        start_time = time.time()
        
        # 并行执行
        analysis_reports, errors = self._execute_analyst_tasks_parallel(tasks)
        total_time = time.time() - start_time
        
        # 处理结果
        return self._process_analyst_results(analysis_reports, errors, total_time, len(tasks))
    
    def _prepare_analyst_tasks(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        selected_analysts: List[str]
    ) -> List[Tuple[str, Any, Dict[str, Any]]]:
        """准备分析师任务"""
        base_context = {'symbol': symbol, **market_data}
        tasks = []
        
        for analyst_type in selected_analysts:
            if analyst_type not in self.ANALYST_CONFIGS:
                continue
                
            config = self.ANALYST_CONFIGS[analyst_type]
            agent = self._agents[f'{analyst_type}_analyst']
            
            # 构建上下文
            if config.special_context_builder:
                context = config.special_context_builder(self, base_context, market_data)
            else:
                context = base_context
            
            tasks.append((analyst_type, agent, context))
        
        return tasks
    
    def _execute_analyst_tasks_parallel(
        self, 
        tasks: List[Tuple[str, Any, Dict[str, Any]]]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """并行执行分析师任务"""
        analysis_reports = {}
        errors = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            # 提交任务
            future_to_analyst = {
                executor.submit(self._execute_single_analyst, analyst_type, agent, context): analyst_type
                for analyst_type, agent, context in tasks
            }
            
            # 收集结果
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_analyst):
                analyst_type = future_to_analyst[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    self._process_single_analyst_result(
                        result, analysis_reports, errors, completed_count, len(tasks)
                    )
                except Exception as e:
                    error_msg = f"{analyst_type}异常: {str(e)}"
                    errors.append(error_msg)
                    print(f"    💥 [{completed_count}/{len(tasks)}] {error_msg}")
        
        return analysis_reports, errors
    
    def _execute_single_analyst(
        self, 
        analyst_type: str, 
        agent: Any, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个分析师"""
        start_time = time.time()
        
        try:
            result = agent.process(context)
            execution_time = time.time() - start_time
            
            return {
                'success': result['success'],
                'analyst_type': analyst_type,
                'result': result,
                'execution_time': execution_time
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'analyst_type': analyst_type,
                'error': str(e),
                'execution_time': execution_time
            }
    
    def _process_single_analyst_result(
        self, 
        result: Dict[str, Any], 
        analysis_reports: Dict[str, Any], 
        errors: List[str],
        completed_count: int,
        total_count: int
    ):
        """处理单个分析师结果"""
        if result['success']:
            analysis_reports[result['analyst_type']] = result['result']['report']
            config = self.ANALYST_CONFIGS[result['analyst_type']]
            print(f"    ✅ [{completed_count}/{total_count}] {config.display_name}完成 ({result['execution_time']:.1f}s)")
            
            # 技术分析师的特殊显示
            if result['analyst_type'] == 'technical' and 'analysis_result' in result['result']:
                analysis_result = result['result']['analysis_result']
                print(f"        📈 推荐: {analysis_result.get('recommendation', 'N/A')}")
                print(f"        🎯 置信度: {analysis_result.get('confidence_score', 0):.2f}")
                print(f"        📊 趋势: {analysis_result.get('trend_direction', 'N/A')}")
        else:
            error_msg = f"{result['analyst_type']}失败: {result.get('error', result.get('result', {}).get('error', '未知错误'))}"
            errors.append(error_msg)
            print(f"    ❌ [{completed_count}/{total_count}] {error_msg}")
    
    def _process_analyst_results(
        self, 
        analysis_reports: Dict[str, Any], 
        errors: List[str], 
        total_time: float,
        total_count: int
    ) -> Dict[str, Any]:
        """处理分析师团队结果"""
        if not analysis_reports:
            print(f"  ❌ 所有分析师都失败了 (总耗时: {total_time:.1f}s)")
            return {
                'success': False,
                'error': f"所有分析师都失败了: {'; '.join(errors)}",
                'reports': {}
            }
        
        success_count = len(analysis_reports)
        
        if errors:
            print(f"  ⚠️ 部分分析师失败: {len(errors)}个失败, {success_count}个成功 (总耗时: {total_time:.1f}s)")
        else:
            print(f"  ✅ 所有分析师完成 ({success_count}/{total_count}) (总耗时: {total_time:.1f}s)")
        
        return {
            'success': True,
            'reports': analysis_reports,
            'errors': errors
        }
    
    def _run_research_debate(
        self, 
        symbol: str,
        analysis_reports: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行研究团队辩论"""
        try:
            return self._agents['debate_coordinator'].conduct_research_debate(
                symbol=symbol,
                analysis_reports=analysis_reports,
                market_context=market_context
            )
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _run_trader_decision(
        self,
        symbol: str,
        analysis_reports: Dict[str, Any],
        debate_result: Dict[str, Any],
        investment_plan: str,
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行交易员决策"""
        try:
            context = {
                'symbol': symbol,
                'analysis_reports': analysis_reports,
                'debate_result': debate_result,
                'investment_plan': investment_plan,
                'market_context': market_context,
                'historical_memories': []  # 可以从状态管理器获取历史记忆
            }
            
            return self._agents['trader'].process(context)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _run_risk_management(
        self,
        symbol: str,
        trading_decision: Any,
        analysis_reports: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """运行风险管理评估"""
        try:
            return self._agents['risk_debate_coordinator'].conduct_risk_debate(
                trading_decision=trading_decision,
                market_data=market_data,
                analysis_reports=analysis_reports,
                historical_memories=[]  # 可以从状态管理器获取历史记忆
            )
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_stage_emoji(self, stage: WorkflowStage) -> str:
        """获取阶段表情符号"""
        emoji_map = {
            WorkflowStage.ANALYSIS: "🔍",
            WorkflowStage.DEBATE: "💬",
            WorkflowStage.TRADING: "💼",
            WorkflowStage.RISK_MANAGEMENT: "⚖️",
            WorkflowStage.FINAL_DECISION: "🎯",
            WorkflowStage.COMPLETION: "✅"
        }
        return emoji_map.get(stage, "📋")
    
    def _log_stage_completion(self, symbol: str, stage: WorkflowStage, result: Dict[str, Any]):
        """记录阶段完成"""
        self.logger.log_workflow_stage(
            ticker=symbol,
            stage=f"{stage.value}完成",
            content=f"{stage.value}阶段执行完成",
            success=result['success'],
            metadata=result.get('metadata', {})
        )
    
    def _create_success_result(self, session_id: str, symbol: str, results: Dict[str, Any], quick_mode: bool = False) -> WorkflowResult:
        """创建成功结果"""
        if quick_mode:
            # 快速模式：使用交易员决策
            trading_result = results[WorkflowStage.TRADING]
            if not trading_result['success']:
                # 交易阶段失败，返回失败结果
                return WorkflowResult(
                    success=False,
                    session_id=session_id,
                    symbol=symbol,
                    stage=WorkflowStage.TRADING,
                    error=trading_result.get('error', '交易决策失败'),
                    mode='quick'
                )
            
            trading_decision = trading_result['trading_decision']
            final_recommendation = trading_decision.recommendation
            final_confidence = trading_decision.confidence_score
            
            print("\n✅ 工作流执行完成（快速模式）")
            print(f"最终决策: {final_recommendation}")
            print(f"置信度: {final_confidence:.2f}")
            
            return WorkflowResult(
                success=True,
                session_id=session_id,
                symbol=symbol,
                stage=WorkflowStage.COMPLETION,
                analysis_results=results[WorkflowStage.ANALYSIS],
                debate_results=results[WorkflowStage.DEBATE],
                trading_decision=results[WorkflowStage.TRADING],
                execution_time=datetime.now().isoformat(),
                # 快速模式专用属性
                recommendation=trading_decision.recommendation,
                confidence_score=trading_decision.confidence_score,
                target_price=trading_decision.target_price,
                acceptable_price_min=trading_decision.acceptable_price_min,
                acceptable_price_max=trading_decision.acceptable_price_max,
                take_profit=trading_decision.take_profit,
                stop_loss=trading_decision.stop_loss,
                position_size=trading_decision.position_size,
                time_horizon=trading_decision.time_horizon,
                reasoning=trading_decision.reasoning,
                mode='quick'
            )
        else:
            # 完整模式：使用基金经理决策
            final_decision = results[WorkflowStage.FINAL_DECISION]['investment_decision']
            
            print("\n✅ 工作流执行完成")
            print(f"最终决策: {final_decision['final_recommendation']}")
            print(f"置信度: {final_decision['confidence_score']:.2f}")
            
            self.logger.log_workflow_stage(
                ticker=symbol,
                stage="工作流完成",
                content=f"交易工作流执行完成\n\n**最终决策**: {final_decision['final_recommendation']}\n**置信度**: {final_decision['confidence_score']:.2f}",
                success=True,
                metadata={
                    "final_recommendation": final_decision['final_recommendation'],
                    "final_confidence": final_decision['confidence_score'],
                    "execution_time": datetime.now().isoformat()
                }
            )
            
            return WorkflowResult(
                success=True,
                session_id=session_id,
                symbol=symbol,
                stage=WorkflowStage.COMPLETION,
                analysis_results=results[WorkflowStage.ANALYSIS],
                debate_results=results[WorkflowStage.DEBATE],
                trading_decision=results[WorkflowStage.TRADING],
                risk_management=results[WorkflowStage.RISK_MANAGEMENT],
                fund_manager_result=results[WorkflowStage.FINAL_DECISION],
                final_decision=final_decision,
                execution_time=datetime.now().isoformat(),
                mode='full'
            )
    
    def _create_failure_result(self, session_id: str, symbol: str, stage: WorkflowStage, error: str) -> WorkflowResult:
        """创建失败结果"""
        self.logger.log_workflow_stage(
            ticker=symbol,
            stage=f"{stage.value}失败",
            content=f"{stage.value}阶段失败：{error}",
            success=False
        )
        
        return WorkflowResult(
            success=False,
            session_id=session_id,
            symbol=symbol,
            stage=stage,
            error=error
        )
    
    def _handle_workflow_exception(self, session_id: str, symbol: str, e: Exception) -> WorkflowResult:
        """处理工作流异常"""
        error_msg = str(e)
        print(f"\n❌ 工作流执行失败: {error_msg}")
        
        self.logger.log_workflow_stage(
            ticker=symbol,
            stage="工作流失败",
            content=f"交易工作流执行失败\n\n**错误**: {error_msg}\n**会话ID**: {session_id}",
            success=False,
            metadata={"error": error_msg, "session_id": session_id}
        )
        
        return WorkflowResult(
            success=False,
            session_id=session_id,
            symbol=symbol,
            stage=WorkflowStage.INITIALIZATION,
            error=error_msg
        )
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return self.state_manager.get_current_session_state()


def create_workflow_orchestrator(config: Optional[Config] = None) -> WorkflowOrchestrator:
    """创建工作流编排器实例"""
    return WorkflowOrchestrator(config)


# 向后兼容的测试代码
if __name__ == "__main__":
    from dotenv import load_dotenv
    from tools.yfinance_tool import YFinanceTool
    
    load_dotenv()
    
    # 测试股票代码
    symbol = "BABA"
    
    print(f"开始测试完整交易工作流 - 股票代码: {symbol}")
    print("=" * 60)
    
    try:
        # 获取市场数据
        print("📊 获取市场数据...")
        yfinance_tool = YFinanceTool()
        market_data = yfinance_tool.get_market_summary(symbol)
        
        if 'error' in market_data:
            print(f"❌ 获取市场数据失败: {market_data['error']}")
            exit(1)
        
        print(f"✅ 成功获取 {symbol} 的市场数据")
        print(f"   当前价格: ${market_data.get('current_price', 'N/A')}")
        print(f"   公司名称: {market_data.get('company_name', 'N/A')}")
        print(f"   行业: {market_data.get('industry', 'N/A')}")
        
        # 创建工作流编排器
        print("\n🔧 初始化工作流编排器...")
        orchestrator = create_workflow_orchestrator()
        
        # 执行完整的交易工作流
        print(f"\n🚀 执行完整交易工作流...")
        result = orchestrator.execute_trading_workflow(
            symbol=symbol,
            market_data=market_data,
            selected_analysts=['fundamental', 'technical', 'sentiment', 'news']
        )
        
        # 显示结果
        if result.success:
            print("\n🎉 工作流执行成功!")
            print(f"最终决策: {result.final_decision['final_recommendation']}")
            print(f"置信度: {result.final_decision['confidence_score']:.2f}")
            print(f"执行时间: {result.execution_time}")
        else:
            print(f"\n❌ 工作流执行失败: {result.error}")
            
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()