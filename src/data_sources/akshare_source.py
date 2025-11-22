"""
AkShare 数据源

使用 AkShare 获取 A 股市场数据
文档: https://akshare.akfamily.xyz/
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from .base import BaseDataSource, MarketDataType

logger = logging.getLogger(__name__)


class AkShareSource(BaseDataSource):
    """AkShare 数据源"""

    def __init__(self):
        """初始化"""
        super().__init__("AkShare")
        self._check_akshare()

    def _check_akshare(self):
        """检查 AkShare 是否已安装"""
        try:
            import akshare as ak
            self.ak = ak
            logger.info("AkShare 数据源初始化成功")
        except ImportError:
            logger.error("AkShare 未安装，请运行: pip install akshare")
            raise ImportError(
                "AkShare 未安装。请运行: pip install akshare\n"
                "或者: pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple"
            )

    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息

        Args:
            stock_code: 股票代码（6位数字，如 "600519"）

        Returns:
            股票信息字典
        """
        try:
            stock_code = self.normalize_stock_code(stock_code, market="A")

            # 获取股票基本信息
            # 使用 stock_individual_info_em 获取个股信息
            df = self.ak.stock_individual_info_em(symbol=stock_code)

            if df is None or df.empty:
                logger.warning(f"未找到股票信息: {stock_code}")
                return None

            # 转换为字典格式
            info_dict = dict(zip(df['item'], df['value']))

            # 确定交易所
            if stock_code.startswith('6'):
                exchange = 'SSE'  # 上海证券交易所
            elif stock_code.startswith(('0', '3')):
                exchange = 'SZSE'  # 深圳证券交易所
            else:
                exchange = 'UNKNOWN'

            return {
                'code': stock_code,
                'name': info_dict.get('股票简称', ''),
                'market': 'A',
                'exchange': exchange,
                'industry': info_dict.get('所处行业', ''),
                'listing_date': info_dict.get('上市时间', None),
                'total_share_capital': info_dict.get('总股本', None),
                'circulating_share_capital': info_dict.get('流通股', None),
            }

        except Exception as e:
            logger.error(f"获取股票信息失败 {stock_code}: {e}")
            return None

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
            日行情列表
        """
        try:
            stock_code = self.normalize_stock_code(stock_code, market="A")

            # 使用 stock_zh_a_hist 获取历史行情
            df = self.ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq"  # 前复权
            )

            if df is None or df.empty:
                logger.warning(f"未找到日行情数据: {stock_code}")
                return []

            # 转换为标准格式
            quotes = []
            for _, row in df.iterrows():
                quotes.append({
                    'date': datetime.strptime(row['日期'], '%Y-%m-%d').date(),
                    'open': float(row['开盘']),
                    'high': float(row['最高']),
                    'low': float(row['最低']),
                    'close': float(row['收盘']),
                    'volume': float(row['成交量']),
                    'amount': float(row['成交额']),
                    'change_pct': float(row['涨跌幅']) if '涨跌幅' in row else None,
                })

            logger.info(f"获取到 {len(quotes)} 条日行情数据: {stock_code}")
            return quotes

        except Exception as e:
            logger.error(f"获取日行情数据失败 {stock_code}: {e}")
            return []

    def get_valuation_metrics(
        self,
        stock_code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取估值指标数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            估值数据列表
        """
        try:
            stock_code = self.normalize_stock_code(stock_code, market="A")

            # 使用 stock_zh_valuation_baidu 获取估值数据
            # 注意: 这个接口可能需要调整，根据 AkShare 版本而定
            try:
                df = self.ak.stock_zh_valuation_baidu(
                    symbol=stock_code,
                    indicator="市盈率",
                    period="day"
                )
            except AttributeError:
                # 如果该接口不存在，尝试从历史数据中获取
                logger.warning(f"AkShare 没有 stock_zh_valuation_baidu 接口，尝试其他方法")
                # 可以从日行情和财务数据计算
                return self._calculate_valuation_from_quotes(stock_code, start_date, end_date)

            if df is None or df.empty:
                logger.warning(f"未找到估值数据: {stock_code}")
                return []

            # 转换为标准格式
            metrics = []
            for _, row in df.iterrows():
                date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date()

                # 只返回指定日期范围内的数据
                if start_date <= date_obj <= end_date:
                    metrics.append({
                        'date': date_obj,
                        'pe_ratio': float(row.get('pe', 0)) if row.get('pe') else None,
                        'pb_ratio': float(row.get('pb', 0)) if row.get('pb') else None,
                        'ps_ratio': float(row.get('ps', 0)) if row.get('ps') else None,
                        'market_cap': float(row.get('market_cap', 0)) if row.get('market_cap') else None,
                    })

            logger.info(f"获取到 {len(metrics)} 条估值数据: {stock_code}")
            return metrics

        except Exception as e:
            logger.error(f"获取估值数据失败 {stock_code}: {e}")
            return []

    def _calculate_valuation_from_quotes(
        self,
        stock_code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        从行情和财务数据计算估值指标

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            估值数据列表
        """
        # 获取日行情
        quotes = self.get_daily_quotes(stock_code, start_date, end_date)

        # 获取股票基本信息（总股本）
        stock_info = self.get_stock_info(stock_code)
        if not stock_info:
            return []

        total_shares = stock_info.get('total_share_capital')
        if not total_shares:
            logger.warning(f"无法获取总股本: {stock_code}")
            return []

        # 转换为数字（可能是字符串形式，如 "100.5亿"）
        try:
            if isinstance(total_shares, str):
                total_shares = float(total_shares.replace('亿', '')) * 1e8
            else:
                total_shares = float(total_shares)
        except (ValueError, AttributeError):
            logger.warning(f"总股本格式错误: {total_shares}")
            return []

        # 计算市值
        metrics = []
        for quote in quotes:
            market_cap = quote['close'] * total_shares
            metrics.append({
                'date': quote['date'],
                'pe_ratio': None,  # 需要财报数据计算
                'pb_ratio': None,  # 需要财报数据计算
                'ps_ratio': None,  # 需要财报数据计算
                'market_cap': market_cap,
            })

        return metrics

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
            分红数据列表
        """
        try:
            stock_code = self.normalize_stock_code(stock_code, market="A")

            # 使用 stock_dividend_cninfo 获取分红数据
            df = self.ak.stock_dividend_cninfo(symbol=stock_code)

            if df is None or df.empty:
                logger.warning(f"未找到分红数据: {stock_code}")
                return []

            # 转换为标准格式
            dividends = []
            for _, row in df.iterrows():
                # 提取年份
                report_year = None
                if '分红年度' in row:
                    try:
                        report_year = int(str(row['分红年度'])[:4])
                    except (ValueError, TypeError):
                        continue

                # 只返回指定年份范围内的数据
                if report_year and start_year <= report_year <= end_year:
                    dividends.append({
                        'year': report_year,
                        'dividend_per_share': float(row.get('每股分红', 0)) if row.get('每股分红') else 0,
                        'dividend_ratio': None,  # 需要结合净利润计算
                        'ex_dividend_date': row.get('除权除息日'),
                        'payment_date': row.get('股权登记日'),
                        'bonus_share_ratio': float(row.get('送股比例', 0)) if row.get('送股比例') else 0,
                    })

            logger.info(f"获取到 {len(dividends)} 条分红数据: {stock_code}")
            return dividends

        except Exception as e:
            logger.error(f"获取分红数据失败 {stock_code}: {e}")
            return []

    def get_market_cap_history(
        self,
        stock_code: str,
        years: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取历史市值数据（每年年底）

        Args:
            stock_code: 股票代码
            years: 年数

        Returns:
            市值历史数据列表，每个元素包含：
            - year: 年份
            - date: 具体日期（年底最后一个交易日）
            - market_cap: 市值
            - pe_ratio: 市盈率（如果有）
        """
        try:
            stock_code = self.normalize_stock_code(stock_code, market="A")

            # 计算日期范围
            end_date = date.today()
            start_date = date(end_date.year - years, 1, 1)

            # 获取日行情数据
            quotes = self.get_daily_quotes(stock_code, start_date, end_date)

            if not quotes:
                return []

            # 获取股票信息（总股本）
            stock_info = self.get_stock_info(stock_code)
            if not stock_info:
                return []

            total_shares = stock_info.get('total_share_capital')
            if not total_shares:
                return []

            # 转换总股本
            try:
                if isinstance(total_shares, str):
                    total_shares = float(total_shares.replace('亿', '')) * 1e8
                else:
                    total_shares = float(total_shares)
            except (ValueError, AttributeError):
                return []

            # 按年份分组，取每年最后一个交易日
            year_end_data = {}
            for quote in quotes:
                year = quote['date'].year
                if year not in year_end_data or quote['date'] > year_end_data[year]['date']:
                    year_end_data[year] = {
                        'year': year,
                        'date': quote['date'],
                        'close': quote['close'],
                        'market_cap': quote['close'] * total_shares,
                    }

            # 转换为列表并排序
            result = sorted(year_end_data.values(), key=lambda x: x['year'], reverse=True)

            logger.info(f"获取到 {len(result)} 年的市值数据: {stock_code}")
            return result

        except Exception as e:
            logger.error(f"获取市值历史失败 {stock_code}: {e}")
            return []
