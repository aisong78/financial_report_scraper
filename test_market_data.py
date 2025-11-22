"""
测试市场数据采集功能

演示如何使用市场数据服务获取并保存：
1. 历史市值数据
2. 分红数据
3. 估值指标
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
from src.database import db
from src.database.models import Stock

console = Console()


def test_akshare_availability():
    """测试 AkShare 是否可用"""
    console.print("\n[bold cyan]1. 测试 AkShare 可用性[/bold cyan]\n")

    try:
        import akshare as ak
        console.print("✓ AkShare 已安装")

        # 测试基本功能
        try:
            # 获取上证指数最新数据作为测试
            df = ak.stock_zh_index_daily(symbol="sh000001")
            if df is not None and not df.empty:
                console.print("✓ AkShare 网络连接正常")
                console.print(f"✓ 测试数据: 获取到上证指数 {len(df)} 条记录")
                return True
            else:
                console.print("[yellow]⚠ AkShare 返回空数据[/yellow]")
                return False
        except Exception as e:
            console.print(f"[yellow]⚠ AkShare 网络测试失败: {e}[/yellow]")
            return False

    except ImportError:
        console.print("[red]✗ AkShare 未安装[/red]")
        console.print("\n安装方法:")
        console.print("  pip install akshare")
        console.print("  或者")
        console.print("  pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple")
        return False


def test_get_stock_info(service: MarketDataService, stock_code: str):
    """测试获取股票基本信息"""
    console.print(f"\n[bold cyan]2. 测试获取股票信息: {stock_code}[/bold cyan]\n")

    stock_info = service.data_source.get_stock_info(stock_code)

    if stock_info:
        console.print("✓ 成功获取股票信息:")
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("字段", style="cyan")
        table.add_column("值", style="green")

        for key, value in stock_info.items():
            table.add_row(key, str(value))

        console.print(table)
        return True
    else:
        console.print("[red]✗ 获取股票信息失败[/red]")
        return False


def test_get_market_cap_history(service: MarketDataService, stock_code: str):
    """测试获取市值历史"""
    console.print(f"\n[bold cyan]3. 测试获取市值历史: {stock_code}[/bold cyan]\n")

    market_cap_data = service.data_source.get_market_cap_history(stock_code, years=5)

    if market_cap_data:
        console.print(f"✓ 成功获取 {len(market_cap_data)} 年市值数据:")

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
                f"{data['close']:.2f}",
                f"{market_cap_billion:.2f}亿"
            )

        console.print(table)
        return True
    else:
        console.print("[yellow]⚠ 未获取到市值数据[/yellow]")
        return False


def test_get_dividend_data(service: MarketDataService, stock_code: str):
    """测试获取分红数据"""
    console.print(f"\n[bold cyan]4. 测试获取分红数据: {stock_code}[/bold cyan]\n")

    from datetime import datetime
    current_year = datetime.now().year
    dividend_data = service.data_source.get_dividend_data(
        stock_code,
        start_year=current_year - 5,
        end_year=current_year
    )

    if dividend_data:
        console.print(f"✓ 成功获取 {len(dividend_data)} 年分红数据:")

        table = Table(title="分红历史", box=box.ROUNDED)
        table.add_column("年份", justify="center", style="cyan")
        table.add_column("每股分红", justify="right", style="green")
        table.add_column("送股比例", justify="right", style="yellow")
        table.add_column("除权日", justify="center")

        for data in dividend_data:
            table.add_row(
                str(data['year']),
                f"{data['dividend_per_share']:.4f}元" if data['dividend_per_share'] else "N/A",
                f"{data.get('bonus_share_ratio', 0):.2f}%" if data.get('bonus_share_ratio') else "N/A",
                str(data.get('ex_dividend_date', 'N/A'))
            )

        console.print(table)
        return True
    else:
        console.print("[yellow]⚠ 未获取到分红数据[/yellow]")
        return False


def test_enrich_database(service: MarketDataService, stock_code: str):
    """测试补充数据库数据"""
    console.print(f"\n[bold cyan]5. 测试补充数据库: {stock_code}[/bold cyan]\n")

    # 首先确保数据库中有这只股票
    with db.session_scope() as session:
        stock = session.query(Stock).filter_by(code=stock_code).first()

        if not stock:
            console.print(f"[yellow]⚠ 数据库中没有股票 {stock_code}，创建中...[/yellow]")

            # 获取股票信息
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
                console.print(f"✓ 已创建股票: {stock.name} ({stock.code})")
            else:
                console.print("[red]✗ 无法获取股票信息[/red]")
                return False

    # 补充市场数据
    success = service.enrich_financial_metrics(stock_code, years=5)

    if success:
        console.print("\n[bold green]✓ 数据库补充成功！[/bold green]")

        # 显示补充后的数据
        valuation_history = service.get_stock_valuation_history(stock_code, years=5)

        if valuation_history:
            console.print(f"\n数据库中的估值历史 ({len(valuation_history)} 年):")

            table = Table(box=box.ROUNDED)
            table.add_column("年份", justify="center", style="cyan")
            table.add_column("PE", justify="right", style="yellow")
            table.add_column("PB", justify="right", style="yellow")
            table.add_column("市值", justify="right", style="green")

            for data in valuation_history:
                pe = f"{data['pe_ratio']:.2f}" if data['pe_ratio'] else "N/A"
                pb = f"{data['pb_ratio']:.2f}" if data['pb_ratio'] else "N/A"
                mc = f"{data['market_cap'] / 1e8:.2f}亿" if data['market_cap'] else "N/A"

                table.add_row(str(data['year']), pe, pb, mc)

            console.print(table)

        return True
    else:
        console.print("[yellow]⚠ 数据库补充部分成功[/yellow]")
        return False


def main():
    """主函数"""
    console.print("""
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          市场数据采集测试                                 ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]

本测试将演示：
1. AkShare 数据源可用性检查
2. 获取股票基本信息
3. 获取历史市值数据
4. 获取分红数据
5. 补充数据库财务指标
    """)

    # 初始化数据库
    db.init_database()

    # 测试 AkShare
    if not test_akshare_availability():
        console.print("\n[bold red]请先安装 AkShare 再继续测试[/bold red]")
        return

    # 创建服务
    try:
        service = MarketDataService()
    except ImportError as e:
        console.print(f"\n[bold red]错误: {e}[/bold red]")
        return

    # 测试股票代码
    test_codes = ["600519", "000858"]  # 茅台、五粮液

    for stock_code in test_codes:
        console.print(f"\n{'=' * 60}")
        console.print(f"[bold]测试股票: {stock_code}[/bold]")
        console.print('=' * 60)

        # 逐个测试功能
        test_get_stock_info(service, stock_code)
        test_get_market_cap_history(service, stock_code)
        test_get_dividend_data(service, stock_code)

        # 如果用户想要补充数据库，可以取消下面的注释
        # test_enrich_database(service, stock_code)

    console.print("\n[bold green]✓ 测试完成！[/bold green]\n")
    console.print("说明：")
    console.print("  • 如果需要补充数据库，请取消 test_enrich_database() 的注释")
    console.print("  • AkShare 数据获取可能较慢，请耐心等待")
    console.print("  • 部分数据可能因网络或API限制而缺失\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]用户中断测试[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]错误: {e}[/bold red]\n")
        import traceback
        traceback.print_exc()
