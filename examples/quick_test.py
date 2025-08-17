#!/usr/bin/env python3
"""
TradingAgents OpenAI 框架快速测试
测试基础功能是否正常工作
"""
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

def test_imports():
    """测试导入是否正常"""
    print("🧪 测试模块导入...")
    try:
        from core import Config, create_workflow_orchestrator
        print("✅ 核心模块导入成功")
        
        from tools.google_news_tool import GoogleNewsTool
        print("✅ Google News工具导入成功")
        
        from tools.yfinance_tool import YFinanceTool
        print("✅ YFinance工具导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_config():
    """测试配置是否正常"""
    print("\n🧪 测试配置系统...")
    try:
        from core import Config
        config = Config()
        print(f"✅ 配置创建成功 (Deepseek模型: {config.deepseek.model})")
        print(f"✅ API密钥已配置: {'已设置' if config.deepseek.api_key else '未设置'}")
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_tools():
    """测试工具是否正常"""
    print("\n🧪 测试工具系统...")
    try:
        from tools.yfinance_tool import create_yfinance_tool
        yf_tool = create_yfinance_tool()
        print("✅ YFinance工具创建成功")
        
        from tools.google_news_tool import create_google_news_tool
        news_tool = create_google_news_tool()
        print("✅ Google News工具创建成功")
        
        return True
    except Exception as e:
        print(f"❌ 工具测试失败: {e}")
        return False

def test_workflow_creation():
    """测试工作流创建"""
    print("\n🧪 测试工作流创建...")
    try:
        from core import Config, create_workflow_orchestrator
        config = Config()
        orchestrator = create_workflow_orchestrator(config)
        print("✅ 工作流编排器创建成功")
        return True
    except Exception as e:
        print(f"❌ 工作流创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print(" TradingAgents OpenAI 框架快速测试")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config, 
        test_tools,
        test_workflow_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f" 测试结果: {passed}/{total} 测试通过")
    print("=" * 60)
    
    if passed == total:
        print("🎉 所有基础功能测试通过！")
        print("💡 系统已准备就绪，可以运行完整演示")
        return True
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)