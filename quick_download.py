#!/usr/bin/env python3
"""
快速财报下载工具

使用示例:
    # 下载美股财报
    python quick_download.py --us AAPL
    python quick_download.py --us MSFT GOOGL TSLA

    # 下载A股财报
    python quick_download.py --cn 600519
    python quick_download.py --cn 000001 600036

    # 指定保存目录
    python quick_download.py --us AAPL --output test_data
"""

import sys
import argparse
from pathlib import Path


def download_us_report(ticker: str, output_dir: str = 'reports/US_Stocks'):
    """
    从SEC EDGAR下载美股财报

    Args:
        ticker: 股票代码（如 AAPL）
        output_dir: 保存目录
    """
    print(f"\n{'='*60}")
    print(f"下载美股财报: {ticker}")
    print(f"{'='*60}\n")

    try:
        from src.scrapers import USReportScraper

        scraper = USReportScraper()
        reports = scraper.download_report(
            ticker=ticker,
            report_type='10-K',
            save_dir=output_dir
        )

        if reports:
            print(f"✓ 成功下载 {len(reports)} 份财报")
            for report in reports:
                print(f"  - {report}")
        else:
            print("⚠ 未找到财报或下载失败")
            print(f"\n提示：你也可以手动从SEC EDGAR下载:")
            print(f"  https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker={ticker}")

    except Exception as e:
        print(f"✗ 下载失败: {e}")
        print(f"\n手动下载方法:")
        print(f"  1. 访问: https://www.sec.gov/edgar/searchedgar/companysearch.html")
        print(f"  2. 搜索: {ticker}")
        print(f"  3. 找到最新的 10-K 文件")
        print(f"  4. 点击 'Documents' 下载HTML格式")


def download_cn_report(stock_code: str, output_dir: str = 'reports/CN_Stocks'):
    """
    从巨潮资讯下载A股财报

    Args:
        stock_code: 股票代码（如 600519）
        output_dir: 保存目录
    """
    print(f"\n{'='*60}")
    print(f"下载A股财报: {stock_code}")
    print(f"{'='*60}\n")

    try:
        from src.scrapers import CNReportScraper

        scraper = CNReportScraper()
        reports = scraper.download_report(
            stock_code=stock_code,
            report_types=['年报'],
            save_dir=output_dir
        )

        if reports:
            print(f"✓ 成功下载 {len(reports)} 份财报")
            for report in reports:
                print(f"  - {report}")
        else:
            print("⚠ 未找到财报或下载失败（可能是网络限制）")
            print(f"\n提示：你也可以手动从巨潮资讯下载:")
            print(f"  http://www.cninfo.com.cn/new/disclosure/stock?stockCode={stock_code}")

    except Exception as e:
        print(f"✗ 下载失败: {e}")
        print(f"\n手动下载方法:")
        print(f"  1. 访问: http://www.cninfo.com.cn/new/disclosure")
        print(f"  2. 搜索股票代码: {stock_code}")
        print(f"  3. 找到最新年报并下载PDF")


def show_examples():
    """显示使用示例"""
    print("""
╔══════════════════════════════════════════════════════════╗
║           财报下载工具 - 使用指南                        ║
╚══════════════════════════════════════════════════════════╝

🇺🇸 美股财报（免费公开）:

  方法1: 使用本脚本自动下载
    python quick_download.py --us AAPL

  方法2: 手动从SEC EDGAR下载
    网址: https://www.sec.gov/edgar/searchedgar/companysearch.html
    步骤:
      1. 搜索公司（如 "AAPL"）
      2. 点击公司名
      3. 找到最新的 "10-K" 或 "10-Q"
      4. 点击 "Documents" 按钮
      5. 下载 HTML 格式文件

  热门公司代码:
    AAPL   - Apple
    MSFT   - Microsoft
    GOOGL  - Google
    TSLA   - Tesla
    NVDA   - Nvidia
    META   - Meta (Facebook)
    AMZN   - Amazon

🇨🇳 A股财报（免费公开）:

  方法1: 使用本脚本自动下载
    python quick_download.py --cn 600519

  方法2: 手动从巨潮资讯下载
    网址: http://www.cninfo.com.cn/new/disclosure
    步骤:
      1. 输入股票代码（如 "600519"）
      2. 在公告列表找到年报
      3. 下载PDF文件

  热门公司代码:
    600519 - 贵州茅台
    000001 - 平安银行
    600036 - 招商银行
    000858 - 五粮液

📝 示例命令:

  # 下载单个公司
  python quick_download.py --us AAPL

  # 下载多个公司
  python quick_download.py --us AAPL MSFT GOOGL

  # 指定输出目录
  python quick_download.py --us AAPL --output test_data

  # 下载A股
  python quick_download.py --cn 600519

💡 提示:

  - 所有财报都是公开免费的
  - SEC EDGAR最稳定（美国政府网站）
  - 如果自动下载失败，可以手动下载后放到指定目录
  - 支持的格式：HTML, PDF, XBRL
""")


def main():
    parser = argparse.ArgumentParser(
        description='快速下载财报工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--us', nargs='+', metavar='TICKER',
                       help='美股代码（如 AAPL MSFT）')
    parser.add_argument('--cn', nargs='+', metavar='CODE',
                       help='A股代码（如 600519 000001）')
    parser.add_argument('--output', '-o', default=None,
                       help='输出目录（默认: reports/）')
    parser.add_argument('--examples', action='store_true',
                       help='显示使用示例和下载指南')

    args = parser.parse_args()

    # 显示示例
    if args.examples:
        show_examples()
        return

    # 检查是否提供了参数
    if not args.us and not args.cn:
        print("请指定要下载的股票代码！\n")
        print("使用方法:")
        print("  python quick_download.py --us AAPL          # 下载美股")
        print("  python quick_download.py --cn 600519        # 下载A股")
        print("  python quick_download.py --examples         # 查看详细指南")
        return

    # 下载美股
    if args.us:
        output_dir = args.output or 'reports/US_Stocks'
        for ticker in args.us:
            download_us_report(ticker.upper(), output_dir)

    # 下载A股
    if args.cn:
        output_dir = args.output or 'reports/CN_Stocks'
        for code in args.cn:
            download_cn_report(code, output_dir)

    print(f"\n{'='*60}")
    print("下载完成！")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
