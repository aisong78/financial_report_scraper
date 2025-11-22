#!/usr/bin/env python3
"""
查看采集的财务数据

用法:
    python 查看采集数据.py                 # 查看所有数据摘要
    python 查看采集数据.py 600519          # 查看指定股票的详细数据
    python 查看采集数据.py 600519 000858   # 对比多只股票
"""

import sys
from sqlalchemy import create_engine, text
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
DB_PATH = "data/database.db"

def view_summary():
    """查看数据摘要"""
    engine = create_engine(f"sqlite:///{DB_PATH}")

    console.print("\n[bold cyan]📊 数据库数据摘要[/bold cyan]\n")

    with engine.connect() as conn:
        # 1. 股票列表
        result = conn.execute(text("""
            SELECT s.code, s.name, s.market, COUNT(fr.id) as report_count
            FROM stocks s
            LEFT JOIN financial_reports fr ON s.id = fr.stock_id
            GROUP BY s.id, s.code, s.name, s.market
            ORDER BY s.code
        """))
        stocks = result.fetchall()

        if not stocks:
            console.print("[yellow]数据库中暂无数据[/yellow]")
            return

        table = Table(title="股票列表")
        table.add_column("股票代码", style="cyan")
        table.add_column("股票名称", style="green")
        table.add_column("市场", justify="center", style="yellow")
        table.add_column("财报数", justify="right", style="magenta")

        for stock in stocks:
            table.add_row(
                str(stock[0]),
                str(stock[1] or ""),
                str(stock[2]),
                str(stock[3])
            )

        console.print(table)
        console.print(f"\n总计: {len(stocks)} 只股票\n")

        # 2. 财报统计
        result = conn.execute(text("""
            SELECT report_type, COUNT(*) as count
            FROM financial_reports
            GROUP BY report_type
        """))
        report_stats = result.fetchall()

        if report_stats:
            console.print("[bold]财报类型统计:[/bold]")
            for stat in report_stats:
                console.print(f"  • {stat[0]}: {stat[1]} 份")

        result = conn.execute(text("SELECT COUNT(*) FROM financial_reports"))
        total_reports = result.scalar()
        console.print(f"\n总计: {total_reports} 份财报")

        result = conn.execute(text("SELECT COUNT(*) FROM financial_metrics"))
        total_metrics = result.scalar()
        console.print(f"财务指标记录: {total_metrics} 条\n")


