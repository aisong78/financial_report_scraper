"""
筛选框架演示

演示如何使用筛选型框架进行股票筛选
"""

from src.analyzers import load_screener
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def demo_quality_stock_screener():
    """演示优质白马股筛选"""
    console.print("\n[bold cyan]═══ 优质白马股筛选框架演示 ═══[/bold cyan]\n")

    # 加载筛选框架
    screener = load_screener('quality_stock_screener')

    # 示例1：贵州茅台（应该通过）
    console.print("[bold]示例1：贵州茅台（优质白马股）[/bold]\n")

    maotai_current = {
        # 核心财务指标
        'roe': 0.28,
        'gross_margin': 0.91,
        'revenue_growth_rate_qoq': 0.18,
        'profit_growth_rate_qoq': 0.16,
        'dividend_paid': 30000000000,  # 300亿分红
        'dividend_payout_ratio': 0.72,  # 72%分红率

        # 估值与性价比
        'market_cap': 280000000000,  # 2.8万亿市值
        'pe_ratio': 32,
        'peg_ratio': 1.8,
        'dividend_yield': 0.022,  # 2.2%股息率

        # 风险控制
        'violations': 0,
        'fraud': 0,
        'esg_rating': 'AA',
    }

    # 历史数据（最近5年，倒序）
    maotai_history = [
        {'roe': 0.28, 'gross_margin': 0.91, 'net_profit': 52600000000, 'dividend_paid': 30000000000},  # 2023
        {'roe': 0.30, 'gross_margin': 0.92, 'net_profit': 52000000000, 'dividend_paid': 29000000000},  # 2022
        {'roe': 0.32, 'gross_margin': 0.91, 'net_profit': 46600000000, 'dividend_paid': 24000000000},  # 2021
        {'roe': 0.28, 'gross_margin': 0.91, 'net_profit': 40000000000, 'dividend_paid': 20000000000},  # 2020
        {'roe': 0.30, 'gross_margin': 0.90, 'net_profit': 35200000000, 'dividend_paid': 17000000000},  # 2019
    ]

    result1 = screener.screen(maotai_current, maotai_history)
    print_screening_result(result1, "贵州茅台")

    # 示例2：某成长股（部分通过）
    console.print("\n[bold]示例2：某成长股（部分指标不达标）[/bold]\n")

    growth_current = {
        # 核心财务指标
        'roe': 0.18,  # ROE不错
        'gross_margin': 0.25,  # 毛利率偏低（<30%）
        'revenue_growth_rate_qoq': 0.35,  # 增速很快
        'profit_growth_rate_qoq': 0.28,
        'dividend_paid': 0,  # 不分红（成长期）
        'dividend_payout_ratio': 0,

        # 估值与性价比
        'market_cap': 15000000000,  # 150亿
        'pe_ratio': 45,  # PE偏高（>20）
        'peg_ratio': 1.3,  # PEG合理
        'dividend_yield': 0,

        # 风险控制
        'violations': 0,
        'fraud': 0,
        'esg_rating': 'BBB',
    }

    growth_history = [
        {'roe': 0.18, 'gross_margin': 0.25, 'net_profit': 800000000, 'dividend_paid': 0},  # 2023
        {'roe': 0.16, 'gross_margin': 0.26, 'net_profit': 600000000, 'dividend_paid': 0},  # 2022
        {'roe': 0.15, 'gross_margin': 0.24, 'net_profit': 450000000, 'dividend_paid': 0},  # 2021
        {'roe': 0.14, 'gross_margin': 0.23, 'net_profit': 320000000, 'dividend_paid': 0},  # 2020
        {'roe': 0.12, 'gross_margin': 0.22, 'net_profit': 220000000, 'dividend_paid': 0},  # 2019
    ]

    result2 = screener.screen(growth_current, growth_history)
    print_screening_result(result2, "某成长股")

    # 示例3：问题股（未通过）
    console.print("\n[bold]示例3：某问题股（多项指标不达标）[/bold]\n")

    problem_current = {
        # 核心财务指标
        'roe': 0.08,  # ROE低
        'gross_margin': 0.15,  # 毛利率很低
        'revenue_growth_rate_qoq': -0.05,  # 负增长
        'profit_growth_rate_qoq': -0.12,
        'dividend_paid': 50000000,
        'dividend_payout_ratio': 0.15,

        # 估值与性价比
        'market_cap': 20000000000,  # 200亿
        'pe_ratio': 35,
        'peg_ratio': None,  # 负增长无法计算PEG
        'dividend_yield': 0.008,

        # 风险控制
        'violations': 1,  # 有违规记录
        'fraud': 0,
        'esg_rating': 'B',  # 评级低
    }

    problem_history = [
        {'roe': 0.08, 'gross_margin': 0.15, 'net_profit': 300000000, 'dividend_paid': 50000000},
        {'roe': 0.09, 'gross_margin': 0.16, 'net_profit': 350000000, 'dividend_paid': 60000000},
        {'roe': 0.12, 'gross_margin': 0.18, 'net_profit': 400000000, 'dividend_paid': 70000000},
        {'roe': 0.14, 'gross_margin': 0.20, 'net_profit': 420000000, 'dividend_paid': 80000000},
        {'roe': 0.15, 'gross_margin': 0.22, 'net_profit': 450000000, 'dividend_paid': 90000000},
    ]

    result3 = screener.screen(problem_current, problem_history)
    print_screening_result(result3, "某问题股")


