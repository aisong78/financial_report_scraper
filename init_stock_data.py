#!/usr/bin/env python3
"""
通用股票数据初始化工具

功能：
1. 获取股票基本信息（优先使用真实数据源）
2. 创建模拟财务数据（包含所有必要字段）
3. 支持批量初始化多只股票

使用示例：
    python init_stock_data.py 688005  # 初始化容百科技
    python init_stock_data.py 600519 000858  # 初始化多只股票
"""
import sys
from pathlib import Path
from datetime import date, datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich import box
from src.database import db
from src.database.models import Stock, FinancialReport, FinancialMetric

console = Console()


def get_data_source():
    """
    获取数据源（优先使用真实数据源）

    Returns:
        数据源实例
    """
    # 尝试导入并使用 AkShare
    try:
        from src.data_sources.akshare_source import AkShareSource
        console.print("[green]✓ 使用 AkShare 数据源（真实数据）[/green]")
        return AkShareSource()
    except ImportError as e:
        console.print(f"[yellow]⚠ AkShare 不可用: {e}[/yellow]")
        console.print("[yellow]使用 Mock 数据源（模拟数据）[/yellow]")
        from src.data_sources.mock_source import MockDataSource
        return MockDataSource()


def get_stock_info_with_fallback(source, stock_code: str) -> Optional[Dict[str, Any]]:
    """
    获取股票信息（带降级处理）

    Args:
        source: 数据源
        stock_code: 股票代码

    Returns:
        股票信息字典，如果失败则返回None
    """
    try:
        info = source.get_stock_info(stock_code)
        if info:
            return info
    except Exception as e:
        console.print(f"[yellow]⚠ 无法从数据源获取股票信息: {e}[/yellow]")

    # 降级：根据股票代码推测市场
    console.print("[yellow]使用推测的股票信息...[/yellow]")

    if stock_code.startswith('6'):
        market, exchange = 'A', 'SSE'
    elif stock_code.startswith('0') or stock_code.startswith('3'):
        market, exchange = 'A', 'SZSE'
    elif stock_code.startswith('688'):
        market, exchange = '科创板', 'SSE'
    elif stock_code.isdigit() and len(stock_code) == 5:
        market, exchange = 'HK', 'HKEX'
    else:
        market, exchange = 'US', 'NASDAQ'

    return {
        'code': stock_code,
        'name': f'股票{stock_code}',
        'market': market,
        'exchange': exchange,
        'industry': '未知'
    }


def create_mock_financial_data(
    stock_id: int,
    stock_code: str,
    industry: str,
    years: int = 5
) -> List[Dict[str, Any]]:
    """
    创建模拟财务数据（包含完整字段）

    Args:
        stock_id: 股票ID
        stock_code: 股票代码
        industry: 行业
        years: 年数

    Returns:
        模拟数据列表
    """
    current_year = datetime.now().year

    # 根据行业设置基础参数
    industry_params = {
        '白酒': {
            'base_revenue': 100000000000,  # 1000亿
            'base_profit': 40000000000,     # 400亿
            'gross_margin': 0.90,
            'net_margin': 0.40,
            'roe': 0.28,
            'asset_liability_ratio': 0.25,
            'growth_rate': 1.15  # 年增长15%
        },
        '电池': {
            'base_revenue': 10000000000,   # 100亿
            'base_profit': 500000000,      # 5亿
            'gross_margin': 0.15,
            'net_margin': 0.05,
            'roe': 0.10,
            'asset_liability_ratio': 0.60,
            'growth_rate': 1.25  # 年增长25%（高成长）
        },
        '科技': {
            'base_revenue': 5000000000,    # 50亿
            'base_profit': 800000000,      # 8亿
            'gross_margin': 0.55,
            'net_margin': 0.16,
            'roe': 0.18,
            'asset_liability_ratio': 0.35,
            'growth_rate': 1.30  # 年增长30%
        },
        '默认': {
            'base_revenue': 5000000000,    # 50亿
            'base_profit': 500000000,      # 5亿
            'gross_margin': 0.30,
            'net_margin': 0.10,
            'roe': 0.12,
            'asset_liability_ratio': 0.50,
            'growth_rate': 1.10  # 年增长10%
        }
    }

    params = industry_params.get(industry, industry_params['默认'])

    data_list = []
    for i in range(years):
        year = current_year - 1 - i  # 从去年开始往前
        growth_factor = params['growth_rate'] ** (years - 1 - i)

        revenue = params['base_revenue'] * growth_factor
        net_profit = params['base_profit'] * growth_factor
        total_equity = net_profit / params['roe']
        total_assets = total_equity / (1 - params['asset_liability_ratio'])
        total_liabilities = total_assets * params['asset_liability_ratio']

        data = {
            'year': year,
            'report_date': date(year, 12, 31),
            'revenue': revenue,
            'net_profit': net_profit,
            'gross_margin': params['gross_margin'],
            'net_margin': params['net_margin'],
            'roe': params['roe'],
            'roa': params['roe'] * (1 - params['asset_liability_ratio']),
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'asset_liability_ratio': params['asset_liability_ratio'],
            'current_ratio': 2.0,  # 流动比率
            'operating_cash_flow': net_profit * 1.1,  # 现金流略高于净利润
            'ocf_to_net_profit': 1.1,
            # 估值数据
            'pe_ratio': 25.0,
            'pb_ratio': 3.0,
            # 增长率（从第二年开始）
            'revenue_yoy': (params['growth_rate'] - 1) if i < years - 1 else None,
            'net_profit_yoy': (params['growth_rate'] - 1) if i < years - 1 else None,
        }

        data_list.append(data)

    return data_list


