#!/usr/bin/env python3
"""
财务数据采集工具

功能：
- 自动下载并解析财务报告
- 支持自定义年限和报告类型
- 支持增量更新
- 交互式用户确认
- 多数据源交叉验证

使用示例：
    # 采集5年全部数据（年报+半年报+季报）
    python collect_data.py 688005

    # 采集指定年限
    python collect_data.py 600519 --years 3

    # 只采集年报
    python collect_data.py 600519 --reports annual

    # 采集多种报告
    python collect_data.py 600519 --reports annual,semi

    # 增量更新（只更新最新数据）
    python collect_data.py 600519 --incremental

    # 批量采集
    python collect_data.py 688005 600519 000858

    # 非交互模式（直接采集，不询问）
    python collect_data.py 688005 --no-interactive
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.table import Table
from rich import box

from src.database import db
from src.services.data_collector import DataCollector

console = Console()


@click.command()
@click.argument('stock_codes', nargs=-1, required=True)
@click.option(
    '--years', '-y',
    default=5,
    type=int,
    help='采集年限（默认：5年）'
)
@click.option(
    '--reports', '-r',
    default='annual,semi,quarter',
    help='报告类型：annual(年报), semi(半年报), quarter(季报)，逗号分隔'
)
@click.option(
    '--incremental', '-i',
    is_flag=True,
    help='增量更新模式（只更新最新数据）'
)
@click.option(
    '--no-interactive',
    is_flag=True,
    help='非交互模式（不询问用户，直接采集）'
)
@click.option(
    '--check-only',
    is_flag=True,
    help='仅检查数据完整性，不采集'
)
def main(stock_codes, years, reports, incremental, no_interactive, check_only):
    """
    财务数据采集工具

    采集指定股票的财务报告数据并入库

    示例：

        \b
        # 采集5年全部数据
        python collect_data.py 688005

        \b
        # 只采集年报
        python collect_data.py 600519 --reports annual

        \b
        # 增量更新
        python collect_data.py 600519 --incremental

        \b
        # 批量采集
        python collect_data.py 688005 600519 000858
    """
    # 初始化数据库
    db.init_database()

    # 解析报告类型
    report_types = [r.strip() for r in reports.split(',')]

    # 验证报告类型
    valid_types = {'annual', 'semi', 'quarter'}
    invalid_types = set(report_types) - valid_types

    if invalid_types:
        console.print(f"[red]错误: 无效的报告类型 {invalid_types}[/red]")
        console.print(f"有效的类型: {', '.join(valid_types)}")
        return

    # 显示采集计划
    console.print(f"""
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          财务数据采集工具                                 ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]

[bold]采集计划:[/bold]
  • 股票数量: {len(stock_codes)}
  • 采集年限: {years} 年
  • 报告类型: {', '.join([_type_name(t) for t in report_types])}
  • 模式: {'增量更新' if incremental else '完整采集'}
  • 交互: {'否' if no_interactive else '是'}
    """)

    # 创建采集器
    collector = DataCollector()

    # 统计结果
    total_stocks = len(stock_codes)
    success_count = 0
    skipped_count = 0
    failed_count = 0

    # 遍历所有股票
    for i, stock_code in enumerate(stock_codes, 1):
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]处理股票 {i}/{total_stocks}: {stock_code}[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")

        try:
            # 检查数据完整性
            report = collector.check_data_completeness(
                stock_code,
                years,
                report_types
            )

            # 仅检查模式
            if check_only:
                collector.display_completeness_report(report)
                continue

            # 如果数据完整，跳过
            if report.is_complete and not incremental:
                console.print(f"\n[green]✓ {stock_code} 数据已完整，跳过采集[/green]")
                skipped_count += 1
                continue

            # 交互模式：询问用户
            if not no_interactive:
                confirmed = collector.ask_user_to_collect(stock_code, report)

                if not confirmed:
                    console.print(f"[dim]跳过 {stock_code}[/dim]")
                    skipped_count += 1
                    continue

                is_incremental = (confirmed == 'incremental')
            else:
                # 非交互模式：显示完整性报告后直接采集
                collector.display_completeness_report(report)
                console.print(f"[cyan]开始自动采集 {stock_code}...[/cyan]")
                is_incremental = incremental

            # 执行采集
            success = collector.collect_stock_data(
                stock_code,
                years,
                report_types,
                is_incremental
            )

            if success:
                success_count += 1
                console.print(f"\n[bold green]✅ {stock_code} 采集成功[/bold green]")
            else:
                failed_count += 1
                console.print(f"\n[bold red]✗ {stock_code} 采集失败[/bold red]")

        except KeyboardInterrupt:
            console.print(f"\n\n[yellow]用户终止采集[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]✗ {stock_code} 采集出错: {e}[/bold red]")
            failed_count += 1

            # 询问是否继续
            if not no_interactive and i < total_stocks:
                choice = input("\n是否继续处理下一只股票？(y/n): ").strip().lower()
                if choice != 'y':
                    break

    # 显示汇总
    console.print(f"""
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          采集完成                                         ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]
    """)

    # 汇总表格
    summary_table = Table(title="采集汇总", box=box.ROUNDED)
    summary_table.add_column("状态", style="cyan")
    summary_table.add_column("数量", justify="right", style="bold")
    summary_table.add_column("百分比", justify="right")

    summary_table.add_row("成功", str(success_count), f"{success_count/total_stocks*100:.1f}%")
    summary_table.add_row("跳过", str(skipped_count), f"{skipped_count/total_stocks*100:.1f}%")
    summary_table.add_row("失败", str(failed_count), f"{failed_count/total_stocks*100:.1f}%")
    summary_table.add_row("总计", str(total_stocks), "100.0%")

    console.print(summary_table)

    # 下一步提示
    if success_count > 0:
        console.print(f"""
[bold green]✓ 数据采集完成！[/bold green]

下一步可以：
  [cyan]python stock_analyzer.py analyze {stock_codes[0]}[/cyan]
  [cyan]python stock_analyzer.py screen {stock_codes[0]}[/cyan]
        """)


def _type_name(report_type: str) -> str:
    """获取报告类型的中文名称"""
    names = {
        'annual': '年报',
        'semi': '半年报',
        'quarter': '季报'
    }
    return names.get(report_type, report_type)


if __name__ == '__main__':
    main()
