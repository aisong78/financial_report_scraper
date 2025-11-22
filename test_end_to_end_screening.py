"""
端到端测试：股票代码 → 数据库查询 → 筛选分析

演示完整流程：
1. 输入股票代码
2. 从数据库获取最近5年数据
3. 执行筛选框架分析
4. 展示结果
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.database import db
from src.database.models import Stock, FinancialMetric, FinancialReport
from src.analyzers import load_screener

console = Console()


class StockScreeningService:
    """股票筛选服务"""

    def __init__(self):
        """初始化"""
        # 初始化数据库
        db.init_database()

    def screen_stock(self, stock_code: str, framework_name: str = "quality_stock_screener"):
        """
        筛选股票

        Args:
            stock_code: 股票代码
            framework_name: 筛选框架名称

        Returns:
            ScreeningResult or None
        """
        console.print(f"\n[bold cyan]开始筛选股票: {stock_code}[/bold cyan]\n")

        # 1. 查询股票基本信息
        with db.session_scope() as session:
            stock = session.query(Stock).filter_by(code=stock_code).first()

            if not stock:
                console.print(f"[bold red]错误: 未找到股票 {stock_code}[/bold red]")
                return None

            console.print(f"✓ 找到股票: {stock.name} ({stock.code}), 市场: {stock.market}")

            # 2. 获取财务数据（最近5年）
            console.print(f"\n[bold]正在获取财务数据...[/bold]")
            current_metrics, historical_metrics = self._get_financial_data(session, stock.id)

            if not current_metrics:
                console.print(f"[bold red]错误: 该股票没有财务数据[/bold red]")
                return None

            # 显示数据概览
            self._display_data_overview(current_metrics, historical_metrics)

            # 3. 加载筛选框架
            console.print(f"\n[bold]加载筛选框架: {framework_name}[/bold]")
            screener = load_screener(framework_name)

            # 4. 执行筛选
            console.print(f"\n[bold]执行筛选分析...[/bold]\n")
            result = screener.screen(
                current_metrics=current_metrics,
                historical_metrics=historical_metrics,
                industry=stock.industry
            )

            return result, stock

    def _get_financial_data(
        self,
        session,
        stock_id: int,
        years: int = 5
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        获取财务数据

        Args:
            session: 数据库会话
            stock_id: 股票ID
            years: 获取年数

        Returns:
            (current_metrics, historical_metrics)
        """
        # 获取最近N年的年报数据
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

        # 转换为字典格式
        def metric_to_dict(metric: FinancialMetric) -> Dict[str, Any]:
            """将FinancialMetric对象转换为字典"""
            return {
                # 基础指标
                'report_date': metric.report_date,
                'revenue': float(metric.revenue) if metric.revenue else None,
                'net_profit': float(metric.net_profit) if metric.net_profit else None,
                'gross_margin': float(metric.gross_margin) if metric.gross_margin else None,
                'net_margin': float(metric.net_margin) if metric.net_margin else None,
                'roe': float(metric.roe) if metric.roe else None,
                'roa': float(metric.roa) if metric.roa else None,

                # 增长率
                'revenue_growth_rate_yoy': float(metric.revenue_yoy) if metric.revenue_yoy else None,
                'revenue_growth_rate_qoq': float(metric.revenue_qoq) if metric.revenue_qoq else None,
                'profit_growth_rate_yoy': float(metric.net_profit_yoy) if metric.net_profit_yoy else None,
                'profit_growth_rate_qoq': float(metric.net_profit_qoq) if metric.net_profit_qoq else None,

                # 资产负债
                'total_assets': float(metric.total_assets) if metric.total_assets else None,
                'total_liabilities': float(metric.total_liabilities) if metric.total_liabilities else None,
                'total_equity': float(metric.total_equity) if metric.total_equity else None,
                'debt_to_asset_ratio': float(metric.asset_liability_ratio) if metric.asset_liability_ratio else None,
                'current_ratio': float(metric.current_ratio) if metric.current_ratio else None,

                # 现金流
                'operating_cash_flow': float(metric.operating_cash_flow) if metric.operating_cash_flow else None,
                'operating_cashflow_ratio': float(metric.ocf_to_net_profit) if metric.ocf_to_net_profit else None,

                # 估值
                'pe_ratio': float(metric.pe_ratio) if metric.pe_ratio else None,
                'pb_ratio': float(metric.pb_ratio) if metric.pb_ratio else None,
                'peg_ratio': float(metric.peg_ratio) if metric.peg_ratio else None,

                # 运营效率
                'asset_turnover': float(metric.asset_turnover) if metric.asset_turnover else None,

                # 分红（从extra_metrics中获取，如果有的话）
                'dividend_paid': metric.extra_metrics.get('dividend_paid', 0) if metric.extra_metrics else 0,
                'dividend_payout_ratio': metric.extra_metrics.get('dividend_payout_ratio', 0) if metric.extra_metrics else 0,
                'dividend_yield': metric.extra_metrics.get('dividend_yield', 0) if metric.extra_metrics else 0,

                # 市值（从extra_metrics中获取）
                'market_cap': metric.extra_metrics.get('market_cap', 0) if metric.extra_metrics else 0,

                # 风险控制（从extra_metrics中获取）
                'violations': metric.extra_metrics.get('violations', 0) if metric.extra_metrics else 0,
                'fraud': metric.extra_metrics.get('fraud', 0) if metric.extra_metrics else 0,
                'esg_rating': metric.extra_metrics.get('esg_rating', 'N/A') if metric.extra_metrics else 'N/A',
            }

        # 当前指标（最新一期）
        current_metrics = metric_to_dict(metrics_list[0])

        # 历史指标（倒序，最新在前）
        historical_metrics = [metric_to_dict(m) for m in metrics_list]

        return current_metrics, historical_metrics

    def _display_data_overview(
        self,
        current_metrics: Dict[str, Any],
        historical_metrics: List[Dict[str, Any]]
    ):
        """显示数据概览"""
        console.print(f"\n[bold green]✓ 获取到 {len(historical_metrics)} 年财务数据[/bold green]")

        # 创建数据表格
        table = Table(title="历史财务数据概览", box=box.ROUNDED)
        table.add_column("年份", style="cyan", justify="center")
        table.add_column("营收", justify="right")
        table.add_column("净利润", justify="right")
        table.add_column("ROE", justify="right")
        table.add_column("毛利率", justify="right")
        table.add_column("净利率", justify="right")

        for i, metrics in enumerate(historical_metrics[:5]):  # 显示最近5年
            year = metrics['report_date'].year if metrics.get('report_date') else 'N/A'
            revenue = f"{metrics.get('revenue', 0) / 1e8:.1f}亿" if metrics.get('revenue') else 'N/A'
            profit = f"{metrics.get('net_profit', 0) / 1e8:.1f}亿" if metrics.get('net_profit') else 'N/A'
            roe = f"{metrics.get('roe', 0) * 100:.1f}%" if metrics.get('roe') else 'N/A'
            gross_margin = f"{metrics.get('gross_margin', 0) * 100:.1f}%" if metrics.get('gross_margin') else 'N/A'
            net_margin = f"{metrics.get('net_margin', 0) * 100:.1f}%" if metrics.get('net_margin') else 'N/A'

            # 最新年份高亮
            style = "bold green" if i == 0 else ""

            table.add_row(
                str(year),
                revenue,
                profit,
                roe,
                gross_margin,
                net_margin,
                style=style
            )

        console.print(table)


