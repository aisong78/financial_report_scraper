#!/usr/bin/env python3
"""简单的数据查看脚本"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from rich.console import Console
from rich.table import Table

console = Console()

# 数据库路径
DB_PATH = "data/database.db"

def main():
    """查看数据库中的数据"""
    engine = create_engine(f"sqlite:///{DB_PATH}")

    console.print("\n[bold cyan]📊 数据库数据查看[/bold cyan]\n")

    with engine.connect() as conn:
        # 1. 查看所有股票
        console.print("[bold]1. 股票列表:[/bold]")
        result = conn.execute(text("SELECT code, name, market FROM stocks ORDER BY code"))
        stocks = result.fetchall()

        if stocks:
            table = Table()
            table.add_column("股票代码", style="cyan")
            table.add_column("股票名称", style="green")
            table.add_column("市场", style="yellow")

            for stock in stocks:
                table.add_row(str(stock[0]), str(stock[1] or ""), str(stock[2]))

            console.print(table)
            console.print(f"总计: {len(stocks)} 只股票\n")
        else:
            console.print("[yellow]暂无股票数据[/yellow]\n")

        # 2. 查看财报数据
        console.print("[bold]2. 财报数据:[/bold]")
        result = conn.execute(text("""
            SELECT
                s.code,
                s.name,
                fr.report_year,
                fr.report_type,
                fr.created_at
            FROM financial_reports fr
            JOIN stocks s ON fr.stock_id = s.id
            ORDER BY s.code, fr.report_year DESC, fr.report_type
            LIMIT 20
        """))
        reports = result.fetchall()

        if reports:
            table = Table()
            table.add_column("股票", style="cyan")
            table.add_column("年份", justify="center")
            table.add_column("类型", justify="center")
            table.add_column("采集时间")

            for report in reports:
                table.add_row(
                    f"{report[0]} {report[1] or ''}",
                    str(report[2]),
                    str(report[3]),
                    str(report[4])[:19]
                )

            console.print(table)

            # 统计
            result = conn.execute(text("SELECT COUNT(*) FROM financial_reports"))
            total = result.scalar()
            console.print(f"总计: {total} 份财报\n")
        else:
            console.print("[yellow]暂无财报数据[/yellow]\n")

        # 3. 查看财务指标（示例：最新一条）
        if reports:
            console.print("[bold]3. 财务指标示例 (最新一条):[/bold]")
            result = conn.execute(text("""
                SELECT
                    s.code,
                    s.name,
                    fr.report_year,
                    fm.metric_name,
                    fm.value
                FROM financial_metrics fm
                JOIN financial_reports fr ON fm.report_id = fr.id
                JOIN stocks s ON fr.stock_id = s.id
                ORDER BY fr.created_at DESC
                LIMIT 20
            """))
            metrics = result.fetchall()

            if metrics:
                table = Table()
                table.add_column("股票", style="cyan")
                table.add_column("年份", justify="center")
                table.add_column("指标", style="yellow")
                table.add_column("数值", justify="right", style="green")

                for metric in metrics:
                    value = metric[4]
                    # 格式化数值
                    try:
                        value_num = float(value)
                        if value_num > 1000000:
                            value_str = f"{value_num/10000:.2f} 亿"
                        elif value_num > 10000:
                            value_str = f"{value_num/10000:.2f} 万"
                        else:
                            value_str = f"{value_num:.2f}"
                    except:
                        value_str = str(value)

                    table.add_row(
                        f"{metric[0]} {metric[1] or ''}",
                        str(metric[2]),
                        str(metric[3]),
                        value_str
                    )

                console.print(table)
            else:
                console.print("[yellow]暂无财务指标数据[/yellow]")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        import traceback
        traceback.print_exc()
