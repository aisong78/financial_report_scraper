#!/usr/bin/env python3
"""
数据查看工具 - 查看数据库中采集的财务数据

用法:
    python view_data.py                    # 查看所有股票数据摘要
    python view_data.py 600519             # 查看指定股票的详细数据
    python view_data.py 600519 --year 2023 # 查看指定股票指定年份的数据
"""

import sys
from pathlib import Path
from datetime import datetime
import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.database.models import FinancialData, session_scope
from sqlalchemy import func, desc

console = Console()


def show_all_stocks():
    """显示所有股票的数据摘要"""
    with session_scope() as session:
        # 查询所有股票及其记录数
        stocks = session.query(
            FinancialData.stock_code,
            func.count(FinancialData.id).label('count'),
            func.min(FinancialData.report_year).label('min_year'),
            func.max(FinancialData.report_year).label('max_year')
        ).group_by(FinancialData.stock_code).all()

        if not stocks:
            console.print("[yellow]数据库中暂无数据[/yellow]")
            return

        table = Table(title="📊 数据库中的股票数据")
        table.add_column("股票代码", style="cyan")
        table.add_column("记录数", justify="right", style="green")
        table.add_column("年份范围", style="yellow")

        for stock in stocks:
            table.add_row(
                stock.stock_code,
                str(stock.count),
                f"{stock.min_year} - {stock.max_year}"
            )

        console.print(table)
        console.print(f"\n总计: [bold]{len(stocks)}[/bold] 只股票")


def show_stock_detail(stock_code, year=None):
    """显示指定股票的详细数据"""
    with session_scope() as session:
        # 构建查询
        query = session.query(FinancialData).filter(
            FinancialData.stock_code == stock_code
        )

        if year:
            query = query.filter(FinancialData.report_year == year)

        records = query.order_by(
            desc(FinancialData.report_year),
            FinancialData.report_type
        ).all()

        if not records:
            console.print(f"[yellow]未找到股票 {stock_code} 的数据[/yellow]")
            return

        # 显示基本信息
        console.print(f"\n[bold cyan]股票: {stock_code}[/bold cyan]")
        console.print(f"记录数: {len(records)}\n")

        # 显示每条记录的摘要
        for i, record in enumerate(records, 1):
            console.print(f"[bold]记录 {i}:[/bold]")
            console.print(f"  年份: {record.report_year}")
            console.print(f"  报告类型: {record.report_type}")
            console.print(f"  采集时间: {record.created_at}")

            # 显示关键财务数据
            console.print("\n  [cyan]关键财务指标:[/cyan]")

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("指标", style="yellow")
            table.add_column("数值", style="green")

            if record.revenue:
                table.add_row("营业收入", f"{record.revenue:,.2f} 万元")
            if record.net_profit:
                table.add_row("净利润", f"{record.net_profit:,.2f} 万元")
            if record.total_assets:
                table.add_row("总资产", f"{record.total_assets:,.2f} 万元")
            if record.roe:
                table.add_row("ROE", f"{record.roe:.2%}")
            if record.debt_to_asset_ratio:
                table.add_row("资产负债率", f"{record.debt_to_asset_ratio:.2%}")
            if record.revenue_growth_rate:
                table.add_row("营收增长率", f"{record.revenue_growth_rate:.2%}")
            if record.net_profit_growth_rate:
                table.add_row("利润增长率", f"{record.net_profit_growth_rate:.2%}")

            console.print(table)
            console.print("")


def show_stock_comparison(stock_codes):
    """对比多只股票的最新数据"""
    with session_scope() as session:
        table = Table(title="📊 股票对比（最新年报）")
        table.add_column("股票代码", style="cyan")
        table.add_column("年份", justify="center")
        table.add_column("营收(亿)", justify="right", style="green")
        table.add_column("净利润(亿)", justify="right", style="green")
        table.add_column("ROE", justify="right", style="yellow")
        table.add_column("资产负债率", justify="right", style="magenta")

        for code in stock_codes:
            # 查询该股票最新的年报数据
            record = session.query(FinancialData).filter(
                FinancialData.stock_code == code,
                FinancialData.report_type == 'annual'
            ).order_by(desc(FinancialData.report_year)).first()

            if record:
                table.add_row(
                    code,
                    str(record.report_year),
                    f"{record.revenue/10000:.2f}" if record.revenue else "N/A",
                    f"{record.net_profit/10000:.2f}" if record.net_profit else "N/A",
                    f"{record.roe:.2%}" if record.roe else "N/A",
                    f"{record.debt_to_asset_ratio:.2%}" if record.debt_to_asset_ratio else "N/A"
                )
            else:
                table.add_row(code, "无数据", "-", "-", "-", "-")

        console.print(table)


@click.command()
@click.argument('stock_codes', nargs=-1)
@click.option('--year', type=int, help='指定年份')
@click.option('--compare', is_flag=True, help='对比多只股票')
def main(stock_codes, year, compare):
    """
    数据查看工具

    示例:
        python view_data.py                    # 查看所有股票
        python view_data.py 600519             # 查看指定股票
        python view_data.py 600519 --year 2023 # 查看指定年份
        python view_data.py 600519 000858 --compare  # 对比多只股票
    """
    console.print("\n[bold cyan]🔍 财务数据查看工具[/bold cyan]\n")

    if not stock_codes:
        # 显示所有股票
        show_all_stocks()
    elif compare and len(stock_codes) > 1:
        # 对比多只股票
        show_stock_comparison(stock_codes)
    elif len(stock_codes) == 1:
        # 显示单只股票详情
        show_stock_detail(stock_codes[0], year)
    else:
        console.print("[yellow]请使用 --compare 参数来对比多只股票[/yellow]")


if __name__ == '__main__':
    main()
