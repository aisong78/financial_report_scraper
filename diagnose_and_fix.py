#!/usr/bin/env python3
"""
数据诊断和修复工具

自动检测并修复财务数据中的缺失字段问题
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich import box
from src.database import db
from src.database.models import Stock, FinancialMetric

console = Console()


def diagnose_stock_data(stock_code: str):
    """
    诊断股票数据的完整性

    Args:
        stock_code: 股票代码

    Returns:
        (stock_id, missing_fields, metric_count)
    """
    console.print(f"\n[bold cyan]诊断股票: {stock_code}[/bold cyan]\n")

    with db.session_scope() as session:
        # 查找股票
        stock = session.query(Stock).filter_by(code=stock_code).first()

        if not stock:
            console.print(f"[red]✗ 股票不存在[/red]")
            return None, None, 0

        console.print(f"[green]✓ 股票信息: {stock.name} ({stock.market}/{stock.exchange})[/green]")

        # 查询所有财务数据
        metrics = session.query(FinancialMetric).filter_by(
            stock_id=stock.id
        ).order_by(FinancialMetric.report_date.desc()).all()

        if not metrics:
            console.print(f"[red]✗ 没有财务数据[/red]")
            return stock.id, None, 0

        console.print(f"[green]✓ 找到 {len(metrics)} 条财务记录[/green]\n")

        # 检查关键字段
        required_fields = {
            'roe': 'ROE（净资产收益率）',
            'asset_liability_ratio': '资产负债率',
            'ocf_to_net_profit': '经营现金流/净利润',
            'revenue_yoy': '营收同比增长率',
            'net_profit_yoy': '利润同比增长率',
            'pe_ratio': '市盈率',
            'gross_margin': '毛利率',
            'net_margin': '净利率',
            'current_ratio': '流动比率',
        }

        # 创建检查表格
        table = Table(title="字段完整性检查", box=box.ROUNDED)
        table.add_column("字段", style="cyan")
        table.add_column("中文名", style="dim")
        table.add_column("状态", justify="center")
        table.add_column("最新值", justify="right")

        latest_metric = metrics[0]
        missing_fields = []

        for field, name_zh in required_fields.items():
            value = getattr(latest_metric, field, None)

            if value is None:
                status = "[red]✗ 缺失[/red]"
                display_value = "[red]None[/red]"
                missing_fields.append(field)
            else:
                status = "[green]✓[/green]"
                if isinstance(value, float):
                    display_value = f"{value:.4f}"
                else:
                    display_value = str(value)

            table.add_row(field, name_zh, status, display_value)

        console.print(table)

        if missing_fields:
            console.print(f"\n[yellow]⚠ 发现 {len(missing_fields)} 个缺失字段[/yellow]")
            console.print(f"缺失字段: {', '.join(missing_fields)}")
        else:
            console.print(f"\n[green]✓ 所有关键字段完整[/green]")

        return stock.id, missing_fields, len(metrics)


def fix_stock_data(stock_code: str):
    """
    修复股票数据（重新初始化）

    Args:
        stock_code: 股票代码
    """
    console.print(f"\n[bold yellow]开始修复股票数据: {stock_code}[/bold yellow]\n")

    # 询问用户确认
    console.print("[yellow]这将删除现有的财务数据并重新创建。[/yellow]")
    console.print("[yellow]股票基本信息会保留。[/yellow]")

    confirm = input("\n是否继续？(y/N): ")

    if confirm.lower() != 'y':
        console.print("[dim]已取消[/dim]")
        return

    with db.session_scope() as session:
        # 删除旧的财务数据
        stock = session.query(Stock).filter_by(code=stock_code).first()

        if stock:
            deleted_count = session.query(FinancialMetric).filter_by(
                stock_id=stock.id
            ).delete()

            console.print(f"[dim]删除了 {deleted_count} 条旧数据[/dim]")

    # 使用init_stock_data重新初始化
    console.print(f"\n[bold]重新初始化数据...[/bold]\n")

    import subprocess
    result = subprocess.run(
        [sys.executable, 'init_stock_data.py', stock_code],
        capture_output=False
    )

    if result.returncode == 0:
        console.print(f"\n[bold green]✓ 修复完成！[/bold green]")
    else:
        console.print(f"\n[bold red]✗ 修复失败[/bold red]")


def main():
    """主函数"""
    console.print("""
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          数据诊断和修复工具                               ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]

此工具将：
1. 检查股票财务数据的完整性
2. 发现缺失的关键字段
3. 提供自动修复选项（重新初始化数据）
    """)

    # 初始化数据库
    db.init_database()

    # 获取股票代码
    if len(sys.argv) > 1:
        stock_codes = sys.argv[1:]
    else:
        code_input = input("请输入股票代码（多个用空格分隔）: ").strip()
        if not code_input:
            console.print("[red]未输入股票代码[/red]")
            return
        stock_codes = code_input.split()

    # 诊断每只股票
    results = {}

    for code in stock_codes:
        stock_id, missing_fields, count = diagnose_stock_data(code)
        results[code] = {
            'stock_id': stock_id,
            'missing_fields': missing_fields,
            'metric_count': count
        }

    # 汇总报告
    console.print(f"\n[bold cyan]═══ 诊断汇总 ═══[/bold cyan]\n")

    summary_table = Table(box=box.ROUNDED)
    summary_table.add_column("股票代码", style="cyan")
    summary_table.add_column("数据条数", justify="right")
    summary_table.add_column("缺失字段数", justify="right")
    summary_table.add_column("状态", justify="center")

    need_fix = []

    for code, result in results.items():
        if result['stock_id'] is None:
            summary_table.add_row(
                code,
                "0",
                "N/A",
                "[red]不存在[/red]"
            )
        elif result['missing_fields']:
            summary_table.add_row(
                code,
                str(result['metric_count']),
                str(len(result['missing_fields'])),
                "[yellow]需修复[/yellow]"
            )
            need_fix.append(code)
        else:
            summary_table.add_row(
                code,
                str(result['metric_count']),
                "0",
                "[green]正常[/green]"
            )

    console.print(summary_table)

    # 提供修复选项
    if need_fix:
        console.print(f"\n[yellow]发现 {len(need_fix)} 只股票需要修复: {', '.join(need_fix)}[/yellow]")
        console.print("\n修复选项:")
        console.print("  1. 全部修复")
        console.print("  2. 选择性修复")
        console.print("  3. 跳过")

        choice = input("\n请选择 (1/2/3): ").strip()

        if choice == '1':
            for code in need_fix:
                fix_stock_data(code)
        elif choice == '2':
            for code in need_fix:
                console.print(f"\n修复 {code}?")
                confirm = input("(y/N): ")
                if confirm.lower() == 'y':
                    fix_stock_data(code)
        else:
            console.print("[dim]已跳过修复[/dim]")
    else:
        console.print(f"\n[green]✓ 所有股票数据完整，无需修复！[/green]")

    console.print(f"\n[bold]诊断完成！[/bold]\n")


if __name__ == "__main__":
    main()