def init_stock(stock_code: str, source=None, years: int = 5) -> bool:
    """
    初始化单只股票数据

    Args:
        stock_code: 股票代码
        source: 数据源（可选）
        years: 创建几年的历史数据

    Returns:
        是否成功
    """
    console.print(f"\n[bold cyan]═══ 初始化股票: {stock_code} ═══[/bold cyan]\n")

    # 获取数据源
    if source is None:
        source = get_data_source()

    # 获取股票信息
    console.print("1️⃣  获取股票基本信息...")
    stock_info = get_stock_info_with_fallback(source, stock_code)

    if not stock_info:
        console.print(f"[bold red]✗ 无法获取股票信息: {stock_code}[/bold red]")
        return False

    console.print(f"[green]✓ 股票名称: {stock_info['name']}[/green]")
    console.print(f"[green]✓ 市场: {stock_info['market']} / {stock_info['exchange']}[/green]")
    console.print(f"[green]✓ 行业: {stock_info.get('industry', '未知')}[/green]")

    with db.session_scope() as session:
        # 2. 创建或更新股票记录
        console.print("\n2️⃣  创建股票记录...")
        stock = session.query(Stock).filter_by(code=stock_code).first()

        if not stock:
            stock = Stock(
                code=stock_info['code'],
                name=stock_info['name'],
                market=stock_info['market'],
                exchange=stock_info['exchange'],
                industry=stock_info.get('industry', '未知')
            )
            session.add(stock)
            console.print(f"[green]✓ 创建新股票记录[/green]")
        else:
            console.print(f"[yellow]○ 股票记录已存在，跳过[/yellow]")

        session.flush()  # 确保 stock.id 可用

        # 3. 创建模拟财务数据
        console.print(f"\n3️⃣  创建 {years} 年模拟财务数据...")

        mock_data = create_mock_financial_data(
            stock.id,
            stock_code,
            stock_info.get('industry', '未知'),
            years
        )

        created_count = 0
        for data in mock_data:
            year = data['year']

            # 检查是否已存在
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
                    report_date=data['report_date'],
                    publish_date=date(year + 1, 4, 20),
                    file_url=f"https://example.com/report/{year}"
                )
                session.add(report)
                session.flush()

                # 创建财务指标（包含完整字段）
                metric = FinancialMetric(
                    stock_id=stock.id,
                    report_id=report.id,
                    report_date=data['report_date'],
                    revenue=data['revenue'],
                    net_profit=data['net_profit'],
                    gross_margin=data['gross_margin'],
                    net_margin=data['net_margin'],
                    roe=data['roe'],
                    roa=data['roa'],
                    total_assets=data['total_assets'],
                    total_liabilities=data['total_liabilities'],
                    total_equity=data['total_equity'],
                    asset_liability_ratio=data['asset_liability_ratio'],
                    current_ratio=data['current_ratio'],
                    operating_cash_flow=data['operating_cash_flow'],
                    ocf_to_net_profit=data['ocf_to_net_profit'],
                    pe_ratio=data['pe_ratio'],
                    pb_ratio=data['pb_ratio'],
                    revenue_yoy=data.get('revenue_yoy'),
                    net_profit_yoy=data.get('net_profit_yoy'),
                )
                session.add(metric)
                console.print(f"  [green]✓ {year} 年[/green]")
                created_count += 1
            else:
                console.print(f"  [dim]○ {year} 年（已存在）[/dim]")

        if created_count > 0:
            console.print(f"\n[green]✓ 创建了 {created_count} 年的财务数据[/green]")
        else:
            console.print(f"\n[yellow]○ 所有数据已存在，无需创建[/yellow]")

    console.print(f"\n[bold green]✓ {stock_code} 初始化完成！[/bold green]")
    return True


