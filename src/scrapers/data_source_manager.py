"""
数据源管理器

支持多种财报数据源，自动切换
"""

from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import importlib
from ..utils.logger import get_logger


class DataSourceType(Enum):
    """数据源类型"""
    CNINFO = "cninfo"  # 巨潮资讯（默认）
    AKSHARE = "akshare"  # AkShare（可选）
    TUSHARE = "tushare"  # Tushare Pro（可选）
    CUSTOM = "custom"  # 自定义


class DataSource:
    """数据源基类"""

    def __init__(self, source_type: DataSourceType, name: str):
        self.source_type = source_type
        self.name = name
        self.logger = get_logger()
        self._available = None

    def is_available(self) -> bool:
        """检查数据源是否可用"""
        if self._available is not None:
            return self._available

        self._available = self._check_availability()
        return self._available

    def _check_availability(self) -> bool:
        """子类实现：检查数据源是否可用"""
        raise NotImplementedError

    def fetch_financial_data(self, stock_code: str, **kwargs) -> Optional[Dict[str, Any]]:
        """获取财务数据"""
        raise NotImplementedError


class CninfoDataSource(DataSource):
    """巨潮资讯数据源（默认）"""

    def __init__(self):
        super().__init__(DataSourceType.CNINFO, "巨潮资讯")

    def _check_availability(self) -> bool:
        """检查巨潮资讯爬虫是否可用"""
        try:
            from .cn_scraper import ChinaStockScraper
            return True
        except Exception as e:
            self.logger.warning(f"巨潮资讯数据源不可用: {e}")
            return False

    def fetch_financial_data(self, stock_code: str, **kwargs) -> Optional[Dict[str, Any]]:
        """通过巨潮资讯获取财报"""
        from .cn_scraper import ChinaStockScraper

        # 判断市场
        market = kwargs.get('market', 'A')
        if len(stock_code) == 5 or stock_code.startswith('0'):
            market = 'HK'

        scraper = ChinaStockScraper(market=market)

        try:
            # 获取财报列表
            announcements = scraper.scrape(stock_code, **kwargs)

            if not announcements:
                return None

            # 下载第一份财报
            first_report = announcements[0]
            file_path = scraper.download_report(first_report, stock_code)

            if file_path:
                return {
                    'source': self.name,
                    'file_path': file_path,
                    'data_type': 'pdf',
                    'metadata': first_report
                }

        except Exception as e:
            self.logger.error(f"巨潮资讯获取数据失败: {e}")

        return None


class AkshareDataSource(DataSource):
    """AkShare数据源（可选）"""

    def __init__(self):
        super().__init__(DataSourceType.AKSHARE, "AkShare")

    def _check_availability(self) -> bool:
        """检查AkShare是否已安装"""
        try:
            import akshare
            return True
        except ImportError:
            self.logger.info("AkShare未安装，如需使用请运行: pip install akshare")
            return False

    def fetch_financial_data(self, stock_code: str, **kwargs) -> Optional[Dict[str, Any]]:
        """通过AkShare获取财报数据"""
        try:
            import akshare as ak

            # 获取三大报表
            balance_df = ak.stock_financial_report_sina(stock=stock_code, symbol='资产负债表')
            income_df = ak.stock_financial_report_sina(stock=stock_code, symbol='利润表')
            cashflow_df = ak.stock_financial_report_sina(stock=stock_code, symbol='现金流量表')

            return {
                'source': self.name,
                'data_type': 'dataframe',
                'balance_sheet': balance_df,
                'income_statement': income_df,
                'cash_flow': cashflow_df
            }

        except Exception as e:
            self.logger.error(f"AkShare获取数据失败: {e}")
            return None


