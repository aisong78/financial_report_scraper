"""
市场数据采集演示

使用模拟数据源演示市场数据采集功能
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.services import MarketDataService
from src.data_sources import MockDataSource
from src.database import db
from src.database.models import Stock, FinancialReport, FinancialMetric
from datetime import datetime, date

console = Console()


def demo_data_source():
    """演示数据源功能"""
    console.print("\n[bold cyan]1. 数据源功能演示[/bold cyan]\n")

    # 创建模拟数据源
    source = MockDataSource()

    # 测试获取股票信息
    stock_code = "600519"
    console.print(f"[bold]获取股票信息: {stock_code}[/bold]")

    stock_info = source.get_stock_info(stock_code)
    if stock_info:
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("字段", style="cyan", width=20)
        table.add_column("值", style="green")

        for key, value in stock_info.items():
            table.add_row(key, str(value))

        console.print(table)

    # 测试获取市值历史
    console.print(f"\n[bold]获取市值历史: {stock_code}（5年）[/bold]")

    market_cap_data = source.get_market_cap_history(stock_code, years=5)
    if market_cap_data:
        table = Table(title="市值历史", box=box.ROUNDED)
        table.add_column("年份", justify="center", style="cyan")
        table.add_column("日期", justify="center")
        table.add_column("收盘价", justify="right", style="yellow")
        table.add_column("市值", justify="right", style="green")

        for data in market_cap_data:
            market_cap_billion = data['market_cap'] / 1e8
            table.add_row(
                str(data['year']),
                str(data['date']),
                f"{data['close']:.2f}元",
                f"{market_cap_billion:.0f}亿元"
            )

        console.print(table)

    # 测试获取分红数据
    console.print(f"\n[bold]获取分红数据: {stock_code}（5年）[/bold]")

    current_year = datetime.now().year
    dividend_data = source.get_dividend_data(
        stock_code,
        start_year=current_year - 5,
        end_year=current_year
    )

    if dividend_data:
        table = Table(title="分红历史", box=box.ROUNDED)
        table.add_column("年份", justify="center", style="cyan")
        table.add_column("每股分红", justify="right", style="green")
        table.add_column("分红率", justify="right", style="yellow")
        table.add_column("除权日", justify="center")

        for data in dividend_data:
            table.add_row(
                str(data['year']),
                f"{data['dividend_per_share']:.2f}元",
                f"{data['dividend_ratio'] * 100:.1f}%" if data['dividend_ratio'] else "N/A",
                str(data.get('ex_dividend_date', 'N/A'))
            )

        console.print(table)


def demo_database_enrichment():
    """演示数据库补充功能"""
    console.print("\n[bold cyan]2. 数据库补充功能演示[/bold cyan]\n")

    # 初始化数据库
    db.init_database()

    # 创建市场数据服务（使用模拟数据源）
    service = MarketDataService(data_source=MockDataSource())

    # 测试股票
    stock_code = "600519"

    # 确保数据库中有这只股票和财务数据
    with db.session_scope() as session:
        stock = session.query(Stock).filter_by(code=stock_code).first()

        if not stock:
            console.print(f"[yellow]创建股票记录: {stock_code}[/yellow]")
            stock_info = service.data_source.get_stock_info(stock_code)
            stock = Stock(
                code=stock_info['code'],
                name=stock_info['name'],
                market=stock_info['market'],
                exchange=stock_info['exchange'],
                industry=stock_info.get('industry', '')
            )
            session.add(stock)
            session.flush()

        # 创建财务报告和指标（如果不存在）
        current_year = datetime.now().year
        for i in range(5):
            year = current_year - i

            # 检查是否已有该年份的报告
            report = session.query(FinancialReport).filter_by(
                stock_id=stock.id,
                report_type='annual',
                fiscal_year=year
            ).first()

            if not report:
                # 创建报告
                report = FinancialReport(
                    stock_id=stock.id,
                    report_type='annual',
                    fiscal_year=year,
                    fiscal_period='FY',
                    report_date=date(year, 12, 31),
                    publish_date=date(year + 1, 4, 30),
                    file_url=f"https://example.com/report/{year}"
                )
                session.add(report)
                session.flush()

                # 创建指标
                metric = FinancialMetric(
                    stock_id=stock.id,
                    report_id=report.id,
                    report_date=date(year, 12, 31),
                    # 模拟一些基础数据
                    revenue=50000000000 + i * 5000000000,  # 500亿 + 增长
                    net_profit=20000000000 + i * 2000000000,  # 200亿 + 增长
                    roe=0.28,
                    gross_margin=0.91,
                )
                session.add(metric)

        console.print(f"✓ 确保数据库中有股票和财务数据: {stock.name}")

    # 补充市场数据
    console.print(f"\n[bold]补充市场数据: {stock_code}[/bold]")

    success = service.enrich_financial_metrics(stock_code, years=5)

    if success:
        console.print("[bold green]✓ 市场数据补充成功！[/bold green]")

        # 显示补充后的数据
        console.print(f"\n[bold]查看补充后的数据[/bold]")

        with db.session_scope() as session:
            stock = session.query(Stock).filter_by(code=stock_code).first()

            metrics = (
                session.query(FinancialMetric)
                .join(FinancialReport)
                .filter(
                    FinancialMetric.stock_id == stock.id,
                    FinancialReport.report_type == 'annual'
                )
                .order_by(FinancialReport.fiscal_year.desc())
                .limit(5)
                .all()
            )

            table = Table(title=f"{stock.name} 财务数据（含市场数据）", box=box.ROUNDED)
            table.add_column("年份", justify="center", style="cyan")
            table.add_column("营收", justify="right", style="yellow")
            table.add_column("净利润", justify="right", style="yellow")
            table.add_column("市值", justify="right", style="green")
            table.add_column("PE", justify="right", style="magenta")

            for metric in metrics:
                if metric.report:
                    year = metric.report.fiscal_year
                    revenue = f"{float(metric.revenue) / 1e8:.0f}亿" if metric.revenue else "N/A"
                    profit = f"{float(metric.net_profit) / 1e8:.0f}亿" if metric.net_profit else "N/A"

                    # 从 extra_metrics 获取市值
                    market_cap = "N/A"
                    pe = "N/A"
                    if metric.extra_metrics:
                        if 'market_cap' in metric.extra_metrics:
                            market_cap = f"{metric.extra_metrics['market_cap'] / 1e8:.0f}亿"
                        if 'pe_ratio_calculated' in metric.extra_metrics:
                            pe = f"{metric.extra_metrics['pe_ratio_calculated']:.1f}"

                    table.add_row(str(year), revenue, profit, market_cap, pe)

            console.print(table)

    else:
        console.print("[yellow]⚠ 数据库补充部分失败[/yellow]")


def main():
    """主函数"""
    console.print("""
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          市场数据采集演示                                 ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]

本演示将展示：
1. 数据源功能（使用模拟数据）
   - 获取股票基本信息
   - 获取历史市值
   - 获取分红数据

2. 数据库补充功能
   - 将市场数据保存到数据库
   - 计算PE等估值指标
   - 查看补充后的完整数据
    """)

    try:
        # 演示1：数据源功能
        demo_data_source()

        # 演示2：数据库补充
        demo_database_enrichment()

        console.print("\n[bold green]✓ 演示完成！[/bold green]\n")
        console.print("说明：")
        console.print("  • 本演示使用模拟数据源（MockDataSource）")
        console.print("  • 实际使用时可以替换为 AkShareSource 获取真实数据")
        console.print("  • 市场数据被保存在 FinancialMetric.extra_metrics 字段中")
        console.print("  • 支持计算PE、PB等估值指标\n")

    except Exception as e:
        console.print(f"\n[bold red]错误: {e}[/bold red]\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]用户中断演示[/yellow]")
