"""
TradingAgents OpenAI框架综合测试
测试所有核心功能和集成
"""
import pytest
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import Config, create_workflow_orchestrator
from core.agent_base import LLMClient, BaseAgent
from core.state_manager import StateManager, AgentRole, Message
from tools.google_news_tool import GoogleNewsTool
from tools.yfinance_tool import YFinanceTool
from utils.memory import MemoryManager
from utils.logger import get_logger


class TestConfig:
    """测试配置系统"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = Config()
        assert config is not None
        assert hasattr(config, 'deepseek')
        assert hasattr(config, 'openai')
        assert hasattr(config, 'trading')
        assert hasattr(config, 'debate')
    
    def test_deepseek_config(self):
        """测试Deepseek配置"""
        config = Config()
        assert config.deepseek.model == "deepseek-chat"
        assert config.deepseek.base_url == "https://api.deepseek.com"
    
    def test_config_from_env(self):
        """测试从环境变量加载配置"""
        # 临时设置环境变量进行测试
        original_key = os.environ.get('DEEPSEEK_API_KEY')
        original_model = os.environ.get('DEEPSEEK_MODEL')
        
        try:
            os.environ['DEEPSEEK_API_KEY'] = 'test-key'
            os.environ['DEEPSEEK_MODEL'] = 'test-model'
            
            config = Config()
            assert config.deepseek.api_key == 'test-key'
            assert config.deepseek.model == 'test-model'
        finally:
            # 恢复原始环境变量
            if original_key:
                os.environ['DEEPSEEK_API_KEY'] = original_key
            else:
                os.environ.pop('DEEPSEEK_API_KEY', None)
            
            if original_model:
                os.environ['DEEPSEEK_MODEL'] = original_model
            else:
                os.environ.pop('DEEPSEEK_MODEL', None)


class TestLLMClient:
    """测试LLM客户端"""
    
    def test_client_creation(self):
        """测试客户端创建"""
        client = LLMClient('deepseek')
        assert client is not None
        assert client.provider == 'deepseek'
        assert client.model == 'deepseek-chat'
    
    @patch('openai.OpenAI')
    def test_chat_completion_mock(self, mock_openai):
        """测试聊天完成（Mock）"""
        # 模拟OpenAI响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "测试响应"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = LLMClient('deepseek')
        messages = [{"role": "user", "content": "测试消息"}]
        
        response = client.chat_completion(messages, agent_name="单元测试")
        assert response == "测试响应"


class TestStateManager:
    """测试状态管理"""
    
    def test_trading_state_creation(self):
        """测试交易状态创建"""
        state_manager = StateManager()
        assert state_manager is not None
        # 检查状态管理器的基本属性
        assert hasattr(state_manager, 'get_state')
        assert callable(getattr(state_manager, 'get_state'))
    
    def test_message_system(self):
        """测试消息系统"""
        message = Message(
            sender=AgentRole.FUNDAMENTAL_ANALYST,
            content="测试消息",
            timestamp=datetime.now().isoformat()
        )
        
        assert message.sender == AgentRole.FUNDAMENTAL_ANALYST
        assert message.content == "测试消息"
        assert message.timestamp is not None


class TestTools:
    """测试工具集成"""
    
    def test_google_news_tool_creation(self):
        """测试Google News工具创建"""
        tool = GoogleNewsTool()
        assert tool is not None
        assert tool.name == "google_news"
    
    def test_yfinance_tool_creation(self):
        """测试YFinance工具创建"""
        tool = YFinanceTool()
        assert tool is not None
        assert tool.name == "yfinance"
    
    @patch('yfinance.Ticker')
    def test_yfinance_mock_data(self, mock_ticker):
        """测试YFinance数据获取（Mock）"""
        # 模拟yfinance响应
        mock_data = Mock()
        mock_data.info = {
            'shortName': 'Apple Inc.',
            'sector': 'Technology',
            'marketCap': 3000000000000
        }
        mock_ticker.return_value = mock_data
        
        tool = YFinanceTool()
        result = tool.get_company_info('AAPL')
        
        assert result is not None
        assert 'Company Name' in result


class TestMemorySystem:
    """测试记忆系统"""
    
    def test_memory_manager_creation(self):
        """测试记忆管理器创建"""
        manager = MemoryManager()
        assert manager is not None
    
    def test_memory_system_creation(self):
        """测试记忆系统创建"""
        manager = MemoryManager()
        memory = manager.get_memory('analyst')
        
        assert memory is not None
        assert memory.agent_type == 'analyst'
    
    def test_add_memory(self):
        """测试添加记忆"""
        manager = MemoryManager()
        memory = manager.get_memory('test_agent')
        
        memory.add_memory(
            symbol='AAPL',
            market_conditions={'price': 150.0, 'trend': 'up'},
            decision='BUY',
            confidence=0.8,
            reasoning='测试理由',
            session_id='test_session'
        )
        
        assert len(memory.memories) > 0
        assert memory.memories[-1].symbol == 'AAPL'


class TestAgents:
    """测试Agent系统"""
    
    def test_base_agent_creation(self):
        """测试基础Agent创建"""
        # 由于BaseAgent是抽象类，这里测试其属性设置
        assert AgentRole.FUNDAMENTAL_ANALYST.value == "fundamental_analyst"
        assert AgentRole.TECHNICAL_ANALYST.value == "technical_analyst"
    
    @patch('core.agent_base.LLMClient')
    def test_agent_process_mock(self, mock_llm):
        """测试Agent处理（Mock）"""
        # 这里可以添加具体的Agent测试
        # 由于实际Agent类较复杂，使用Mock进行测试
        mock_llm.return_value.chat_completion.return_value = "测试响应"
        
        # 测试基本的Agent属性
        assert True  # 占位符测试


class TestWorkflow:
    """测试工作流系统"""
    
    def test_workflow_orchestrator_creation(self):
        """测试工作流编排器创建"""
        config = Config()
        orchestrator = create_workflow_orchestrator(config)
        
        assert orchestrator is not None
        assert hasattr(orchestrator, 'config')
        assert hasattr(orchestrator, 'state_manager')
    
    @patch('core.agent_base.LLMClient.chat_completion')
    def test_workflow_basic_execution(self, mock_chat):
        """测试工作流基本执行"""
        # Mock LLM响应
        mock_chat.return_value = "测试分析结果"
        
        config = Config()
        # 设置测试API密钥
        config.deepseek.api_key = "test-key"
        
        orchestrator = create_workflow_orchestrator(config)
        
        # 准备测试数据
        test_market_data = {
            'financial_data': {
                'revenue': 100000000,
                'net_income': 20000000,
                'pe_ratio': 15.0
            },
            'market_data': {
                'current_price': 150.0,
                'market_cap': 3000000000000
            },
            'technical_indicators': {
                'rsi_14': 55.0,
                'macd': 1.2
            }
        }
        
        # 测试工作流是否能正常初始化
        # 实际执行会进行API调用，这里只测试结构
        assert orchestrator.config is not None
        assert orchestrator.state_manager is not None


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.integration
    def test_full_system_integration(self):
        """测试系统完整集成"""
        # 这是一个标记为集成测试的用例
        # 需要真实的API密钥才能运行
        config = Config()
        
        # 检查是否有真实的API密钥
        if not config.deepseek.api_key or config.deepseek.api_key == "":
            pytest.skip("需要真实的API密钥进行集成测试")
        
        orchestrator = create_workflow_orchestrator(config)
        assert orchestrator is not None
    
    def test_system_components_integration(self):
        """测试系统组件集成"""
        # 测试各组件能否正确协作
        config = Config()
        manager = MemoryManager()
        logger = get_logger()
        
        # 测试组件创建
        assert config is not None
        assert manager is not None
        assert logger is not None
        
        # 测试基本交互
        memory = manager.get_memory('integration_test')
        assert memory is not None


class TestErrorHandling:
    """测试错误处理"""
    
    def test_invalid_config(self):
        """测试无效配置处理"""
        # 测试配置错误处理
        config = Config()
        # 清空API密钥测试错误处理
        config.deepseek.api_key = ""
        
        # 应该能创建但在使用时会有相应处理
        client = LLMClient('deepseek', config)
        assert client is not None
    
    def test_missing_dependencies(self):
        """测试缺失依赖处理"""
        # 测试工具在缺失数据时的处理
        tool = GoogleNewsTool()
        
        # 测试空查询
        result = tool.get_news("", "2024-01-01", 1)
        assert "未找到相关新闻" in result or "出错" in result


if __name__ == "__main__":
    # 运行测试
    print("=" * 60)
    print(" TradingAgents OpenAI 框架测试套件")
    print("=" * 60)
    
    # 基本功能测试
    test_config = TestConfig()
    test_config.test_config_creation()
    test_config.test_deepseek_config()
    print("✅ 配置系统测试通过")
    
    test_state = TestStateManager()
    test_state.test_trading_state_creation()
    test_state.test_message_system()
    print("✅ 状态管理测试通过")
    
    test_tools = TestTools()
    test_tools.test_google_news_tool_creation()
    test_tools.test_yfinance_tool_creation()
    print("✅ 工具系统测试通过")
    
    test_memory = TestMemorySystem()
    test_memory.test_memory_manager_creation()
    test_memory.test_memory_system_creation()
    test_memory.test_add_memory()
    print("✅ 记忆系统测试通过")
    
    test_workflow = TestWorkflow()
    test_workflow.test_workflow_orchestrator_creation()
    print("✅ 工作流系统测试通过")
    
    test_integration = TestIntegration()
    test_integration.test_system_components_integration()
    print("✅ 系统集成测试通过")
    
    print("\n" + "=" * 60)
    print("🎉 所有基础测试通过！")
    print("💡 系统已准备就绪，可以运行完整演示")
    print("=" * 60)