"""
美股爬虫

从 SEC EDGAR 获取财报
"""

import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from sec_edgar_downloader import Downloader

from .base_scraper import BaseScraper


class USStockScraper(BaseScraper):
    """美股爬虫"""

    def __init__(self):
        """初始化"""
        super().__init__(market="US")

        # 检查邮箱配置
        self.user_email = self.config.user_email
        if "example.com" in self.user_email:
            self.logger.warning("请配置有效的 user_email 以使用 SEC 下载功能")
            self.downloader = None
        else:
            # 创建下载器
            self.downloader = Downloader(
                company_name="FinancialAnalyzer",
                email_address=self.user_email,
                download_folder=str(self.save_dir)
            )

    def scrape(
        self,
        stock_code: str,
        lookback_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        爬取财报列表

        注意：SEC EDGAR API 不支持列表查询，
        这个方法主要是为了统一接口

        Args:
            stock_code: 股票代码
            lookback_days: 回溯天数

        Returns:
            空列表（实际下载在 download_reports 中完成）
        """
        self.logger.info(f"美股爬虫不支持单独的列表查询，请使用 download_reports")
        return []

    def download_report(
        self,
        report_info: Dict[str, Any]
    ) -> Optional[str]:
        """
        下载单个财报

        注意：美股爬虫使用 batch 下载，不支持单个下载

        Args:
            report_info: 财报信息

        Returns:
            None
        """
        self.logger.warning("美股爬虫使用批量下载，请使用 download_reports")
        return None

    def download_reports(
        self,
        ticker: str,
        lookback_days: Optional[int] = None,
        forms: Optional[List[str]] = None
    ) -> List[str]:
        """
        下载美股财报

        Args:
            ticker: 股票代码（如 AAPL, TSLA）
            lookback_days: 回溯天数
            forms: 财报类型列表，默认 ["10-K", "10-Q"]

        Returns:
            下载的文件路径列表
        """
        if self.downloader is None:
            self.logger.error("下载器未初始化，请检查 user_email 配置")
            return []

        if lookback_days is None:
            lookback_days = self.config.lookback_days

        if forms is None:
            forms = ["10-K", "10-Q"]  # 10-K: 年报, 10-Q: 季报

        self.logger.info(f"开始下载美股财报: {ticker}, 回溯 {lookback_days} 天")

        # 计算起始日期
        after_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

        downloaded_files = []

        try:
            for form in forms:
                self.logger.info(f"正在下载 {form}...")

                # 下载
                num_downloaded = self.downloader.get(
                    filing_type=form,
                    ticker_or_cik=ticker,
                    after_date=after_date,
                    download_details=True
                )

                self.logger.info(f"下载了 {num_downloaded} 份 {form}")

            # 提取和整理文件
            extracted = self._extract_primary_documents(ticker)
            downloaded_files.extend(extracted)

            self.logger.info(f"下载完成: {ticker}, 共 {len(downloaded_files)} 份财报")

        except Exception as e:
            self.logger.exception(f"下载美股财报失败: {ticker}")

        return downloaded_files

    def _extract_primary_documents(self, ticker: str) -> List[str]:
        """
        提取主要文档并重命名

        SEC 下载的文件结构很复杂，这个方法提取主要的 HTML 文件
        并重命名为更易读的格式

        Args:
            ticker: 股票代码

        Returns:
            提取的文件路径列表
        """
        extracted_files = []

        # SEC 文件存储路径
        sec_root = self.save_dir / "sec-edgar-filings" / ticker

        if not sec_root.exists():
            self.logger.warning(f"未找到 SEC 文件目录: {sec_root}")
            return []

        # 遍历所有下载的文件
        for form_dir in sec_root.iterdir():
            if not form_dir.is_dir():
                continue

            form_type = form_dir.name  # 如 10-K, 10-Q

            for accession_dir in form_dir.iterdir():
                if not accession_dir.is_dir():
                    continue

                accession = accession_dir.name

                # 查找 primary-document.html
                primary_doc = accession_dir / "primary-document.html"

                if primary_doc.exists():
                    # 构造新文件名: Ticker_Form_Accession.html
                    new_name = f"{ticker}_{form_type}_{accession}.html"
                    target_path = self.save_dir / new_name

                    # 复制文件
                    if not target_path.exists():
                        try:
                            shutil.copy(primary_doc, target_path)
                            self.logger.info(f"提取财报: {new_name}")
                            extracted_files.append(str(target_path))
                        except Exception as e:
                            self.logger.error(f"提取文件失败: {primary_doc}, 错误: {e}")

        return extracted_files


# 便捷函数

def scrape_us_stock(ticker: str, **kwargs) -> List[str]:
    """爬取美股财报"""
    scraper = USStockScraper()
    return scraper.download_reports(ticker, **kwargs)


if __name__ == "__main__":
    # 测试
    print("测试美股爬虫...")
    files = scrape_us_stock("AAPL", lookback_days=365)
    print(f"下载了 {len(files)} 个文件")
