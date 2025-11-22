"""
模拟数据源

用于测试和演示，不依赖外部API
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

from .base import BaseDataSource, MarketDataType

logger = logging.getLogger(__name__)


class MockDataSource(BaseDataSource):
    """模拟数据源（用于测试）"""

    def __init__(self):
        """初始化"""
        super().__init__("MockDataSource")
        logger.info("模拟数据源初始化成功")

        # 模拟股票数据库
        self.mock_stocks = {
            '600519': {
                'code': '600519',
                'name': '贵州茅台',
                'market': 'A',
                'exchange': 'SSE',
                'industry': '白酒',
                'listing_date': '2001-08-27',
                'total_share_capital': 125618 * 10000,  # 12.56亿股
            },
            '000858': {
                'code': '000858',
                'name': '五粮液',
                'market': 'A',
                'exchange': 'SZSE',
                'industry': '白酒',
                'listing_date': '1998-04-27',
                'total_share_capital': 387160 * 10000,  # 38.72亿股
            }
        }

    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        stock_code = self.normalize_stock_code(stock_code, market="A")
        return self.mock_stocks.get(stock_code)

    def get_daily_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """获取日行情数据（模拟）"""
        stock_code = self.normalize_stock_code(stock_code, market="A")

        if stock_code not in self.mock_stocks:
            return []

        # 生成模拟数据
        quotes = []
        current_date = start_date
        base_price = 1800.0 if stock_code == '600519' else 160.0

        while current_date <= end_date:
            # 跳过周末
            if current_date.weekday() < 5:
                # 模拟价格波动
                change = random.uniform(-0.03, 0.03)
                close_price = base_price * (1 + change)

                quotes.append({
                    'date': current_date,
                    'open': close_price * random.uniform(0.98, 1.02),
                    'high': close_price * random.uniform(1.00, 1.05),
                    'low': close_price * random.uniform(0.95, 1.00),
                    'close': close_price,
                    'volume': random.randint(100000, 500000),
                    'amount': close_price * random.randint(100000, 500000),
                    'change_pct': change * 100,
                })

            current_date += timedelta(days=1)

        return quotes

    def get_valuation_metrics(
        self,
        stock_code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """获取估值指标数据（模拟）"""
        stock_code = self.normalize_stock_code(stock_code, market="A")

        if stock_code not in self.mock_stocks:
            return []

        stock_info = self.mock_stocks[stock_code]
        quotes = self.get_daily_quotes(stock_code, start_date, end_date)

        metrics = []
        for quote in quotes:
            market_cap = quote['close'] * stock_info['total_share_capital']
            metrics.append({
                'date': quote['date'],
                'pe_ratio': random.uniform(30, 40) if stock_code == '600519' else random.uniform(25, 35),
                'pb_ratio': random.uniform(8, 12) if stock_code == '600519' else random.uniform(5, 8),
                'ps_ratio': random.uniform(10, 15),
                'market_cap': market_cap,
                'circulating_market_cap': market_cap * 0.9,
            })

        return metrics

    def get_dividend_data(
        self,
        stock_code: str,
        start_year: int,
        end_year: int
    ) -> List[Dict[str, Any]]:
        """获取分红数据（模拟）"""
        stock_code = self.normalize_stock_code(stock_code, market="A")

        if stock_code not in self.mock_stocks:
            return []

        dividends = []

        # 茅台：高分红
        if stock_code == '600519':
            base_dividend = 23.0
            for year in range(start_year, end_year + 1):
                dividends.append({
                    'year': year,
                    'dividend_per_share': base_dividend + (year - start_year) * 2.5,
                    'dividend_ratio': 0.72,
                    'ex_dividend_date': f'{year}-07-15',
                    'payment_date': f'{year}-07-16',
                    'bonus_share_ratio': 0,
                })

        # 五粮液：中等分红
        elif stock_code == '000858':
            base_dividend = 20.0
            for year in range(start_year, end_year + 1):
                dividends.append({
                    'year': year,
                    'dividend_per_share': base_dividend + (year - start_year) * 2.0,
                    'dividend_ratio': 0.65,
                    'ex_dividend_date': f'{year}-06-20',
                    'payment_date': f'{year}-06-21',
                    'bonus_share_ratio': 0,
                })

        return dividends

    def get_market_cap_history(
        self,
        stock_code: str,
        years: int = 5
    ) -> List[Dict[str, Any]]:
        """获取历史市值数据（每年年底）"""
        stock_code = self.normalize_stock_code(stock_code, market="A")

        if stock_code not in self.mock_stocks:
            return []

        stock_info = self.mock_stocks[stock_code]
        result = []

        current_year = datetime.now().year

        # 茅台：逐年增长的市值
        if stock_code == '600519':
            prices = [1200, 1350, 1600, 1850, 2000]  # 最近5年年底价格
        # 五粮液
        else:
            prices = [100, 120, 140, 155, 165]

        for i in range(years):
            year = current_year - years + i + 1
            price = prices[i] if i < len(prices) else prices[-1]

            result.append({
                'year': year,
                'date': date(year, 12, 31),
                'close': price,
                'market_cap': price * stock_info['total_share_capital'],
            })

        return result