def init_multiple_stocks(stock_codes: List[str], years: int = 5):
    """
    批量初始化多只股票

    Args:
        stock_codes: 股票代码列表
        years: 创建几年的历史数据
    """
    console.print(f"""
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          股票数据初始化工具                               ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]

准备初始化 {len(stock_codes)} 只股票的数据...
    """)

    # 初始化数据库
    console.print("[bold]初始化数据库...[/bold]")
    db.init_database()
    console.print()

    # 获取数据源
    source = get_data_source()
    console.print()

    # 批量初始化
    success_count = 0
    failed_codes = []

    for code in stock_codes:
        try:
            if init_stock(code, source, years):
                success_count += 1
        except Exception as e:
            console.print(f"[bold red]✗ {code} 初始化失败: {e}[/bold red]")
            failed_codes.append(code)

    # 显示汇总
    console.print(f"""
[bold cyan]═══ 初始化完成 ═══[/bold cyan]

成功: {success_count} / {len(stock_codes)}
失败: {len(failed_codes)}
    """)

    if failed_codes:
        console.print(f"[red]失败的股票代码: {', '.join(failed_codes)}[/red]")

    # 显示数据库统计
    with db.session_scope() as session:
        stock_count = session.query(Stock).count()
        report_count = session.query(FinancialReport).count()
        metric_count = session.query(FinancialMetric).count()

        table = Table(title="数据库统计", box=box.ROUNDED)
        table.add_column("类型", style="cyan")
        table.add_column("数量", justify="right", style="green")

        table.add_row("股票", str(stock_count))
        table.add_row("财务报告", str(report_count))
        table.add_row("财务指标", str(metric_count))

        console.print()
        console.print(table)

    console.print(f"""
[bold green]✓ 所有数据已就绪！[/bold green]

现在可以使用以下命令分析股票：

  [cyan]python stock_analyzer.py info {stock_codes[0]}[/cyan]
  [cyan]python stock_analyzer.py screen {stock_codes[0]}[/cyan]
  [cyan]python stock_analyzer.py analyze {stock_codes[0]}[/cyan]
    """)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        console.print("""
[bold cyan]股票数据初始化工具[/bold cyan]

使用方法：
  python init_stock_data.py <股票代码1> [股票代码2] ...

示例：
  python init_stock_data.py 688005              # 初始化容百科技
  python init_stock_data.py 600519 000858       # 初始化茅台和五粮液
  python init_stock_data.py AAPL MSFT GOOGL     # 初始化美股

功能：
  • 自动获取股票基本信息（优先使用真实数据源）
  • 创建5年模拟财务数据（包含完整的分析所需字段）
  • 支持批量初始化多只股票
        """)
        sys.exit(0)

    stock_codes = sys.argv[1:]
    init_multiple_stocks(stock_codes, years=5)


if __name__ == "__main__":
    main()
