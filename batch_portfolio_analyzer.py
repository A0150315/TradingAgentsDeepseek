#!/usr/bin/env python3
"""
批量投资组合分析器
并行分析多支股票，输出排序后的交易建议
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import concurrent.futures
import time
import csv
import json
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from core.workflow import create_workflow_orchestrator
from tools.yfinance_tool import YFinanceTool
from utils.email_sender import create_email_sender


class BatchPortfolioAnalyzer:
    """批量投资组合分析器"""

    def __init__(self, max_workers: int = 3):
        """初始化分析器

        Args:
            max_workers: 最大并行工作数量，建议3以避免API限流
        """
        self.max_workers = max_workers
        self.yfinance_tool = YFinanceTool()

    def analyze_portfolio(
        self,
        symbols: List[str],
        selected_analysts: Optional[List[str]] = None,
        output_file: Optional[str] = None,
        include_market_data: bool = True,
        portfolio_positions: Optional[
            Dict[str, float]
        ] = None,  # 新增：当前投资组合仓位
    ) -> Dict[str, Any]:
        """批量分析股票组合

        Args:
            symbols: 股票代码列表
            selected_analysts: 选择的分析师列表
            output_file: 输出文件路径（可选）
            include_market_data: 是否获取市场数据
            portfolio_positions: 当前投资组合仓位 {symbol: position_size}

        Returns:
            批量分析结果
        """
        portfolio_positions = portfolio_positions or {}
        print(f"\n🚀 开始批量分析 {len(symbols)} 支股票...")
        print("=" * 60)
        print(f"📊 并行度: {self.max_workers} 个工作线程")
        if selected_analysts:
            print(f"👥 分析师: {', '.join(selected_analysts)}")
        if portfolio_positions:
            print(f"💼 当前持仓: {len(portfolio_positions)} 支股票有仓位")
        print()

        start_time = time.time()
        results = []
        errors = []

        # 获取市场数据（如果需要）
        market_data_dict = {}
        if include_market_data:
            print("📈 获取市场数据...")
            market_data_dict = self._fetch_market_data(symbols)

        # 并行执行股票分析
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            # 提交任务
            future_to_symbol = {
                executor.submit(
                    self._analyze_single_stock,
                    symbol,
                    market_data_dict.get(symbol, {}),
                    selected_analysts,
                    portfolio_positions.get(symbol, 0.0),  # 传入当前仓位
                ): symbol
                for symbol in symbols
            }

            # 收集结果
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                completed_count += 1

                try:
                    result = future.result()
                    if result.success:
                        results.append(result)
                        print(
                            f"  ✅ [{completed_count}/{len(symbols)}] {symbol}: {result.recommendation} (置信度: {result.confidence_score:.2f})"
                        )
                    else:
                        errors.append(
                            {"symbol": symbol, "error": result.error or "未知错误"}
                        )
                        print(
                            f"  ❌ [{completed_count}/{len(symbols)}] {symbol}: 分析失败 - {result.error or '未知错误'}"
                        )

                except Exception as e:
                    error_msg = f"{symbol}分析异常: {str(e)}"
                    errors.append({"symbol": symbol, "error": error_msg})
                    print(f"  💥 [{completed_count}/{len(symbols)}] {error_msg}")

        total_time = time.time() - start_time

        # 按置信度排序
        results.sort(key=lambda x: x.confidence_score, reverse=True)

        # 显示汇总
        self._print_summary(results, errors, total_time)

        # 输出到文件
        if output_file and results:
            self._save_results(results, errors, output_file)
            print(f"📁 结果已保存到: {output_file}")

        return {
            "success": True,
            "total_analyzed": len(symbols),
            "successful_count": len(results),
            "failed_count": len(errors),
            "execution_time": total_time,
            "results": results,
            "errors": errors,
            "output_file": output_file,
        }

    def _fetch_market_data(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取市场数据"""
        market_data_dict = {}

        for symbol in symbols:
            try:
                market_data = self.yfinance_tool.get_market_summary(symbol)
                if "error" not in market_data:
                    market_data_dict[symbol] = market_data
                    print(
                        f"    📊 {symbol}: ${market_data.get('current_price', 'N/A')}"
                    )
                else:
                    print(f"    ⚠️ {symbol}: 无法获取市场数据")
            except Exception as e:
                print(f"    ❌ {symbol}: 市场数据获取异常 - {str(e)}")

        print(f"✅ 成功获取 {len(market_data_dict)}/{len(symbols)} 支股票的市场数据\n")
        return market_data_dict

    def _analyze_single_stock(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        selected_analysts: Optional[List[str]],
        current_position_size: float = 0.0,
    ) -> Any:
        """分析单支股票"""
        try:
            # 为每个股票创建独立的orchestrator实例
            orchestrator = create_workflow_orchestrator()

            # 使用快速模式执行工作流
            result = orchestrator.execute_trading_workflow(
                symbol=symbol,
                market_data=market_data,
                selected_analysts=selected_analysts,
                quick_mode=True,
                current_position_size=current_position_size,
            )
            return result
        except Exception as e:
            # 为了保持一致性，这里也返回一个简单的WorkflowResult对象
            from core.workflow import WorkflowResult, WorkflowStage

            return WorkflowResult(
                success=False,
                session_id="",
                symbol=symbol,
                stage=WorkflowStage.INITIALIZATION,
                error=str(e),
                mode="quick",
            )

    def _print_summary(
        self, results: List[Any], errors: List[Dict[str, Any]], total_time: float
    ):
        """打印汇总信息"""
        success_count = len(results)
        total_count = success_count + len(errors)

        print(f"\n📊 批量分析完成:")
        print(f"  ✅ 成功: {success_count} 支股票")
        print(f"  ❌ 失败: {len(errors)} 支股票")
        print(f"  ⏱️ 总耗时: {total_time:.1f}s")
        print(f"  📈 平均耗时: {total_time/total_count:.1f}s/股票")

        if results:
            print(f"\n🎯 TOP 5 推荐（按置信度排序）:")
            for i, result in enumerate(results[:5], 1):
                action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(
                    result.recommendation, "⚪"
                )
                print(
                    f"  {i}. {action_emoji} {result.symbol}: {result.recommendation} "
                    f"(置信度: {result.confidence_score:.2f}, 目标价: ${result.target_price:.2f})"
                )

    def _save_results(
        self,
        results: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        output_file: str,
    ):
        """保存结果到文件"""
        if output_file.endswith(".csv"):
            self._save_to_csv(results, errors, output_file)
        elif output_file.endswith(".json"):
            self._save_to_json(results, errors, output_file)
        else:
            # 默认保存为CSV
            csv_file = output_file + ".csv"
            self._save_to_csv(results, errors, csv_file)

    def _save_to_csv(
        self,
        results: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        file_path: str,
    ):
        """保存结果到CSV文件"""
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "symbol",
                "recommendation",
                "confidence_score",
                "target_price",
                "acceptable_price_min",
                "acceptable_price_max",
                "take_profit",
                "stop_loss",
                "position_size",
                "time_horizon",
                "reasoning",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in results:
                # 截断reasoning字段以适应CSV
                reasoning = result.reasoning
                if len(reasoning) > 200:
                    reasoning = reasoning[:200] + "..."

                writer.writerow(
                    {
                        "symbol": result.symbol,
                        "recommendation": result.recommendation,
                        "confidence_score": result.confidence_score,
                        "target_price": result.target_price,
                        "acceptable_price_min": result.acceptable_price_min,
                        "acceptable_price_max": result.acceptable_price_max,
                        "take_profit": result.take_profit,
                        "stop_loss": result.stop_loss,
                        "position_size": result.position_size,
                        "time_horizon": result.time_horizon,
                        "reasoning": reasoning,
                    }
                )

    def _save_to_json(
        self,
        results: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        file_path: str,
    ):
        """保存结果到JSON文件"""
        output_data = {
            "analysis_time": datetime.now().isoformat(),
            "total_stocks": len(results) + len(errors),
            "successful_analysis": len(results),
            "failed_analysis": len(errors),
            "results": results,
            "errors": errors,
        }

        with open(file_path, "w", encoding="utf-8") as jsonfile:
            json.dump(output_data, jsonfile, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    load_dotenv()

    # 15支股票投资组合
    portfolio_symbols = [
        "AAPL",
        "MSFT",
        "GOOGL",
        "NVDA",
        "TSM",
        "ASML",
        "AMD",
        "QCOM",
        "INTC",
        "V",
        "JPM",
        "BRK-B",
        "JNJ",
        "PG",
        "MCD",
    ]

    # 选择的分析师（可以根据需要调整）
    selected_analysts = ["fundamental", "technical", "sentiment", "news"]

    current_positions = {
        "TSM": 0.241,
        "MSFT": 0.507,
        "NVDA": 0.175,
        "MCD": 0.305,
        "AMD": 0.320,
    }

    # 输出文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"portfolio_analysis_{timestamp}.csv"

    print("🎯 批量投资组合分析")
    print("=" * 50)
    print(f"📈 分析股票: {', '.join(portfolio_symbols)}")
    print(f"👥 分析师团队: {', '.join(selected_analysts)}")
    print(f"📁 输出文件: {output_file}")

    try:
        # 创建分析器
        analyzer = BatchPortfolioAnalyzer(max_workers=2)

        # 执行批量分析
        batch_result = analyzer.analyze_portfolio(
            symbols=portfolio_symbols,
            selected_analysts=selected_analysts,
            output_file=output_file,
            include_market_data=True,
            portfolio_positions=current_positions,  # 传入当前仓位信息
        )

        if batch_result["success"]:
            print(f"\n🎉 批量分析成功完成!")
            print(
                f"📊 成功分析 {batch_result['successful_count']}/{batch_result['total_analyzed']} 支股票"
            )
            print(f"⏱️ 总耗时: {batch_result['execution_time']:.1f}秒")

            # 发送邮件报告
            print("\n📧 准备发送邮件报告...")
            try:
                email_sender = create_email_sender()
                success = email_sender.send_analysis_report(
                    csv_file=output_file,
                    analysis_summary=batch_result,
                    timestamp=timestamp,
                    subject_prefix="投资组合分析报告",
                )

                if success:
                    print("✅ 邮件报告发送成功!")
                else:
                    print("❌ 邮件报告发送失败")

            except Exception as email_error:
                print(f"📧 邮件发送异常: {str(email_error)}")
                import traceback

                traceback.print_exc()

        else:
            print(f"\n❌ 批量分析失败")

    except Exception as e:
        print(f"\n💥 分析过程中发生异常: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