def view_stock_detail(stock_code):
    """查看指定股票的详细数据"""
    engine = create_engine(f"sqlite:///{DB_PATH}")

    console.print(f"\n[bold cyan]📈 股票详情: {stock_code}[/bold cyan]\n")

    with engine.connect() as conn:
        # 1. 股票基本信息
        result = conn.execute(text("""
            SELECT code, name, market, industry, listing_date
            FROM stocks
            WHERE code = :code
        """), {"code": stock_code})
        stock = result.fetchone()

        if not stock:
            console.print(f"[red]未找到股票 {stock_code}[/red]")
            return

        console.print(Panel(
            f"[bold]代码:[/bold] {stock[0]}\n"
            f"[bold]名称:[/bold] {stock[1] or 'N/A'}\n"
            f"[bold]市场:[/bold] {stock[2]}\n"
            f"[bold]行业:[/bold] {stock[3] or 'N/A'}\n"
            f"[bold]上市日期:[/bold] {stock[4] or 'N/A'}",
            title="基本信息",
            border_style="cyan"
        ))

        # 2. 财报列表
        result = conn.execute(text("""
            SELECT
                fr.fiscal_year,
                fr.fiscal_period,
                fr.report_type,
                fr.report_date,
                fr.file_format,
                fr.is_parsed
            FROM financial_reports fr
            JOIN stocks s ON fr.stock_id = s.id
            WHERE s.code = :code
            ORDER BY fr.fiscal_year DESC, fr.report_type
        """), {"code": stock_code})
        reports = result.fetchall()

        if reports:
            table = Table(title="财报列表")
            table.add_column("年份", justify="center")
            table.add_column("期间", justify="center")
            table.add_column("类型", justify="center")
            table.add_column("报告日期", justify="center")
            table.add_column("格式")
            table.add_column("已解析", justify="center")

            for report in reports:
                table.add_row(
                    str(report[0]),
                    str(report[1] or ""),
                    str(report[2]),
                    str(report[3] or "")[:10],
                    str(report[4] or ""),
                    "✅" if report[5] else "❌"
                )

            console.print(table)
            console.print(f"\n共 {len(reports)} 份财报\n")
        else:
            console.print("[yellow]暂无财报数据[/yellow]\n")

        # 3. 最新财务指标
        result = conn.execute(text("""
            SELECT
                fm.report_date,
                fm.revenue,
                fm.net_profit,
                fm.total_assets,
                fm.total_liabilities,
                fm.roe,
                fm.net_margin,
                fm.asset_liability_ratio,
                fm.revenue_yoy,
                fm.net_profit_yoy,
                fr.report_type
            FROM financial_metrics fm
            JOIN financial_reports fr ON fm.report_id = fr.id
            JOIN stocks s ON fr.stock_id = s.id
            WHERE s.code = :code
            ORDER BY fm.report_date DESC
            LIMIT 1
        """), {"code": stock_code})
        metrics = result.fetchone()

        if metrics:
            console.print("[bold]最新财务指标:[/bold]")

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("指标", style="yellow", width=20)
            table.add_column("数值", style="green", justify="right")

            table.add_row("报告日期", str(metrics[0])[:10] if metrics[0] else "N/A")
            table.add_row("报告类型", str(metrics[10]))

            if metrics[1]:
                table.add_row("营业收入", f"{metrics[1]/10000:.2f} 亿元")
            if metrics[2]:
                table.add_row("净利润", f"{metrics[2]/10000:.2f} 亿元")
            if metrics[3]:
                table.add_row("总资产", f"{metrics[3]/10000:.2f} 亿元")
            if metrics[4]:
                table.add_row("总负债", f"{metrics[4]/10000:.2f} 亿元")
            if metrics[5]:
                table.add_row("ROE", f"{metrics[5]*100:.2f}%")
            if metrics[6]:
                table.add_row("净利率", f"{metrics[6]*100:.2f}%")
            if metrics[7]:
                table.add_row("资产负债率", f"{metrics[7]*100:.2f}%")
            if metrics[8]:
                table.add_row("营收同比增长", f"{metrics[8]*100:.2f}%")
            if metrics[9]:
                table.add_row("利润同比增长", f"{metrics[9]*100:.2f}%")

            console.print(table)
        else:
            console.print("[yellow]暂无财务指标数据[/yellow]")


def compare_stocks(stock_codes):
    """对比多只股票"""
    engine = create_engine(f"sqlite:///{DB_PATH}")

    console.print(f"\n[bold cyan]📊 股票对比[/bold cyan]\n")

    with engine.connect() as conn:
        table = Table(title="最新年报数据对比")
        table.add_column("股票", style="cyan", width=15)
        table.add_column("年份", justify="center", width=8)
        table.add_column("营收(亿)", justify="right", style="green")
        table.add_column("净利润(亿)", justify="right", style="green")
        table.add_column("ROE", justify="right", style="yellow")
        table.add_column("净利率", justify="right", style="yellow")
        table.add_column("资产负债率", justify="right", style="magenta")

        for code in stock_codes:
            result = conn.execute(text("""
                SELECT
                    s.code,
                    s.name,
                    fr.fiscal_year,
                    fm.revenue,
                    fm.net_profit,
                    fm.roe,
                    fm.net_margin,
                    fm.asset_liability_ratio
                FROM financial_metrics fm
                JOIN financial_reports fr ON fm.report_id = fr.id
                JOIN stocks s ON fr.stock_id = s.id
                WHERE s.code = :code AND fr.report_type = 'annual'
                ORDER BY fr.fiscal_year DESC
                LIMIT 1
            """), {"code": code})
            data = result.fetchone()

            if data:
                table.add_row(
                    f"{data[0]} {data[1] or ''}",
                    str(data[2]),
                    f"{data[3]/10000:.2f}" if data[3] else "N/A",
                    f"{data[4]/10000:.2f}" if data[4] else "N/A",
                    f"{data[5]*100:.2f}%" if data[5] else "N/A",
                    f"{data[6]*100:.2f}%" if data[6] else "N/A",
                    f"{data[7]*100:.2f}%" if data[7] else "N/A"
                )
            else:
                table.add_row(f"{code}", "无数据", "-", "-", "-", "-", "-")

        console.print(table)


def main():
    args = sys.argv[1:]

    if not args:
        # 显示摘要
        view_summary()
    elif len(args) == 1:
        # 显示单只股票详情
        view_stock_detail(args[0])
    else:
        # 对比多只股票
        compare_stocks(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        import traceback
        traceback.print_exc()