def test_with_mock_data():
    """使用模拟数据测试（如果数据库为空）"""
    console.print("\n[bold yellow]数据库为空，使用模拟数据演示[/bold yellow]\n")

    # 模拟茅台数据
    current_metrics = {
        'roe': 0.28,
        'gross_margin': 0.91,
        'net_margin': 0.52,
        'revenue_growth_rate_qoq': 0.18,
        'profit_growth_rate_qoq': 0.16,
        'debt_to_asset_ratio': 0.20,
        'current_ratio': 2.8,
        'operating_cashflow_ratio': 1.3,
        'pe_ratio': 32,
        'pb_ratio': 8.5,
        'peg_ratio': 1.8,
        'market_cap': 280000000000,
        'dividend_paid': 30000000000,
        'dividend_payout_ratio': 0.72,
        'dividend_yield': 0.022,
        'violations': 0,
        'fraud': 0,
        'esg_rating': 'AA',
    }

    historical_metrics = [
        {
            'report_date': datetime(2023, 12, 31),
            'roe': 0.28, 'gross_margin': 0.91, 'net_profit': 52600000000,
            'dividend_paid': 30000000000, 'revenue': 120000000000
        },
        {
            'report_date': datetime(2022, 12, 31),
            'roe': 0.30, 'gross_margin': 0.92, 'net_profit': 52000000000,
            'dividend_paid': 29000000000, 'revenue': 115000000000
        },
        {
            'report_date': datetime(2021, 12, 31),
            'roe': 0.32, 'gross_margin': 0.91, 'net_profit': 46600000000,
            'dividend_paid': 24000000000, 'revenue': 105000000000
        },
        {
            'report_date': datetime(2020, 12, 31),
            'roe': 0.28, 'gross_margin': 0.91, 'net_profit': 40000000000,
            'dividend_paid': 20000000000, 'revenue': 95000000000
        },
        {
            'report_date': datetime(2019, 12, 31),
            'roe': 0.30, 'gross_margin': 0.90, 'net_profit': 35200000000,
            'dividend_paid': 17000000000, 'revenue': 85000000000
        },
    ]

    # 显示数据概览
    service = StockScreeningService()
    service._display_data_overview(current_metrics, historical_metrics)

    # 加载框架并筛选
    console.print(f"\n[bold]加载筛选框架并执行分析...[/bold]\n")
    screener = load_screener('quality_stock_screener')
    result = screener.screen(current_metrics, historical_metrics)

    # 创建模拟股票对象
    class MockStock:
        code = "600519"
        name = "贵州茅台"
        market = "A"

    return result, MockStock()


