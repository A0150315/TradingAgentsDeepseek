# TradingAgents OpenAI Framework

基于论文《TradingAgents: Multi-Agents LLM Financial Trading Framework》实现的多智能体股票交易框架，使用原生OpenAI库构建。

## 架构设计

### 核心特性
- 7个专业角色的智能体：基础分析师、情绪分析师、新闻分析师、技术分析师、研究员、交易员、风险管理员
- 结构化通信协议，避免"电话游戏"效应
- 分层决策流程，模拟真实交易公司运作
- 支持多轮辩论和深度思考

### 目录结构
```
trading_agents_openai/
├── core/                    # 核心框架
│   ├── __init__.py
│   ├── agent_base.py       # 基础Agent类
│   ├── config.py           # 配置管理
│   ├── state_manager.py    # 状态管理
│   └── workflow.py         # 工作流编排
├── agents/                  # 各种智能体
│   ├── __init__.py
│   ├── analysts/           # 分析师团队
│   │   ├── __init__.py
│   │   ├── fundamental_analyst.py
│   │   ├── sentiment_analyst.py
│   │   ├── news_analyst.py
│   │   └── technical_analyst.py
│   ├── researchers/        # 研究团队
│   │   ├── __init__.py
│   │   ├── bull_researcher.py
│   │   └── bear_researcher.py
│   ├── trader/             # 交易员
│   │   ├── __init__.py
│   │   └── trader.py
│   └── risk_management/    # 风险管理团队
│       ├── __init__.py
│       ├── risky_analyst.py
│       ├── neutral_analyst.py
│       ├── safe_analyst.py
│       └── risk_manager.py
├── communication/          # 通信协议
│   ├── __init__.py
│   ├── protocols.py        # 通信协议定义
│   └── message_types.py    # 消息类型
├── data/                   # 数据层
│   ├── __init__.py
│   ├── adapters/           # 数据适配器
│   │   ├── __init__.py
│   │   ├── market_data.py
│   │   ├── news_data.py
│   │   └── sentiment_data.py
│   └── providers/          # 数据提供者
│       ├── __init__.py
│       └── base_provider.py
├── utils/                  # 工具类
│   ├── __init__.py
│   ├── logging.py
│   ├── metrics.py
│   └── helpers.py
├── tests/                  # 测试
│   ├── __init__.py
│   └── test_agents.py
├── examples/               # 示例
│   ├── __init__.py
│   └── basic_trading.py
└── requirements.txt        # 依赖
```

## 使用方法

1. 安装依赖：`pip install -r requirements.txt`
2. 配置API密钥和参数
3. 运行示例：`python examples/basic_trading.py`

## 配置

支持通过配置文件或环境变量设置：
- OpenAI API配置
- 交易策略参数
- 风险管理参数
- 数据源配置