def print_screening_result(result: 'ScreeningResult', stock_name: str):
    """打印筛选结果（美化版）"""

    # 1. 标题和总体结果
    result_color = "green" if result.passed else "red" if result.result_type == "fail" else "yellow"

    console.print(Panel(
        f"[bold]{stock_name}[/bold]\n"
        f"框架: {result.framework_name}\n"
        f"{result.framework_description}\n\n"
        f"[{result_color}]{result.status_icon} 筛选结果: {result.result_type.upper()}[/{result_color}]\n"
        f"通过率: [{result_color}]{result.total_pass_rate:.1%}[/{result_color}]",
        title="[bold cyan]筛选报告[/bold cyan]",
        border_style=result_color
    ))

    # 2. 各分类结果
    for category in result.category_results:
        category_color = "green" if category.passed else "red"

        console.print(f"\n[bold]{category.status_icon} {category.name}[/bold]  "
                      f"[{category_color}]({category.pass_rate:.0%} 通过)[/{category_color}]")

        # 创建标准表格
        table = Table(show_header=True, header_style="bold", box=box.SIMPLE, padding=(0, 1))
        table.add_column("标准", style="cyan", width=30)
        table.add_column("状态", justify="center", width=8)
        table.add_column("详情", width=40)

        for criterion in category.criteria_results:
            status_color = "green" if criterion.passed else "red"
            importance_badge = ""
            if criterion.importance == "critical":
                importance_badge = " [bold red]关键[/bold red]"
            elif criterion.importance == "high":
                importance_badge = " [yellow]重要[/yellow]"

            table.add_row(
                criterion.name + importance_badge,
                f"[{status_color}]{criterion.status_icon}[/{status_color}]",
                criterion.reason
            )

        console.print(table)

    # 3. 未通过的条件汇总
    if result.failed_criteria:
        console.print(f"\n[bold red]❌ 未通过的条件（{len(result.failed_criteria)}项）:[/bold red]")

        # 按重要性排序
        critical = [c for c in result.failed_criteria if c.importance == 'critical']
        high = [c for c in result.failed_criteria if c.importance == 'high']
        medium = [c for c in result.failed_criteria if c.importance == 'medium']

        if critical:
            console.print("\n  [bold red]关键指标：[/bold red]")
            for c in critical:
                console.print(f"    • {c.name}: {c.reason}")

        if high:
            console.print("\n  [bold yellow]重要指标：[/bold yellow]")
            for c in high:
                console.print(f"    • {c.name}: {c.reason}")

        if medium:
            console.print("\n  [dim]一般指标：[/dim]")
            for c in medium:
                console.print(f"    • {c.name}: {c.reason}")

    # 4. 改进建议
    if result.suggestions:
        console.print("\n[bold blue]💡 改进建议:[/bold blue]")
        for suggestion in result.suggestions:
            console.print(f"  {suggestion}")

    # 5. 结论
    console.print()
    if result.passed:
        console.print(Panel(
            "[bold green]✅ 该股票通过筛选，符合优质白马股标准！[/bold green]\n"
            "建议：加入备选池，进一步深入研究",
            border_style="green"
        ))
    elif result.result_type == "partial":
        console.print(Panel(
            "[bold yellow]⚠️ 该股票部分通过筛选[/bold yellow]\n"
            "建议：密切关注改善情况，谨慎决策",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[bold red]❌ 该股票未通过筛选[/bold red]\n"
            "建议：暂不考虑，关注其他标的",
            border_style="red"
        ))

    console.print("\n" + "─" * 100 + "\n")


def main():
    """主函数"""
    console.print("""
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          筛选型框架演示                                   ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]

本演示展示如何使用筛选型框架进行股票筛选：
• 硬性门槛：所有条件必须满足
• 时间序列：支持"连续N年"、"复合增长率"等检查
• 重要性分级：critical/high/medium
• 多维度评估：财务、估值、风险控制

对比评分型框架：
• 评分型：给出0-100分，适合比较排名
• 筛选型：给出Pass/Fail，适合过滤选股
    """)

    try:
        demo_quality_stock_screener()

        console.print("[bold green]✓ 演示完成！[/bold green]\n")
        console.print("说明：")
        console.print("  • 本演示使用模拟数据")
        console.print("  • 实际使用时会从数据库读取真实财报数据")
        console.print("  • 筛选规则可通过 config/frameworks/quality_stock_screener.yaml 配置\n")

    except Exception as e:
        console.print(f"\n[bold red]错误: {e}[/bold red]\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
