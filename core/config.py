"""
核心配置管理模块
支持通过配置文件和环境变量进行配置
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class ProviderConfig:
    """通用LLM提供者配置"""

    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v3.1-latest"
    max_tokens: int = 32000
    temperature: float = 0
    timeout: int = 60


@dataclass
class TradingConfig:
    """交易配置"""

    symbols: list = field(default_factory=lambda: ["AAPL", "GOOGL", "MSFT"])
    initial_capital: float = 100000.0
    max_position_size: float = 0.1  # 最大仓位比例
    stop_loss_pct: float = 0.05  # 止损百分比
    take_profit_pct: float = 0.15  # 止盈百分比
    risk_free_rate: float = 0.03  # 无风险利率


@dataclass
class DebateConfig:
    """辩论配置"""

    max_rounds: int = 3
    research_team_max_rounds: int = 3
    risk_team_max_rounds: int = 3
    min_consensus_threshold: float = 0.6
    models: List[str] = field(default_factory=lambda: ['deepseek-v3.1-latest'])
    randomize_models: bool = False


@dataclass
class DataConfig:
    """数据配置"""

    market_data_provider: str = "online"  # 改为在线模式
    news_data_provider: str = "google_news"
    fundamental_data_provider: str = "yfinance"
    sentiment_data_provider: str = "mock"
    cache_enabled: bool = True
    cache_ttl: int = 300
    max_retries: int = 3
    timeout: int = 30
    online_tools: bool = True  # 启用在线工具
    data_dir: str = "./data"


class Config:
    """主配置类"""

    def __init__(self, config_file: Optional[str] = None):
        """初始化配置

        Args:
            config_file: 配置文件路径，如果为None则使用环境变量
        """
        self.deepseek = ProviderConfig()
        self.trading = TradingConfig()
        self.debate = DebateConfig()
        self.data = DataConfig()

        if config_file and Path(config_file).exists():
            self._load_from_file(config_file)
        else:
            self._load_from_env()

    def _load_from_file(self, config_file: str):
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        if "deepseek" in config_data:
            for key, value in config_data["deepseek"].items():
                if hasattr(self.deepseek, key):
                    setattr(self.deepseek, key, value)

        for section_name in ["trading", "debate", "data"]:
            if section_name in config_data:
                section = getattr(self, section_name)
                for key, value in config_data[section_name].items():
                    if hasattr(section, key):
                        setattr(section, key, value)

    def _load_from_env(self):
        if os.getenv("DEEPSEEK_API_KEY"):
            self.deepseek.api_key = os.getenv("DEEPSEEK_API_KEY")
        if os.getenv("DEEPSEEK_BASE_URL"):
            self.deepseek.base_url = os.getenv("DEEPSEEK_BASE_URL")
        if os.getenv("DEEPSEEK_MODEL"):
            self.deepseek.model = os.getenv("DEEPSEEK_MODEL")

        if os.getenv("TRADING_SYMBOLS"):
            self.trading.symbols = os.getenv("TRADING_SYMBOLS").split(",")
        if os.getenv("INITIAL_CAPITAL"):
            self.trading.initial_capital = float(os.getenv("INITIAL_CAPITAL"))

        if os.getenv("DEBATE_MODELS"):
            self.debate.models = [m.strip() for m in os.getenv("DEBATE_MODELS").split(",") if m.strip()]
        if os.getenv("DEBATE_RANDOMIZE_MODELS"):
            self.debate.randomize_models = os.getenv("DEBATE_RANDOMIZE_MODELS").lower() == "true"

    def get_llm_config(self, provider: str = "deepseek") -> Dict[str, Any]:
        return {
            "api_key": self.deepseek.api_key,
            "base_url": self.deepseek.base_url,
            "model": self.deepseek.model,
            "max_tokens": self.deepseek.max_tokens,
            "temperature": self.deepseek.temperature,
            "timeout": self.deepseek.timeout,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deepseek": {
                "api_key": "***" if self.deepseek.api_key else "",
                "base_url": self.deepseek.base_url,
                "model": self.deepseek.model,
                "max_tokens": self.deepseek.max_tokens,
                "temperature": self.deepseek.temperature,
                "timeout": self.deepseek.timeout,
            },
            "trading": {
                "symbols": self.trading.symbols,
                "initial_capital": self.trading.initial_capital,
                "max_position_size": self.trading.max_position_size,
                "stop_loss_pct": self.trading.stop_loss_pct,
                "take_profit_pct": self.trading.take_profit_pct,
                "risk_free_rate": self.trading.risk_free_rate,
            },
            "debate": {
                "max_rounds": self.debate.max_rounds,
                "research_team_max_rounds": self.debate.research_team_max_rounds,
                "risk_team_max_rounds": self.debate.risk_team_max_rounds,
                "min_consensus_threshold": self.debate.min_consensus_threshold,
                "models": self.debate.models,
                "randomize_models": self.debate.randomize_models,
            },
            "data": {
                "market_data_provider": self.data.market_data_provider,
                "news_data_provider": self.data.news_data_provider,
                "fundamental_data_provider": self.data.fundamental_data_provider,
                "sentiment_data_provider": self.data.sentiment_data_provider,
                "cache_enabled": self.data.cache_enabled,
                "cache_ttl": self.data.cache_ttl,
                "max_retries": self.data.max_retries,
                "timeout": self.data.timeout,
                "online_tools": self.data.online_tools,
                "data_dir": self.data.data_dir,
            },
        }

    def save_to_file(self, config_file: str):
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


# 全局配置实例
global_config = Config()


def get_config() -> Config:
    """获取全局配置实例"""
    return global_config


def set_config(config: Config):
    """设置全局配置实例"""
    global global_config
    global_config = config
