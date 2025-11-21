"""
中国市场爬虫（A股 + 港股）

从巨潮资讯网获取财报
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os

import requests

from .base_scraper import BaseScraper


class ChinaStockScraper(BaseScraper):
    """中国股票爬虫（A股 + 港股）"""

    def __init__(self, market: str = "A"):
        """
        初始化

        Args:
            market: A（A股）或 HK（港股）
        """
        super().__init__(market)

        self.base_url = "http://www.cninfo.com.cn"
        self.query_url = f"{self.base_url}/new/hisAnnouncement/query"
        self.search_url = f"{self.base_url}/new/information/topSearch/query"

        # 请求头（模拟真实浏览器）
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/new/disclosure/index",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }

    def _get_org_id(self, stock_code: str) -> Optional[str]:
        """
        获取股票的 orgId

        Args:
            stock_code: 股票代码

        Returns:
            orgId，失败返回 None
        """
        try:
            data = {"keyWord": stock_code}
            response = self.session.post(
                self.search_url,
                data=data,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            results = response.json()
            if results and isinstance(results, list):
                for item in results:
                    if item.get('code') == stock_code:
                        org_id = item.get('orgId')
                        self.logger.info(f"获取 orgId 成功: {stock_code} -> {org_id}")
                        return org_id

            self.logger.warning(f"未找到 orgId: {stock_code}")
            return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取 orgId 失败: {stock_code}, 错误: {e}")
            return None
        except Exception as e:
            self.logger.exception(f"获取 orgId 出现未知错误: {stock_code}")
            return None

    def scrape(
        self,
        stock_code: str,
        lookback_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        爬取财报列表

        Args:
            stock_code: 股票代码
            lookback_days: 回溯天数

        Returns:
            财报信息列表
        """
        if lookback_days is None:
            lookback_days = self.config.lookback_days

        self.logger.info(f"开始爬取 {self.market} 股票: {stock_code}, 回溯 {lookback_days} 天")

        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # 构造请求数据
        data = {
            "pageNum": 1,
            "pageSize": 30,
            "tabName": "fulltext",
            "plate": "",
            "stock": stock_code,
            "searchkey": "",
            "secid": "",
            "category": "",
            "trade": "",
            "seDate": f"{start_date.strftime('%Y-%m-%d')}~{end_date.strftime('%Y-%m-%d')}",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true"
        }

        # A股特殊处理
        if self.market == 'A':
            if stock_code.startswith('6'):
                data['column'] = 'sse'  # 上交所
            else:
                data['column'] = 'szse'  # 深交所

            # 只要财报相关公告
            data['category'] = "category_ndbg_szsh;category_bndbg_szsh;category_yjdbg_szsh;category_sjdbg_szsh"

        # 港股特殊处理
        elif self.market == 'HK':
            data['column'] = 'hke'

        # 尝试获取 orgId
        org_id = self._get_org_id(stock_code)
        if org_id:
            data['stock'] = f"{stock_code},{org_id}"

        # 发送请求
        try:
            response = self.session.post(
                self.query_url,
                data=data,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            announcements = result.get('announcements', [])

            self.logger.info(f"找到 {len(announcements)} 条公告")
            return announcements

        except requests.exceptions.Timeout:
            self.logger.error(f"请求超时: {stock_code}")
            return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {stock_code}, 错误: {e}")
            return []
        except Exception as e:
            self.logger.exception(f"爬取出现未知错误: {stock_code}")
            return []

    def download_report(
        self,
        report_info: Dict[str, Any],
        stock_code: str
    ) -> Optional[str]:
        """
        下载财报

        Args:
            report_info: 财报信息（来自 scrape 的结果）
            stock_code: 股票代码

        Returns:
            文件路径，失败返回 None
        """
        # 提取信息
        title = report_info.get('announcementTitle', '未知标题')
        title = title.replace('<em>', '').replace('</em>', '')  # 清理 HTML 标签

        adjunct_url = report_info.get('adjunctUrl', '')
        if not adjunct_url:
            self.logger.warning(f"无下载链接: {title}")
            return None

        # 构造下载 URL
        download_url = f"http://static.cninfo.com.cn/{adjunct_url}"

        # 构造文件名
        file_name = f"{stock_code}_{title}.pdf"
        file_name = self.sanitize_filename(file_name)

        # 保存路径
        save_path = self.save_dir / file_name

        # 下载
        success = self.download_file(download_url, str(save_path))

        if success:
            return str(save_path)
        else:
            return None

    def scrape_and_download(
        self,
        stock_code: str,
        keywords: Optional[List[str]] = None,
        lookback_days: Optional[int] = None
    ) -> List[str]:
        """
        爬取并下载财报（一站式）

        Args:
            stock_code: 股票代码
            keywords: 关键词列表（只下载包含这些关键词的公告）
            lookback_days: 回溯天数

        Returns:
            下载的文件路径列表
        """
        if keywords is None:
            keywords = self.config.keywords

        # 爬取公告列表
        announcements = self.scrape(stock_code, lookback_days)

        if not announcements:
            self.logger.warning(f"未找到任何公告: {stock_code}")
            return []

        # 过滤并下载
        downloaded_files = []

        for ann in announcements:
            title = ann.get('announcementTitle', '')
            title = title.replace('<em>', '').replace('</em>', '')

            # 检查关键词
            if any(kw in title for kw in keywords):
                self.logger.info(f"发现目标公告: {title}")

                # 下载
                file_path = self.download_report(ann, stock_code)

                if file_path:
                    downloaded_files.append(file_path)

                # 速率限制
                self.rate_limit(1.0)

        self.logger.info(f"下载完成: {stock_code}, 共 {len(downloaded_files)} 份财报")
        return downloaded_files


# 便捷函数

def scrape_a_stock(stock_code: str, **kwargs) -> List[str]:
    """爬取 A 股财报"""
    scraper = ChinaStockScraper(market="A")
    return scraper.scrape_and_download(stock_code, **kwargs)


def scrape_hk_stock(stock_code: str, **kwargs) -> List[str]:
    """爬取港股财报"""
    scraper = ChinaStockScraper(market="HK")
    return scraper.scrape_and_download(stock_code, **kwargs)


if __name__ == "__main__":
    # 测试 A 股
    print("测试 A 股爬虫...")
    files = scrape_a_stock("600519", lookback_days=90)
    print(f"下载了 {len(files)} 个文件")

    # 测试港股
    print("\n测试港股爬虫...")
    files = scrape_hk_stock("00700", lookback_days=90)
    print(f"下载了 {len(files)} 个文件")
