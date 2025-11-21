"""
Phase 2 分析框架演示

演示如何使用分析框架评估股票
"""

from src.analyzers import load_framework
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def demo_value_investing():
    """演示价值投资框架"""
    console.print("\n[bold blue]═══ 价值投资框架演示 ═══[/bold blue]\n")

    # 模拟茅台的财务指标
    metrics = {
        # 盈利能力
        'roe': 0.28,  # 28% ROE（优秀）
        'gross_margin': 0.91,  # 91% 毛利率（超优秀）
        'net_margin': 0.52,  # 52% 净利率（超优秀）
        'revenue_growth_rate': 0.18,  # 18% 营收增长（良好）

        # 财务稳健
        'debt_to_asset_ratio': 0.20,  # 20% 负债率（优秀）
        'current_ratio': 2.8,  # 2.8 流动比率（优秀）
        'operating_cashflow_ratio': 1.3,  # 1.3 现金流/利润（优秀）

        # 护城河
        'roe_consistency': 3,  # 连续3年ROE>15%
        'gross_margin_stability': 0.03,  # 毛利率波动3%
        'market_position': 'leader',  # 行业龙头

        # 估值
        'pe_ratio': 32,  # PE 32（略高）
        'pb_ratio': 8.5,  # PB 8.5（偏高）
    }

    # 加载框架并分析
    framework = load_framework('value_investing')
    result = framework.analyze(metrics)

    # 显示结果
    print_analysis_result(result, "贵州茅台")


def demo_growth_investing():
    """演示成长投资框架"""
    console.print("\n[bold green]═══ 成长投资框架演示 ═══[/bold green]\n")

    # 模拟宁德时代的财务指标
    metrics = {
        # 成长性
        'revenue_growth_rate': 0.35,  # 35% 营收增长（优秀）
        'profit_growth_rate': 0.28,  # 28% 利润增长（优秀）
        'growth_acceleration': 'stable',  # 稳定增长

        # 扩张能力
        'asset_turnover': 1.8,  # 1.8 资产周转率（良好）
        'roe': 0.22,  # 22% ROE（优秀）
        'capex_growth_rate': 0.25,  # 25% 资本开支增长（合理）

        # 盈利质量
        'gross_margin': 0.28,  # 28% 毛利率（良好）
        'operating_cashflow_ratio': 0.85,  # 0.85 现金流/利润（优秀）

        # 估值
        'peg_ratio': 1.2,  # PEG 1.2（略高但可接受）
    }

    # 加载框架并分析
    framework = load_framework('growth_investing')
    result = framework.analyze(metrics)

    # 显示结果
    print_analysis_result(result, "宁德时代")


def print_analysis_result(result, stock_name: str):
    """打印分析结果（美化版）"""

    # 1. 总分和评级
    console.print(Panel(
        f"[bold]{stock_name}[/bold]\n"
        f"框架: {result.framework_name}\n"
        f"{result.framework_description}",
        title="[bold cyan]股票分析报告[/bold cyan]",
        border_style="cyan"
    ))

    # 总分
    score_color = "green" if result.score_percentage >= 80 else "yellow" if result.score_percentage >= 60 else "red"
    console.print(f"\n[bold]总分: [{score_color}]{result.total_score:.1f}/{result.max_score}[/{score_color}]  "
                  f"得分率: [{score_color}]{result.score_percentage:.1f}%[/{score_color}]  "
                  f"评级: [{score_color}]{result.grade}[/{score_color}][/bold]\n")

    # 2. 各维度得分
    for category in result.category_scores:
        # 分类标题
        category_color = "green" if category.score_percentage >= 80 else "yellow" if category.score_percentage >= 60 else "red"
        console.print(f"[bold]{category.name}[/bold]  "
                      f"[{category_color}]{category.score:.1f}/{category.max_score} ({category.score_percentage:.0f}%)[/{category_color}]")

        # 创建指标表格
        table = Table(show_header=True, header_style="bold", box=box.SIMPLE, padding=(0, 1))
        table.add_column("指标", style="cyan", width=20)
        table.add_column("数值", justify="right", width=12)
        table.add_column("得分", justify="right", width=10)
        table.add_column("评价", width=20)

        for metric in category.metrics:
            # 格式化数值
            if metric.value is None:
                value_str = "N/A"
            elif isinstance(metric.value, (int, float)):
                if metric.unit == "%":
                    value_str = f"{metric.value * 100:.1f}%"
                else:
                    value_str = f"{metric.value:.2f}{metric.unit}"
            else:
                value_str = str(metric.value)

            # 得分颜色
            score_pct = metric.score / metric.max_score if metric.max_score > 0 else 0
            if score_pct >= 0.8:
                score_color = "green"
            elif score_pct >= 0.5:
                score_color = "yellow"
            else:
                score_color = "red"

            table.add_row(
                metric.display_name,
                value_str,
                f"[{score_color}]{metric.score:.1f}/{metric.max_score}[/{score_color}]",
                metric.comment
            )

        console.print(table)
        console.print()

    # 3. 投资建议
    risk_color = "green" if result.risk_level in ["低", "中低"] else "yellow" if result.risk_level == "中" else "red"

    console.print(Panel(
        f"[bold]{result.recommendation}[/bold]\n\n"
        f"{result.reasoning}\n\n"
        f"风险等级: [{risk_color}]{result.risk_level}[/{risk_color}]",
        title="[bold yellow]投资建议[/bold yellow]",
        border_style="yellow"
    ))

    # 4. 风险提示
    if result.risk_alerts:
        console.print("\n[bold red]⚠️  风险提示:[/bold red]")
        for alert in result.risk_alerts:
            console.print(f"  • {alert}")
    else:
        console.print("\n[bold green]✓ 未发现明显风险[/bold green]")

    console.print("\n" + "─" * 80 + "\n")


def main():
    """主函数"""
    console.print("""
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          Phase 2 - 投资分析框架演示                      ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]

本演示展示如何使用两种经典投资框架分析股票：
1. 价值投资框架（巴菲特风格）
2. 成长投资框架（彼得·林奇风格）
    """)

    try:
        # 演示1：价值投资框架
        demo_value_investing()

        # 演示2：成长投资框架
        demo_growth_investing()

        console.print("[bold green]✓ 演示完成！[/bold green]\n")
        console.print("说明：")
        console.print("  • 本演示使用模拟数据")
        console.print("  • 实际使用时会从数据库读取真实财报数据")
        console.print("  • 评分规则可通过 config/frameworks/*.yaml 配置\n")

    except Exception as e:
        console.print(f"\n[bold red]错误: {e}[/bold red]\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
