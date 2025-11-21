"""
爬虫模块

提供 A股、港股、美股的财报下载功能
"""

from .base_scraper import BaseScraper
from .cn_scraper import ChinaStockScraper, scrape_a_stock, scrape_hk_stock
from .us_scraper import USStockScraper, scrape_us_stock


def identify_market(code: str) -> str:
    """
    识别股票市场

    Args:
        code: 股票代码

    Returns:
        市场类型：A, HK, US, UNKNOWN
    """
    code = code.strip()

    if code.isdigit():
        if len(code) == 6:
            return 'A'  # A股
        elif len(code) == 5:
            return 'HK'  # 港股
    elif code.isalpha():
        return 'US'  # 美股

    return 'UNKNOWN'


def scrape_stock(code: str, **kwargs) -> list:
    """
    智能爬取股票财报（自动识别市场）

    Args:
        code: 股票代码
        **kwargs: 其他参数

    Returns:
        下载的文件路径列表

    Examples:
        >>> scrape_stock("600519")  # A股
        >>> scrape_stock("00700")   # 港股
        >>> scrape_stock("AAPL")    # 美股
    """
    market = identify_market(code)

    if market == 'A':
        return scrape_a_stock(code, **kwargs)
    elif market == 'HK':
        return scrape_hk_stock(code, **kwargs)
    elif market == 'US':
        return scrape_us_stock(code, **kwargs)
    else:
        raise ValueError(f"无法识别股票代码: {code}")


__all__ = [
    'BaseScraper',
    'ChinaStockScraper',
    'USStockScraper',
    'scrape_a_stock',
    'scrape_hk_stock',
    'scrape_us_stock',
    'scrape_stock',
    'identify_market',
]