def main():
    """主函数"""
    console.print("""
[bold cyan]╔══════════════════════════════════════════════════════════╗
║          端到端筛选测试                                   ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]

测试流程：
1. 输入股票代码
2. 从数据库获取最近5年数据
3. 执行筛选框架分析
4. 展示详细结果
    """)

    # 创建服务
    service = StockScreeningService()

    # 测试股票代码
    test_codes = ["600519", "000858", "AAPL"]  # 茅台、五粮液、苹果

    console.print("[bold]提示：如果数据库中没有数据，将使用模拟数据演示[/bold]\n")

    # 尝试从数据库读取
    result = None
    stock = None

    for code in test_codes:
        result_data = service.screen_stock(code, "quality_stock_screener")
        if result_data:
            result, stock = result_data
            break

    # 如果数据库为空，使用模拟数据
    if not result:
        result, stock = test_with_mock_data()

    # 显示筛选结果（简化版）
    if result:
        from demo_screener import print_screening_result
        print_screening_result(result, stock.name)

    console.print("\n[bold green]✓ 测试完成！[/bold green]\n")
    console.print("说明：")
    console.print("  • 如果数据库有数据，会直接从数据库读取")
    console.print("  • 如果数据库为空，会使用模拟数据演示")
    console.print("  • 增长率（CAGR）会自动从历史数据计算")
    console.print("  • 连续N年的条件会检查历史数据\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[bold red]错误: {e}[/bold red]\n")
        import traceback
        traceback.print_exc()
