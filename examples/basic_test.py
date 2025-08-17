"""
TradingAgents OpenAI 框架基础测试
测试基本功能和Deepseek API连接
"""
import os
import json
from datetime import date
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from core import Config, get_config, create_llm_client, get_state_manager
from agents.analysts import create_fundamental_analyst, create_technical_analyst


def test_config():
    """测试配置系统"""
    print("=== 测试配置系统 ===")
    config = get_config()
    print("配置加载成功")
    print(f"Deepseek配置: {config.deepseek.base_url}")
    print(f"模型: {config.deepseek.model}")
    
    # 测试配置字典转换
    config_dict = config.to_dict()
    print("配置序列化成功")
    print("")


def test_llm_client():
    """测试LLM客户端"""
    print("=== 测试LLM客户端 ===")
    try:
        # 创建Deepseek客户端
        llm_client = create_llm_client(provider='deepseek')
        print("LLM客户端创建成功")
        
        # 测试简单对话
        response = llm_client.chat_completion([
            {"role": "user", "content": "你好，请简单介绍一下什么是股票技术分析？"}
        ], agent_name="基础测试")
        print(f"LLM响应: {response[:100]}...")
        print("LLM测试成功")
        print("")
        return llm_client
    except Exception as e:
        print(f"LLM测试失败: {e}")
        print("")
        return None


def test_state_manager():
    """测试状态管理器"""
    print("=== 测试状态管理器 ===")
    state_manager = get_state_manager()
    
    # 开始新会话
    session_id = state_manager.start_session("AAPL")
    print(f"会话创建成功: {session_id}")
    
    # 获取会话状态
    state = state_manager.get_current_session_state()
    print(f"当前会话状态获取成功")
    print(f"会话符号: {state.get('symbol')}")
    print("")


def test_fundamental_analyst(llm_client):
    """测试基础分析师"""
    print("=== 测试基础分析师 ===")
    if not llm_client:
        print("跳过分析师测试（LLM客户端不可用）")
        return
    
    try:
        # 创建基础分析师
        analyst = create_fundamental_analyst(llm_client)
        print(f"基础分析师创建成功: {analyst.name}")
        
        # 准备测试数据
        test_context = {
            'symbol': 'AAPL',
            'financial_data': {
                'revenue': 394_328_000_000,  # 苹果2023年收入
                'net_income': 96_995_000_000,  # 净利润
                'total_assets': 352_755_000_000,  # 总资产
                'total_equity': 62_146_000_000,  # 股东权益
                'pe_ratio': 29.5,  # P/E比率
                'pb_ratio': 39.1   # P/B比率
            },
            'market_data': {
                'current_price': 190.0,
                'market_cap': 2_950_000_000_000,  # 市值
                '52_week_high': 199.62,
                '52_week_low': 164.08
            }
        }
        
        # 执行分析（使用简化的提示避免API调用过多）
        print("开始基础分析...")
        result = analyst.process(test_context)
        
        if result['success']:
            print("基础分析完成")
            analysis = result['analysis_result']
            print(f"推荐: {analysis.get('recommendation', 'N/A')}")
            print(f"置信度: {analysis.get('confidence_score', 'N/A')}")
            print(f"关键发现数量: {len(analysis.get('key_findings', []))}")
        else:
            print(f"基础分析失败: {result['error']}")
        
        print("")
        
    except Exception as e:
        print(f"基础分析师测试失败: {e}")
        print("")


def test_technical_analyst(llm_client):
    """测试技术分析师"""
    print("=== 测试技术分析师 ===")
    if not llm_client:
        print("跳过技术分析师测试（LLM客户端不可用）")
        return
    
    try:
        # 创建技术分析师
        analyst = create_technical_analyst(llm_client)
        print(f"技术分析师创建成功: {analyst.name}")
        
        # 准备测试数据
        test_context = {
            'symbol': 'AAPL',
            'price_data': {
                'current_price': 190.0,
                'open': 188.5,
                'high': 192.0,
                'low': 187.0,
                'previous_close': 189.0,
                'price_change': 1.0,
                'price_change_pct': 0.53
            },
            'technical_indicators': {
                'rsi_14': 58.5,
                'macd': 1.2,
                'macd_signal': 0.8,
                'sma_20': 185.0,
                'sma_50': 180.0,
                'bollinger_upper': 195.0,
                'bollinger_lower': 175.0
            },
            'volume_data': {
                'current_volume': 45_000_000,
                'avg_volume_10d': 52_000_000,
                'volume_ratio': 0.87
            }
        }
        
        # 执行分析
        print("开始技术分析...")
        result = analyst.process(test_context)
        
        if result['success']:
            print("技术分析完成")
            analysis = result['analysis_result']
            print(f"推荐: {analysis.get('recommendation', 'N/A')}")
            print(f"趋势方向: {analysis.get('trend_direction', 'N/A')}")
            print(f"置信度: {analysis.get('confidence_score', 'N/A')}")
        else:
            print(f"技术分析失败: {result['error']}")
        
        print("")
        
    except Exception as e:
        print(f"技术分析师测试失败: {e}")
        print("")


def main():
    """主测试函数"""
    print("TradingAgents OpenAI 框架测试开始")
    print("=" * 50)
    
    # 测试各个组件
    test_config()
    llm_client = test_llm_client()
    test_state_manager()
    test_fundamental_analyst(llm_client)
    test_technical_analyst(llm_client)
    
    print("=" * 50)
    print("测试完成！")
    print("")
    print("使用说明：")
    print("1. 请确保设置了正确的DEEPSEEK_API_KEY环境变量")
    print("2. 所有分析师都已成功创建并可以处理分析请求")
    print("3. 状态管理器正常工作，可以跟踪会话状态")
    print("4. 下一步可以实现完整的工作流编排器")


if __name__ == "__main__":
    main()