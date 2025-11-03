"""
交易员Agent
基于分析师报告和研究团队辩论结果，做出最终的交易决策和执行
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from core.agent_base import BaseAgent
from core.llm_client import LLMClient, safe_json_dumps
from core.state_manager import AgentRole, get_state_manager, TradingDecision
from tools.result_emitters import emit_trading_decision


class Trader(BaseAgent):
    """交易员Agent"""

    def __init__(self, llm_client: LLMClient, **kwargs):
        tools = [emit_trading_decision]

        super().__init__(
            role=AgentRole.TRADER,
            name="交易员",
            llm_client=llm_client,
            tools=tools,
            **kwargs,
        )

        # 交易员特殊系统提示
        self.system_prompt = f"""你是一位专业的股票交易员，具有丰富的市场经验和敏锐的投资嗅觉。

核心职责：
1. 综合分析师团队的专业报告
2. 结合研究团队的辩论结果
3. 基于历史经验和市场判断做出交易决策
4. 制定具体的交易执行计划
5. 考虑风险控制和资金管理

交易决策原则：
- 基于数据驱动，而非情感
- 综合考虑短期和长期因素
- 严格控制风险，保护资本
- 学习历史经验，避免重复错误
- 保持纪律性和一致性

你需要提供明确的交易建议：买入/持有/卖出，并给出详细的理由和执行计划。
"""

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理交易决策请求

        Args:
            context: 包含分析报告、辩论结果、市场数据等信息

        Returns:
            交易决策结果
        """
        # 使用BaseAgent的通用包装方法来自动处理LLM调用链路记录
        return self.execute_with_llm_logging(context, self._do_process)

    def _do_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """实际的处理逻辑（内部方法）

        Args:
            context: 包含分析报告、辩论结果、市场数据等信息

        Returns:
            交易决策结果
        """
        symbol = context.get("symbol", "")
        analysis_reports = context.get("analysis_reports", {})
        debate_result = context.get("debate_result", {})
        investment_plan = context.get("investment_plan", "")
        market_context = context.get("market_context", {})
        historical_memories = context.get("historical_memories", [])

        self.log_action("开始交易决策", {"symbol": symbol})

        # 构建交易决策提示
        trading_prompt = self._build_trading_prompt(
            symbol,
            analysis_reports,
            debate_result,
            investment_plan,
            market_context,
            historical_memories,
        )

        try:
            # 使用工具调用进行交易决策，直接返回工具结果
            decision = self.process_with_tools_return_result(
                trading_prompt, "emit_trading_decision"
            )

            # 创建交易决策对象
            price_range = decision.get("price_range", {})
            risk_management = decision.get("risk_management", {})

            trading_decision = TradingDecision(
                symbol=symbol,
                recommendation=decision.get("recommendation", "HOLD"),
                confidence_score=decision.get("confidence_score", 0.5),
                target_price=price_range.get("target_price", 0.0),
                stop_loss=risk_management.get("stop_loss", 0.0),
                take_profit=risk_management.get("take_profit", 0.0),
                position_size=decision.get("position_size", 0.0),
                time_horizon=decision.get("time_horizon", "中期"),
                reasoning=decision.get("reasoning", ""),
                risk_factors=decision.get("risk_factors", []),
                execution_plan=decision.get("execution_plan", {}),
                decision_timestamp=datetime.now(),
                analyst_consensus=self._summarize_analyst_consensus(analysis_reports),
                debate_influence=debate_result.get("decision", "HOLD"),
                acceptable_price_min=price_range.get("acceptable_min", 0.0),
                acceptable_price_max=price_range.get("acceptable_max", 0.0),
            )

            # 保存交易决策
            self.state_manager.set_trading_decision(trading_decision)

            self.log_action(
                "交易决策完成",
                {
                    "recommendation": decision.get("recommendation"),
                    "confidence": decision.get("confidence_score"),
                    "target_price": price_range.get("target_price"),
                    "price_range": f"{price_range.get('acceptable_min', 0)}-{price_range.get('acceptable_max', 0)}",
                    "stop_loss": risk_management.get("stop_loss"),
                    "take_profit": risk_management.get("take_profit"),
                },
            )

            return {
                "success": True,
                "trading_decision": trading_decision,
                "decision_details": decision,
            }

        except Exception as e:
            self.log_action("交易决策失败", {"error": str(e)})
            return {"success": False, "error": str(e)}

    def _serialize_analysis_reports(
        self, analysis_reports: Dict[str, Any]
    ) -> Dict[str, Any]:
        """序列化分析报告，处理AnalysisReport对象"""
        serialized = {}
        for key, report in analysis_reports.items():
            if hasattr(report, "to_dict"):
                serialized[key] = report.to_dict()
            else:
                serialized[key] = report
        return serialized

    def _build_trading_prompt(
        self,
        symbol: str,
        analysis_reports: Dict[str, Any],
        debate_result: Dict[str, Any],
        investment_plan: str,
        market_context: Dict[str, Any],
        historical_memories: List[Dict[str, Any]],
    ) -> str:
        """构建交易决策提示"""

        # 获取当前仓位信息
        current_position = market_context.get("current_position_size", 0.0)
        current_price = market_context.get("current_price", 0.0)
        raw_average_price = market_context.get("average_price")
        if current_position <= 0.0:
            average_price = "未购入过"
        elif raw_average_price is None:
            average_price = "未提供"
        elif isinstance(raw_average_price, (int, float)) and raw_average_price > 0:
            average_price = f"${raw_average_price:.2f}"
        else:
            average_price = str(raw_average_price)

        # 整理历史经验
        past_memory_str = ""
        if historical_memories:
            for i, memory in enumerate(historical_memories, 1):
                past_memory_str += f"{i}. {memory.get('recommendation', '')}\n"
        else:
            past_memory_str = "暂无历史交易记录可参考。"

        # 序列化分析报告
        serialized_reports = self._serialize_analysis_reports(analysis_reports)

        prompt = f"""
今天是新的一周，作为专业交易员，我需要基于最新数据对股票 {symbol} 做出当前的操作决策。

=== 当前持仓状态 ===
股票代码: {symbol}
当前仓位: {current_position * 100:.1f}% (0%=空仓, 100%=满仓)
当前价格: ${current_price}
平均持仓成本: {average_price}

=== 本周分析数据 ===
【分析师团队报告】
{safe_json_dumps(serialized_reports, indent=2, ensure_ascii=False)}

【研究团队辩论结果】
{safe_json_dumps(debate_result, indent=2, ensure_ascii=False)}

【市场环境】
{safe_json_dumps(market_context, indent=2, ensure_ascii=False)}

【历史操作记录】
{past_memory_str}

=== 操作决策要求 ===

我需要你基于当前仓位状态和最新分析，给出本周的具体操作建议：

1. **即时操作判断**
   - 基于当前仓位 {current_position * 100:.1f}% 和最新数据分析
   - 判断当前是否应该调整仓位
   - 给出具体的目标仓位 (如：从 {current_position * 100:.1f}% 调整到 50%)

2. **仓位调整逻辑**
   - 如果当前空仓(0%)且数据支持买入，建议买入仓位(如0.3-1.0)
   - 如果当前满仓(100%)且数据支持卖出，建议减仓幅度(如减至0.5)
   - 如果当前部分持仓，根据数据强度调整仓位大小
   - 如果数据不支持操作，建议保持当前仓位

3. **风险控制**
   - 基于当前价格设置止损止盈点
   - 考虑最大单次调整幅度，避免过度操作
   - 评估当前操作的风险收益比

4. **操作时机**
   - 判断当前是否适合立即操作
   - 如果需要等待更好时机，说明等待条件
   - 避免建议分批操作，专注于当前的单次决策

重要说明：
- 我的程序每周运行一次，不需要分批建仓策略
- 需要基于当前仓位给出明确的仓位调整建议
- 关注"现在是否应该操作"而不是"未来几周的计划"
- position_size表示建议的目标仓位(0.0-1.0)，不是增减幅度

<MUST>MUST OUTPUT ONLY USE TOOLS, DO NOT OUTPUT ANYTHING ELSE.</MUST>
必须使用且仅使用 emit_trading_decision 工具提供最终的交易决策结果。
请根据当前仓位状态和最新数据，给出当前的具体操作建议。
"""
        return prompt

    def _summarize_analyst_consensus(
        self, analysis_reports: Dict[str, Any]
    ) -> Dict[str, Any]:
        """总结分析师共识"""
        recommendations = {"BUY": 0, "HOLD": 0, "SELL": 0}
        total_confidence = 0
        report_count = 0

        for report_type, report in analysis_reports.items():
            if hasattr(report, "recommendation"):
                rec = report.recommendation
            else:
                rec = report.get("recommendation", "HOLD")

            if rec in recommendations:
                recommendations[rec] += 1

            if hasattr(report, "confidence_score"):
                confidence = report.confidence_score
            else:
                confidence = report.get("confidence_score", 0.5)

            total_confidence += confidence
            report_count += 1

        return {
            "recommendations": recommendations,
            "avg_confidence": (
                total_confidence / report_count if report_count > 0 else 0.5
            ),
            "consensus_level": max(recommendations, key=recommendations.get),
        }

    def execute_trade(self, decision: TradingDecision) -> Dict[str, Any]:
        """执行交易（模拟）

        Args:
            decision: 交易决策对象

        Returns:
            交易执行结果
        """
        self.log_action(
            "执行交易",
            {
                "symbol": decision.symbol,
                "action": decision.recommendation,
                "target_price": decision.target_price,
                "price_range": f"{decision.acceptable_price_min}-{decision.acceptable_price_max}",
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
            },
        )

        # 这里可以集成真实的交易接口
        # 目前返回模拟执行结果

        execution_result = {
            "trade_id": f"TRADE_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "symbol": decision.symbol,
            "action": decision.recommendation,
            "executed_price": decision.target_price * 0.99,  # 模拟执行价格
            "executed_quantity": decision.position_size * 1000,  # 模拟数量
            "execution_time": datetime.now().isoformat(),
            "status": "EXECUTED",
            "fees": decision.target_price
            * decision.position_size
            * 0.001,  # 模拟手续费
            "notes": f"基于交易员决策执行{decision.recommendation}操作",
        }

        return {"success": True, "execution_result": execution_result}

    def review_trade_performance(
        self, trade_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """复盘交易表现

        Args:
            trade_results: 交易结果列表

        Returns:
            表现分析报告
        """
        review_prompt = f"""
请分析以下交易表现并生成复盘报告：

交易记录：
{safe_json_dumps(trade_results, indent=2, ensure_ascii=False)}

请从以下角度进行分析：
1. 整体收益率和风险指标
2. 成功交易的共同特征
3. 失败交易的问题根源
4. 决策质量评估
5. 改进建议和经验总结

请提供详细的复盘分析报告。
"""

        response = self.call_llm(review_prompt)

        return {
            "performance_review": response,
            "total_trades": len(trade_results),
            "review_date": datetime.now().isoformat(),
        }


def create_trader(llm_client: LLMClient, **kwargs) -> Trader:
    """创建交易员实例"""
    return Trader(llm_client, **kwargs)
