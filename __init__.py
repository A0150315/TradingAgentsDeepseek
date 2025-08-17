"""
TradingAgents OpenAI Framework
基于OpenAI原生库的多智能体股票交易框架

主要特性：
- 多智能体协作分析
- 结构化通信协议  
- 论文驱动的架构设计
- 支持多种LLM提供者
- 完整的交易工作流
- Deepseek API集成
"""
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from core.config import Config
from core.workflow import WorkflowOrchestrator
from core.state_manager import get_state_manager
from data.providers.market_data_provider import create_data_adapter

__version__ = "0.1.0"
__author__ = "TradingAgents Team"
__license__ = "MIT"


class TradingAgentsFramework:
    """TradingAgents框架主类"""
    
    def __init__(self, config: Optional[Config] = None):
        """初始化框架
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        self.config = config or Config()
        self.state_manager = get_state_manager()
        self.data_adapter = create_data_adapter(self.config.to_dict())
        self.workflow_orchestrator = WorkflowOrchestrator(self.config)
        
        # 验证配置
        self._validate_setup()
        
        print("🚀 TradingAgents Framework 初始化完成")
        print(f"   - LLM提供者: {self.config.deepseek.base_url}")
        print(f"   - 模型: {self.config.deepseek.model}")
        print(f"   - 数据模式: {'在线' if self.config.data.market_data_provider == 'online' else '离线'}")
    
    def _validate_setup(self):
        """验证系统设置"""
        if not self.config.deepseek.api_key:
            raise ValueError("缺少API密钥：请设置环境变量 DEEPSEEK_API_KEY")
        
        print("✅ 系统配置验证通过")
    
    def analyze_stock(
        self,
        symbol: str,
        selected_analysts: Optional[List[str]] = None,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析股票并生成交易建议
        
        Args:
            symbol: 股票代码 (e.g., 'AAPL', 'GOOGL')
            selected_analysts: 选择的分析师列表，默认为['fundamental', 'technical', 'sentiment', 'news']
            market_data: 外部市场数据，如果为None则自动获取
            
        Returns:
            包含完整分析结果和交易建议的字典
        """
        print(f"\n🔍 开始分析股票: {symbol}")
        print("=" * 60)
        
        # 设置默认分析师
        if selected_analysts is None:
            selected_analysts = ['fundamental', 'technical', 'sentiment', 'news']
        
        # 获取市场数据
        if market_data is None:
            print("📊 获取市场数据...")
            market_data = self._get_comprehensive_market_data(symbol)
        
        # 执行工作流
        result = self.workflow_orchestrator.execute_trading_workflow(
            symbol=symbol,
            market_data=market_data,
            selected_analysts=selected_analysts
        )
        
        if result['success']:
            print(f"\n✅ 分析完成: {symbol}")
            print(f"   - 最终建议: {result['final_decision']['recommendation']}")
            print(f"   - 置信度: {result['final_decision']['confidence']:.2f}")
            print(f"   - 会话ID: {result['session_id']}")
        else:
            print(f"\n❌ 分析失败: {result['error']}")
        
        return result
    
    def _get_comprehensive_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取全面的市场数据"""
        try:
            # 获取基础市场数据
            market_data = self.data_adapter.get_market_data(symbol)
            
            # 获取新闻数据
            news_data = self.data_adapter.get_news_data(symbol)
            
            # 获取基本面数据
            fundamental_data = self.data_adapter.get_fundamental_data(symbol)
            
            # 获取情感数据
            sentiment_data = self.data_adapter.get_sentiment_data(symbol)
            
            # 整合所有数据
            comprehensive_data = {
                'symbol': symbol,
                'market_data': market_data,
                'news_data': news_data,
                'fundamental_data': fundamental_data,
                'sentiment_data': sentiment_data,
                'timestamp': datetime.now().isoformat()
            }
            
            return comprehensive_data
            
        except Exception as e:
            print(f"⚠️ 获取市场数据时出错: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_connection(self) -> bool:
        """测试API连接
        
        Returns:
            连接是否成功
        """
        try:
            from core.agent_base import create_llm_client
            
            client = create_llm_client('deepseek', self.config)
            
            # 发送测试请求
            response = client.chat_completion([
                {"role": "system", "content": "你是一个测试助手"},
                {"role": "user", "content": "请简单回复：测试成功"}
            ], agent_name="系统测试")
            
            if response and "测试成功" in response:
                print("✅ API连接测试成功")
                return True
            else:
                print("❌ API连接测试失败：响应异常")
                return False
                
        except Exception as e:
            print(f"❌ API连接测试失败: {str(e)}")
            return False


# 核心模块导入
from core import (
    Config,
    get_config,
    set_config,
    StateManager,
    get_state_manager,
    AgentRole,
    MessageType,
    BaseAgent,
    AnalystAgent,
    ResearcherAgent,
    LLMClient,
    create_llm_client,
    create_workflow_orchestrator
)

# 分析师团队导入
try:
    from agents.analysts import (
        FundamentalAnalyst,
        TechnicalAnalyst,
        SentimentAnalyst,
        NewsAnalyst,
        create_fundamental_analyst,
        create_technical_analyst,
        create_sentiment_analyst,
        create_news_analyst
    )
except ImportError as e:
    print(f"Warning: 分析师模块导入失败: {e}")

# 便捷函数
def create_framework(config: Optional[Config] = None) -> TradingAgentsFramework:
    """创建框架实例"""
    return TradingAgentsFramework(config)


def quick_analyze(symbol: str, api_key: str = None) -> str:
    """快速分析单个股票"""
    if api_key:
        os.environ['DEEPSEEK_API_KEY'] = api_key
    
    framework = create_framework()
    result = framework.analyze_stock(symbol, selected_analysts=['technical'])
    
    if result['success']:
        decision = result['final_decision']
        return f"{symbol}: {decision['recommendation']} (置信度: {decision['confidence']:.2f})"
    else:
        return f"{symbol}: 分析失败 - {result['error']}"


def quick_start(symbol: str = "AAPL", api_key: str = None) -> dict:
    """快速开始函数
    
    Args:
        symbol: 股票代码
        api_key: API密钥
        
    Returns:
        分析结果
    """
    # 设置API密钥
    if api_key:
        os.environ['DEEPSEEK_API_KEY'] = api_key
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        return {
            'success': False,
            'error': '请设置DEEPSEEK_API_KEY环境变量或传入api_key参数'
        }
    
    try:
        # 创建框架
        framework = create_framework()
        
        # 测试连接
        if not framework.test_connection():
            return {
                'success': False,
                'error': 'API连接失败，请检查网络和密钥'
            }
        
        # 分析股票
        result = framework.analyze_stock(symbol, selected_analysts=['technical'])
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_framework_info() -> dict:
    """获取框架信息"""
    return {
        'name': 'TradingAgents OpenAI Framework',
        'version': __version__,
        'author': __author__,
        'license': __license__,
        'description': '基于OpenAI原生库的多智能体股票交易框架',
        'features': [
            '多智能体协作分析',
            '结构化通信协议',
            '论文驱动的架构设计', 
            '支持Deepseek API',
            '完整的工作流编排',
            '可扩展的插件架构'
        ],
        'agents': [
            '基础分析师 (Fundamental Analyst)',
            '技术分析师 (Technical Analyst)', 
            '情绪分析师 (Sentiment Analyst)',
            '新闻分析师 (News Analyst)',
            '多头研究员 (Bull Researcher)',
            '空头研究员 (Bear Researcher)',
            '交易员 (Trader)',
            '风险管理团队 (Risk Management Team)'
        ]
    }


__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    '__license__',
    
    # 主要类
    'TradingAgentsFramework',
    
    # 便捷函数
    'create_framework',
    'quick_analyze', 
    'quick_start',
    'get_framework_info',
    
    # 核心模块
    'Config',
    'get_config',
    'set_config', 
    'StateManager',
    'get_state_manager',
    'AgentRole',
    'MessageType',
    'BaseAgent',
    'AnalystAgent',
    'ResearcherAgent',
    'LLMClient',
    'create_llm_client',
    'create_workflow_orchestrator'
]


# 示例用法
if __name__ == "__main__":
    # 设置API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("请设置环境变量 DEEPSEEK_API_KEY")
        exit(1)
    
    # 快速开始
    result = quick_start('AAPL', api_key)
    print(f"分析结果: {result}")