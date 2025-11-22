"""
数据源模块

支持多种数据源：
- AkShare: A股市场数据（免费）
- yfinance: 美股、港股数据（免费）
- MockDataSource: 模拟数据源（测试用）
"""

from .base import BaseDataSource, MarketDataType
from .mock_source import MockDataSource

# 可选导入 AkShare（如果已安装）
try:
    from .akshare_source import AkShareSource
    _has_akshare = True
except ImportError:
    _has_akshare = False
    AkShareSource = None

__all__ = [
    'BaseDataSource',
    'MarketDataType',
    'MockDataSource',
]

if _has_akshare:
    __all__.append('AkShareSource')
