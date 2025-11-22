"""
数据源基类

定义统一的数据源接口
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, date


class MarketDataType(Enum):
    """市场数据类型"""
    STOCK_INFO = "stock_info"  # 股票基本信息
    DAILY_QUOTE = "daily_quote"  # 日行情
    VALUATION = "valuation"  # 估值指标（PE、PB等）
    DIVIDEND = "dividend"  # 分红数据
    MARKET_CAP = "market_cap"  # 市值数据


class BaseDataSource(ABC):
    """数据源基类"""

    def __init__(self, name: str):
        """
        初始化

        Args:
            name: 数据源名称
        """
        self.name = name

    @abstractmethod
    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息

        Args:
            stock_code: 股票代码

        Returns:
            股票信息字典，包含：
            - code: 股票代码
            - name: 股票名称
            - market: 市场（A, HK, US）
            - exchange: 交易所
            - industry: 行业
            - listing_date: 上市日期
        """
        pass

    @abstractmethod
    def get_daily_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取日行情数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            日行情列表，每个元素包含：
            - date: 日期
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额
        """
        pass

    @abstractmethod
    def get_valuation_metrics(
        self,
        stock_code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取估值指标数据（PE、PB、市值等）

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            估值数据列表，每个元素包含：
            - date: 日期
            - pe_ratio: 市盈率
            - pb_ratio: 市净率
            - ps_ratio: 市销率
            - market_cap: 总市值
            - circulating_market_cap: 流通市值
        """
        pass

    @abstractmethod
    def get_dividend_data(
        self,
        stock_code: str,
        start_year: int,
        end_year: int
    ) -> List[Dict[str, Any]]:
        """
        获取分红数据

        Args:
            stock_code: 股票代码
            start_year: 开始年份
            end_year: 结束年份

        Returns:
            分红数据列表，每个元素包含：
            - year: 年份
            - dividend_per_share: 每股分红
            - dividend_ratio: 分红率（分红/净利润）
            - ex_dividend_date: 除权除息日
            - payment_date: 派息日
        """
        pass

    def is_available(self) -> bool:
        """
        检查数据源是否可用

        Returns:
            True 如果可用，False 否则
        """
        try:
            # 简单的可用性检查
            return True
        except Exception:
            return False

    def normalize_stock_code(self, stock_code: str, market: str = "A") -> str:
        """
        标准化股票代码格式

        Args:
            stock_code: 原始股票代码
            market: 市场类型

        Returns:
            标准化后的股票代码
        """
        # 移除空格
        stock_code = stock_code.strip().upper()

        if market == "A":
            # A股：6位数字
            stock_code = stock_code.replace("SH", "").replace("SZ", "")
            return stock_code.zfill(6)
        elif market == "HK":
            # 港股：5位数字
            stock_code = stock_code.replace("HK", "")
            return stock_code.zfill(5)
        elif market == "US":
            # 美股：字母代码
            return stock_code.upper()

        return stock_code
