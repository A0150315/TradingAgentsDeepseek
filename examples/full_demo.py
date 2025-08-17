"""
TradingAgents OpenAI 框架完整演示
展示多智能体协作进行股票分析和投资决策的完整流程
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

from core import Config, create_workflow_orchestrator
from tools.yfinance_tool import YFinanceTool
from tools.google_news_tool import GoogleNewsTool


def print_section_header(title: str):
    """打印章节标题"""
    print("\n" + "=" * 60)
    print(f" {title} ")
    print("=" * 60)


def print_analysis_report(report_type: str, report):
    """打印分析报告"""
    print(f"\n📋 {report_type}分析报告:")
    print("-" * 40)
    
    if hasattr(report, 'to_dict'):
        report_dict = report.to_dict()
    else:
        report_dict = report
    
    print(f"分析师: {report_dict.get('analyst_role', 'N/A')}")
    print(f"推荐: {report_dict.get('recommendation', 'N/A')}")
    print(f"置信度: {report_dict.get('confidence_score', 'N/A')}")
    
    key_findings = report_dict.get('key_findings', [])
    if key_findings:
        print("关键发现:")
        for i, finding in enumerate(key_findings[:3], 1):
            print(f"  {i}. {finding}")


def print_debate_summary(debate_results):
    """打印辩论总结"""
    print("\n💬 研究团队辩论总结:")
    print("-" * 40)
    
    debate_result = debate_results.get('debate_result', {})
    
    print(f"辩论决策: {debate_result.get('decision', 'N/A')}")
    print(f"决策置信度: {debate_result.get('confidence', 'N/A')}")
    print(f"获胜方: {debate_result.get('winner', 'N/A')}")
    print(f"决策理由: {debate_result.get('reasoning', 'N/A')}")
    
    # 显示辩论历史片段
    debate_history = debate_results.get('debate_history', [])
    if debate_history:
        print("\n主要论点:")
        for entry in debate_history[:2]:  # 只显示前两轮
            speaker = "🐂 多头" if entry['speaker'] == 'bull' else "🐻 空头"
            message = entry['message'][:100] + "..." if len(entry['message']) > 100 else entry['message']
            print(f"  {speaker}: {message}")


def main():
    """主演示函数"""

    quick_mode = '--quick' in sys.argv or '-q' in sys.argv
    
    if quick_mode:
        print("🚀 快速测试模式 - 减少辩论轮数以加快测试")

    print_section_header("TradingAgents OpenAI 框架演示")
    
    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key or api_key == 'your-deepseek-api-key-here':
        print("⚠️  请先设置有效的 DEEPSEEK_API_KEY 环境变量")
        print("   可以在脚本开头修改或使用以下命令:")
        print("   export DEEPSEEK_API_KEY='your-actual-api-key'")
        return
    
    print("✅ API密钥已配置")
    
    # 创建配置
    config = Config()
    config.data.online_tools = True  # 确保在线工具已启用
    print(f"✅ 配置加载完成 (模型: {config.deepseek.model}, 在线工具: {config.data.online_tools})")

    # 如果是快速模式，减少辩论轮数
    if quick_mode:
        config.debate.research_team_max_rounds = 1
        config.debate.risk_team_max_rounds = 1
        config.debate.max_rounds = 1
        print("⚡ 快速模式：辩论轮数设置为1轮")
    
    # 创建工作流编排器
    print("\n🔧 初始化工作流编排器...")
    try:
        orchestrator = create_workflow_orchestrator(config)
        print("✅ 工作流编排器创建成功")
    except Exception as e:
        print(f"❌ 工作流编排器创建失败: {e}")
        return
    
    # 准备在线数据工具
    yfinance_tool = YFinanceTool()
    google_news_tool = GoogleNewsTool()

    # 准备输入数据
    symbol = "AAPL"
    
    print_section_header(f"开始分析股票: {symbol} (在线模式)")

    try:
        # 使用在线工具获取数据
        print("\n🌐 正在获取在线市场数据...")
        market_data = yfinance_tool.get_market_summary(symbol)
        
        if market_data.get('error'):
            print(f"❌ 获取市场数据失败: {market_data['error']}")
            return

        print("✅ 市场数据获取成功")
        
        # 执行工作流
        result = orchestrator.execute_trading_workflow(
            symbol=symbol,
            market_data=market_data, # 传递在线数据
            selected_analysts=['fundamental', 'technical', 'sentiment', 'news']
        )
        
        if not result['success']:
            print(f"❌ 工作流执行失败: {result['error']}")
            return
        
        # 显示分析结果
        print_section_header("分析师团队报告")
        
        analysis_results = result['analysis_results']
        if analysis_results['success']:
            reports = analysis_results['reports']
            
            for report_type, report in reports.items():
                print_analysis_report(report_type, report)
        else:
            print(f"❌ 分析师团队失败: {analysis_results['error']}")
        
        # 显示辩论结果
        print_section_header("研究团队辩论")
        
        debate_results = result['debate_results']
        if debate_results['success']:
            print_debate_summary(debate_results)
        else:
            print(f"❌ 研究辩论失败: {debate_results['error']}")
        
        # 显示最终决策
        print_section_header("最终投资决策")
        
        final_decision = result['final_decision']
        print(f"📊 股票代码: {final_decision['symbol']}")
        print(f"🎯 投资建议: {final_decision['recommendation']}")
        print(f"🔍 置信度: {final_decision['confidence']:.2%}")
        print(f"📝 决策说明: {final_decision['decision_summary']}")
        print(f"⏰ 决策时间: {final_decision['timestamp']}")
        
        print("\n📈 分析师共识:")
        consensus = final_decision.get('analyst_consensus', {})
        if consensus:
            # 处理不同的共识数据格式
            if isinstance(consensus, dict):
                for key, value in consensus.items():
                    if isinstance(value, (int, float)):
                        print(f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print(f"  共识数据: {consensus}")
        else:
            print("  📊 共识数据不可用")
        
        # 保存结果
        print_section_header("结果保存")
        
        result_file = f"trading_result_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 准备保存的数据（转换不可序列化的对象）
        save_data = {
            'symbol': symbol,
            'execution_time': result['execution_time'],
            'session_id': result['session_id'],
            'final_decision': final_decision,
            'analysis_summary': {
                'analysts_count': len(analysis_results.get('reports', {})),
                'debate_rounds': len(debate_results.get('debate_history', [])),
                'consensus_scores': final_decision.get('analyst_consensus', {})
            }
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 结果已保存到: {result_file}")
        
        # 总结
        print_section_header("执行总结")
        print(f"✅ 工作流执行成功")
        print(f"📊 分析了 {len(analysis_results.get('reports', {}))} 个维度")
        print(f"💬 进行了 {len(debate_results.get('debate_history', []))} 轮辩论")
        print(f"🎯 最终建议: {final_decision['recommendation']} (置信度: {final_decision['confidence']:.1%})")
        print(f"⏱️  总耗时: 约 30-60 秒")
        
    except Exception as e:
        print(f"❌ 工作流执行异常: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()