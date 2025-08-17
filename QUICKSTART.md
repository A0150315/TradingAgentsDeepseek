# TradingAgents OpenAI Framework - 快速开始指南

## 🚀 快速开始

### 1. 安装依赖

```bash
cd trading_agents_openai
pip install -r requirements.txt
```

### 2. 配置API密钥

创建 `.env` 文件或设置环境变量：

```bash
# Deepseek API配置
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_MODEL="deepseek-chat"
```

### 3. 运行演示

```bash
# 基础功能测试
python examples/basic_test.py

# 完整演示
python examples/full_demo.py
```

## 📋 功能特性

### ✅ 已实现功能

1. **核心框架**
   - 配置管理系统
   - 状态管理器
   - 基础Agent类
   - LLM客户端（支持OpenAI和Deepseek）

2. **分析师团队**
   - 基础分析师（财务数据分析）
   - 技术分析师（技术指标分析）
   - 情绪分析师（市场情绪分析）
   - 新闻分析师（新闻事件分析）

3. **研究团队**
   - 多头研究员（看涨分析）
   - 空头研究员（看跌分析）
   - 辩论协调器（管理辩论流程）

4. **工作流编排**
   - 完整的交易决策流程
   - 多智能体协作
   - 结构化通信协议

### 🔄 待实现功能

1. **交易员Agent**
   - 执行交易决策
   - 风险控制
   - 仓位管理

2. **风险管理团队**
   - 风险评估
   - 风险缓解
   - 合规检查

3. **数据接口**
   - 实时市场数据
   - 新闻数据源
   - 社交媒体数据

## 🎯 使用示例

### 基础使用

```python
from core import create_workflow_orchestrator

# 创建工作流编排器
orchestrator = create_workflow_orchestrator()

# 执行交易分析
result = orchestrator.execute_trading_workflow(
    symbol="AAPL",
    market_data={
        'financial_data': {...},
        'technical_indicators': {...},
        'sentiment_data': {...}
    }
)

# 查看结果
print(f"投资建议: {result['final_decision']['recommendation']}")
print(f"置信度: {result['final_decision']['confidence']}")
```

### 高级配置

```python
from core import Config

# 自定义配置
config = Config()
config.deepseek.model = "deepseek-chat"
config.debate.max_rounds = 5
config.trading.max_position_size = 0.2

# 使用自定义配置
orchestrator = create_workflow_orchestrator(config)
```

## 📊 输出示例

```
=========================================
 TradingAgents OpenAI 框架演示
=========================================

🔍 第一阶段：分析师团队分析
  📈 运行基础分析师...
    ✅ 基础分析完成
  📊 运行技术分析师...
    ✅ 技术分析完成
  😊 运行情绪分析师...
    ✅ 情绪分析完成
  📰 运行新闻分析师...
    ✅ 新闻分析完成

💬 第二阶段：研究团队辩论
开始 AAPL 的研究团队辩论...
辩论第 1 轮:
多头: 基于强劲的财务表现和技术突破...
空头: 尽管基本面看似强劲，但估值过高...
辩论第 2 轮:
多头: 空头忽视了长期增长潜力...
空头: 多头过于乐观，忽视了竞争风险...

📊 第三阶段：综合决策
辩论结论: BUY
决策置信度: 0.75

=========================================
 最终投资决策
=========================================
📊 股票代码: AAPL
🎯 投资建议: BUY
🔍 置信度: 73%
📝 决策说明: 基于4个分析师报告和研究团队辩论...
```

## 🛠️ 开发指南

### 扩展新的分析师

```python
from core.agent_base import AnalystAgent

class CustomAnalyst(AnalystAgent):
    def __init__(self, llm_client):
        super().__init__(
            role=AgentRole.CUSTOM_ANALYST,
            name="自定义分析师",
            llm_client=llm_client
        )
    
    def process(self, context):
        # 实现自定义分析逻辑
        pass
```

### 自定义辩论流程

```python
from communication.debate_coordinator import DebateCoordinator

coordinator = DebateCoordinator(
    bull_researcher=bull_researcher,
    bear_researcher=bear_researcher,
    judge_llm=judge_llm,
    max_rounds=5  # 自定义辩论轮数
)
```

## 🔧 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | Deepseek API密钥 | 必需 |
| `DEEPSEEK_BASE_URL` | API基础URL | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-chat` |

### 配置文件

```json
{
  "deepseek": {
    "model": "deepseek-chat",
    "max_tokens": 4000,
    "temperature": 0.7
  },
  "debate": {
    "max_rounds": 3,
    "research_team_max_rounds": 3
  },
  "trading": {
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "max_position_size": 0.1
  }
}
```

## 📝 注意事项

1. **API密钥安全**：请妥善保管API密钥，不要提交到版本控制系统
2. **成本控制**：每次完整分析大约消耗10-20个API调用
3. **数据准确性**：当前使用模拟数据，实际使用需接入真实数据源
4. **投资风险**：本框架仅供研究和教育用途，不构成投资建议

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

本项目采用 MIT 许可证