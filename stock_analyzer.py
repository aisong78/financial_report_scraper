#!/usr/bin/env python3
"""
Stock Analyzer CLI Tool

命令行股票分析工具
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.database import db
from src.database.models import Stock, FinancialMetric, FinancialReport
from src.analyzers import load_framework, load_screener
from src.services import MarketDataService
from src.data_sources import MockDataSource

console = Console()


@click.group()
@click.version_option(version='0.1.0', prog_name='stock-analyzer')
def cli():
    """
    股票分析命令行工具

    支持评分分析、筛选、数据更新等功能
    """
    # 初始化数据库
    db.init_database()


@cli.command()
@click.argument('stock_codes', nargs=-1, required=True)
@click.option('--framework', '-f', default='quality_stock_screener',
              help='筛选框架名称（默认：quality_stock_screener）')
@click.option('--detail/--no-detail', default=True,
              help='是否显示详细信息')
def screen(stock_codes, framework, detail):
    """
    筛选股票（Pass/Fail）

    示例：
        stock-analyzer screen 600519
        stock-analyzer screen 600519 000858 002594
        stock-analyzer screen 600519 --framework quality_stock_screener
    """
    console.print(f"\n[bold cyan]使用筛选框架: {framework}[/bold cyan]\n")

    # 加载筛选框架
    try:
        screener = load_screener(framework)
    except Exception as e:
        console.print(f"[bold red]错误: 加载筛选框架失败 - {e}[/bold red]")
        return

    results = []

    for stock_code in stock_codes:
        result = screen_single_stock(stock_code, screener, detail)
        if result:
            results.append(result)

    # 显示汇总
    if len(stock_codes) > 1:
        print_screen_summary(results)


def screen_single_stock(stock_code, screener, detail=True):
    """筛选单只股票"""
    console.print(f"[bold]正在筛选: {stock_code}[/bold]")

    with db.session_scope() as session:
        # 查询股票
        stock = session.query(Stock).filter_by(code=stock_code).first()

        if not stock:
            console.print(f"[yellow]⚠ 数据库中未找到股票 {stock_code}[/yellow]")
            console.print(f"提示: 使用 'stock-analyzer info {stock_code}' 获取股票信息")
            return None

        # 获取财务数据
        current_metrics, historical_metrics = get_financial_data(session, stock.id)

        if not current_metrics:
            console.print(f"[yellow]⚠ 股票 {stock.name} 没有财务数据[/yellow]")
            return None

        # 执行筛选
        result = screener.screen(
            current_metrics=current_metrics,
            historical_metrics=historical_metrics,
            industry=stock.industry
        )

        # 显示结果
        if detail:
            from demo_screener import print_screening_result
            print_screening_result(result, stock.name)
        else:
            # 简化显示
            status_color = "green" if result.passed else "red"
            console.print(f"  [{status_color}]{result.status_icon} {stock.name}: {result.result_type.upper()}[/{status_color}] (通过率: {result.total_pass_rate:.1%})\n")

        return {
            'code': stock_code,
            'name': stock.name,
            'result': result
        }


@cli.command()
@click.argument('stock_codes', nargs=-1, required=True)
@click.option('--framework', '-f', default='value_investing',
              help='分析框架名称（默认：value_investing）')
@click.option('--detail/--no-detail', default=True,
              help='是否显示详细信息')
def analyze(stock_codes, framework, detail):
    """
    分析股票（评分0-100）

    示例：
        stock-analyzer analyze 600519
        stock-analyzer analyze 600519 000858
        stock-analyzer analyze 600519 --framework growth_investing
    """
    console.print(f"\n[bold cyan]使用分析框架: {framework}[/bold cyan]\n")

    # 加载分析框架
    try:
        analyzer = load_framework(framework)
    except Exception as e:
        console.print(f"[bold red]错误: 加载分析框架失败 - {e}[/bold red]")
        return

    results = []

    for stock_code in stock_codes:
        result = analyze_single_stock(stock_code, analyzer, detail)
        if result:
            results.append(result)

    # 显示汇总对比
    if len(stock_codes) > 1:
        print_analyze_comparison(results)


def analyze_single_stock(stock_code, analyzer, detail=True):
    """分析单只股票"""
    console.print(f"[bold]正在分析: {stock_code}[/bold]")

    with db.session_scope() as session:
        # 查询股票
        stock = session.query(Stock).filter_by(code=stock_code).first()

        if not stock:
            console.print(f"[yellow]⚠ 数据库中未找到股票 {stock_code}[/yellow]")
            return None

        # 获取财务数据
        current_metrics, historical_metrics = get_financial_data(session, stock.id)

        if not current_metrics:
            console.print(f"[yellow]⚠ 股票 {stock.name} 没有财务数据[/yellow]")
            return None

        # 执行分析
        result = analyzer.analyze(current_metrics)

        # 显示结果
        if detail:
            print_analysis_result(result, stock.name)
        else:
            # 简化显示
            score_color = "green" if result.total_score >= 80 else "yellow" if result.total_score >= 60 else "red"
            rating = get_rating_from_score(result.total_score)
            console.print(f"  [{score_color}]{stock.name}: {result.total_score:.1f}分[/{score_color}] ({rating})\n")

        return {
            'code': stock_code,
            'name': stock.name,
            'result': result
        }


@cli.command()
@click.argument('stock_code')
def info(stock_code):
    """
    查看股票信息

    示例：
        stock-analyzer info 600519
    """
    console.print(f"\n[bold cyan]股票信息: {stock_code}[/bold cyan]\n")

    # 尝试从数据库获取
    with db.session_scope() as session:
        stock = session.query(Stock).filter_by(code=stock_code).first()

        if stock:
            # 显示数据库中的信息
            print_stock_info_from_db(stock, session)
        else:
            # 从数据源获取
            console.print(f"[yellow]数据库中未找到 {stock_code}，尝试从数据源获取...[/yellow]\n")
            print_stock_info_from_source(stock_code)


@cli.command()
@click.argument('stock_code')
@click.option('--years', '-y', default=5, help='获取年数（默认：5年）')
def update_data(stock_code, years):
    """
    更新市场数据（市值、分红等）

    示例：
        stock-analyzer update-data 600519
        stock-analyzer update-data 600519 --years 10
    """
    console.print(f"\n[bold cyan]更新市场数据: {stock_code}[/bold cyan]\n")

    # 创建市场数据服务（使用模拟数据源）
    service = MarketDataService(data_source=MockDataSource())

    # 确保数据库中有这只股票
    with db.session_scope() as session:
        stock = session.query(Stock).filter_by(code=stock_code).first()

        if not stock:
            console.print(f"[yellow]数据库中未找到股票 {stock_code}，正在创建...[/yellow]")

            stock_info = service.data_source.get_stock_info(stock_code)
            if stock_info:
                stock = Stock(
                    code=stock_info['code'],
                    name=stock_info['name'],
                    market=stock_info['market'],
                    exchange=stock_info['exchange'],
                    industry=stock_info.get('industry', '')
                )
                session.add(stock)
                session.flush()
                console.print(f"✓ 创建股票: {stock.name}\n")
            else:
                console.print(f"[red]✗ 无法获取股票信息[/red]")
                return

    # 更新市场数据
    console.print(f"正在获取 {years} 年市场数据...")

    success = service.enrich_financial_metrics(stock_code, years=years)

    if success:
        console.print(f"\n[bold green]✓ 市场数据更新成功！[/bold green]\n")

        # 显示更新后的数据
        valuation_history = service.get_stock_valuation_history(stock_code, years=years)

        if valuation_history:
            table = Table(title="估值历史", box=box.ROUNDED)
            table.add_column("年份", justify="center", style="cyan")
            table.add_column("PE", justify="right", style="yellow")
            table.add_column("市值", justify="right", style="green")

            for data in valuation_history:
                pe = f"{data['pe_ratio']:.1f}" if data['pe_ratio'] else "N/A"
                mc = f"{data['market_cap']/1e8:.0f}亿" if data['market_cap'] else "N/A"
                table.add_row(str(data['year']), pe, mc)

            console.print(table)
    else:
        console.print(f"[yellow]⚠ 市场数据更新部分失败[/yellow]")


@cli.command()
def list_frameworks():
    """列出所有可用的分析框架"""
    console.print("\n[bold cyan]可用的分析框架:[/bold cyan]\n")

    # 评分型框架
    console.print("[bold]评分型框架（Scoring）:[/bold]")
    console.print("  • value_investing - 价值投资框架（巴菲特风格）")
    console.print("  • growth_investing - 成长投资框架（彼得·林奇风格）")

    # 筛选型框架
    console.print("\n[bold]筛选型框架（Screening）:[/bold]")
    console.print("  • quality_stock_screener - 优质白马股筛选框架")

    console.print()


# ===== 辅助函数 =====

def get_rating_from_score(score):
    """根据分数获取评级"""
    if score >= 90:
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 70:
        return "中等"
    elif score >= 60:
        return "及格"
    else:
        return "不及格"


def get_financial_data(session, stock_id, years=5):
    """获取财务数据"""
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=365 * years)

    metrics_list = (
        session.query(FinancialMetric)
        .join(FinancialReport)
        .filter(
            FinancialMetric.stock_id == stock_id,
            FinancialReport.report_type == 'annual',
            FinancialMetric.report_date >= cutoff_date
        )
        .order_by(FinancialMetric.report_date.desc())
        .all()
    )

    if not metrics_list:
        return None, None

    def metric_to_dict(metric):
        return {
            'report_date': metric.report_date,
            'revenue': float(metric.revenue) if metric.revenue else None,
            'net_profit': float(metric.net_profit) if metric.net_profit else None,
            'gross_margin': float(metric.gross_margin) if metric.gross_margin else None,
            'net_margin': float(metric.net_margin) if metric.net_margin else None,
            'roe': float(metric.roe) if metric.roe else None,
            'roa': float(metric.roa) if metric.roa else None,
            'revenue_growth_rate_yoy': float(metric.revenue_yoy) if metric.revenue_yoy else None,
            'revenue_growth_rate_qoq': float(metric.revenue_qoq) if metric.revenue_qoq else None,
            'profit_growth_rate_yoy': float(metric.net_profit_yoy) if metric.net_profit_yoy else None,
            'profit_growth_rate_qoq': float(metric.net_profit_qoq) if metric.net_profit_qoq else None,
            'total_assets': float(metric.total_assets) if metric.total_assets else None,
            'total_liabilities': float(metric.total_liabilities) if metric.total_liabilities else None,
            'total_equity': float(metric.total_equity) if metric.total_equity else None,
            'debt_to_asset_ratio': float(metric.asset_liability_ratio) if metric.asset_liability_ratio else None,
            'current_ratio': float(metric.current_ratio) if metric.current_ratio else None,
            'operating_cash_flow': float(metric.operating_cash_flow) if metric.operating_cash_flow else None,
            'operating_cashflow_ratio': float(metric.ocf_to_net_profit) if metric.ocf_to_net_profit else None,
            'pe_ratio': float(metric.pe_ratio) if metric.pe_ratio else None,
            'pb_ratio': float(metric.pb_ratio) if metric.pb_ratio else None,
            'peg_ratio': float(metric.peg_ratio) if metric.peg_ratio else None,
            'asset_turnover': float(metric.asset_turnover) if metric.asset_turnover else None,
            'dividend_paid': metric.extra_metrics.get('dividend_paid', 0) if metric.extra_metrics else 0,
            'dividend_payout_ratio': metric.extra_metrics.get('dividend_payout_ratio', 0) if metric.extra_metrics else 0,
            'dividend_yield': metric.extra_metrics.get('dividend_yield', 0) if metric.extra_metrics else 0,
            'market_cap': metric.extra_metrics.get('market_cap', 0) if metric.extra_metrics else 0,
        }

    current_metrics = metric_to_dict(metrics_list[0])
    historical_metrics = [metric_to_dict(m) for m in metrics_list]

    return current_metrics, historical_metrics


def print_analysis_result(result, stock_name):
    """打印分析结果"""
    score_color = "green" if result.total_score >= 80 else "yellow" if result.total_score >= 60 else "red"
    rating = get_rating_from_score(result.total_score)

    console.print(Panel(
        f"[bold]{stock_name}[/bold]\n"
        f"框架: {result.framework_name}\n\n"
        f"[{score_color}]总分: {result.total_score:.1f}/100[/{score_color}]\n"
        f"评级: [{score_color}]{rating}[/{score_color}]",
        title="[bold cyan]分析报告[/bold cyan]",
        border_style=score_color
    ))

    # 各维度得分
    table = Table(title="各维度得分", box=box.ROUNDED)
    table.add_column("维度", style="cyan")
    table.add_column("得分", justify="right", style="yellow")
    table.add_column("满分", justify="right")
    table.add_column("得分率", style="green")

    for category in result.category_scores:
        table.add_row(
            category.name,
            f"{category.score:.1f}",
            f"{category.max_score:.1f}",
            f"{category.score_percentage:.1f}%"
        )

    console.print(table)

    # 投资建议
    if hasattr(result, 'recommendation') and result.recommendation:
        console.print("\n[bold blue]💡 投资建议:[/bold blue]")
        console.print(f"  {result.recommendation}")

    console.print()


def print_analyze_comparison(results):
    """打印分析对比"""
    console.print("\n[bold cyan]═══ 对比分析 ═══[/bold cyan]\n")

    table = Table(box=box.ROUNDED)
    table.add_column("股票", style="cyan")
    table.add_column("总分", justify="right", style="yellow")
    table.add_column("评级", justify="center", style="green")

    # 按得分排序
    sorted_results = sorted(results, key=lambda x: x['result'].total_score, reverse=True)

    for item in sorted_results:
        score_color = "green" if item['result'].total_score >= 80 else "yellow" if item['result'].total_score >= 60 else "red"
        rating = get_rating_from_score(item['result'].total_score)
        table.add_row(
            f"{item['name']} ({item['code']})",
            f"[{score_color}]{item['result'].total_score:.1f}[/{score_color}]",
            f"[{score_color}]{rating}[/{score_color}]"
        )

    console.print(table)
    console.print()


def print_screen_summary(results):
    """打印筛选汇总"""
    console.print("\n[bold cyan]═══ 筛选汇总 ═══[/bold cyan]\n")

    passed = [r for r in results if r['result'].passed]
    failed = [r for r in results if not r['result'].passed]

    table = Table(box=box.ROUNDED)
    table.add_column("股票", style="cyan")
    table.add_column("结果", justify="center")
    table.add_column("通过率", justify="right", style="yellow")

    for item in results:
        result = item['result']
        status_color = "green" if result.passed else "red"
        table.add_row(
            f"{item['name']} ({item['code']})",
            f"[{status_color}]{result.result_type.upper()}[/{status_color}]",
            f"{result.total_pass_rate:.1%}"
        )

    console.print(table)

    console.print(f"\n[bold]统计:[/bold]")
    console.print(f"  通过: [green]{len(passed)}[/green]")
    console.print(f"  未通过: [red]{len(failed)}[/red]")
    console.print()


def print_stock_info_from_db(stock, session):
    """从数据库打印股票信息"""
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("字段", style="cyan", width=15)
    table.add_column("值", style="green")

    table.add_row("股票代码", stock.code)
    table.add_row("股票名称", stock.name)
    table.add_row("市场", stock.market)
    table.add_row("交易所", stock.exchange or "N/A")
    table.add_row("行业", stock.industry or "N/A")

    console.print(table)

    # 显示财务数据摘要
    metrics_count = session.query(FinancialMetric).filter_by(stock_id=stock.id).count()
    if metrics_count > 0:
        console.print(f"\n[bold]财务数据:[/bold] {metrics_count} 条记录")

        latest_metric = (
            session.query(FinancialMetric)
            .filter_by(stock_id=stock.id)
            .order_by(FinancialMetric.report_date.desc())
            .first()
        )

        if latest_metric:
            console.print(f"最新数据日期: {latest_metric.report_date}")


def print_stock_info_from_source(stock_code):
    """从数据源打印股票信息"""
    source = MockDataSource()
    stock_info = source.get_stock_info(stock_code)

    if stock_info:
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("字段", style="cyan", width=15)
        table.add_column("值", style="green")

        for key, value in stock_info.items():
            table.add_row(key, str(value))

        console.print(table)
        console.print(f"\n[yellow]提示: 使用 'stock-analyzer update-data {stock_code}' 保存到数据库[/yellow]")
    else:
        console.print(f"[red]未找到股票 {stock_code}[/red]")


if __name__ == '__main__':
    cli()