class TushareDataSource(DataSource):
    """Tushare数据源（可选）"""

    def __init__(self, token: Optional[str] = None):
        super().__init__(DataSourceType.TUSHARE, "Tushare Pro")
        self.token = token

    def _check_availability(self) -> bool:
        """检查Tushare是否已安装且已配置token"""
        try:
            import tushare
            if not self.token:
                self.logger.info("Tushare需要配置token，请在config.json中设置")
                return False
            return True
        except ImportError:
            self.logger.info("Tushare未安装，如需使用请运行: pip install tushare")
            return False

    def fetch_financial_data(self, stock_code: str, **kwargs) -> Optional[Dict[str, Any]]:
        """通过Tushare获取财报数据"""
        try:
            import tushare as ts

            ts.set_token(self.token)
            pro = ts.pro_api()

            # 转换股票代码格式（600519 -> 600519.SH）
            ts_code = self._convert_stock_code(stock_code)
            period = kwargs.get('period', '20231231')

            # 获取三大报表
            balance_df = pro.balancesheet(ts_code=ts_code, period=period)
            income_df = pro.income(ts_code=ts_code, period=period)
            cashflow_df = pro.cashflow(ts_code=ts_code, period=period)

            return {
                'source': self.name,
                'data_type': 'dataframe',
                'balance_sheet': balance_df,
                'income_statement': income_df,
                'cash_flow': cashflow_df
            }

        except Exception as e:
            self.logger.error(f"Tushare获取数据失败: {e}")
            return None

    def _convert_stock_code(self, code: str) -> str:
        """转换股票代码为Tushare格式"""
        if code.startswith('6'):
            return f"{code}.SH"
        elif code.startswith(('0', '3')):
            return f"{code}.SZ"
        elif len(code) == 5:
            return f"{code}.HK"
        else:
            return code


class DataSourceManager:
    """数据源管理器"""

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化数据源管理器

        Args:
            config: 配置字典，可包含：
                - preferred_source: 首选数据源
                - tushare_token: Tushare token
                - enable_akshare: 是否启用AkShare
                - enable_tushare: 是否启用Tushare
        """
        self.logger = get_logger()
        self.config = config or {}

        # 注册数据源
        self.sources: List[DataSource] = []
        self._register_sources()

        # 过滤出可用的数据源
        self.available_sources = [s for s in self.sources if s.is_available()]

        self.logger.info(f"可用数据源: {[s.name for s in self.available_sources]}")

    def _register_sources(self):
        """注册所有数据源（按优先级排序）"""
        preferred = self.config.get('preferred_source', 'cninfo')

        # 根据配置和首选项排序
        if preferred == 'akshare' and self.config.get('enable_akshare', False):
            self.sources.append(AkshareDataSource())
            self.sources.append(CninfoDataSource())
        elif preferred == 'tushare' and self.config.get('enable_tushare', False):
            token = self.config.get('tushare_token')
            self.sources.append(TushareDataSource(token=token))
            self.sources.append(CninfoDataSource())
        else:
            # 默认：优先使用巨潮资讯
            self.sources.append(CninfoDataSource())

            # 可选数据源
            if self.config.get('enable_akshare', False):
                self.sources.append(AkshareDataSource())

            if self.config.get('enable_tushare', False):
                token = self.config.get('tushare_token')
                self.sources.append(TushareDataSource(token=token))

    def fetch_data(self, stock_code: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        获取财报数据（自动切换数据源）

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数

        Returns:
            财报数据字典，失败返回None
        """
        if not self.available_sources:
            self.logger.error("没有可用的数据源！请检查配置或安装依赖。")
            return None

        # 依次尝试每个数据源
        for source in self.available_sources:
            self.logger.info(f"尝试使用数据源: {source.name}")

            try:
                data = source.fetch_financial_data(stock_code, **kwargs)
                if data:
                    self.logger.info(f"✓ 成功从 {source.name} 获取数据")
                    return data
                else:
                    self.logger.warning(f"✗ {source.name} 未返回数据")

            except Exception as e:
                self.logger.error(f"✗ {source.name} 出错: {e}")
                continue

        self.logger.error(f"所有数据源都失败了: {stock_code}")
        return None

    def add_custom_source(self, source: DataSource):
        """添加自定义数据源"""
        if source.is_available():
            self.available_sources.append(source)
            self.logger.info(f"添加自定义数据源: {source.name}")
        else:
            self.logger.warning(f"自定义数据源不可用: {source.name}")


# 便捷函数

def get_financial_data(stock_code: str, config: Optional[Dict] = None, **kwargs) -> Optional[Dict[str, Any]]:
    """
    获取财报数据（便捷函数）

    Args:
        stock_code: 股票代码
        config: 配置字典
        **kwargs: 其他参数

    Returns:
        财报数据
    """
    manager = DataSourceManager(config)
    return manager.fetch_data(stock_code, **kwargs)


if __name__ == '__main__':
    # 测试
    print("数据源管理器模块")
    print("\n测试可用数据源:")

    manager = DataSourceManager()
    print(f"\n可用数据源数量: {len(manager.available_sources)}")
    for source in manager.available_sources:
        print(f"  - {source.name} ({source.source_type.value})")
