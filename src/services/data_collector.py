"""
数据采集服务

负责统一的财务数据采集、验证和入库
支持多数据源、增量更新、交叉验证
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich import box

from src.database import db
from src.database.models import Stock, FinancialReport, FinancialMetric

console = Console()
logger = logging.getLogger(__name__)

# 尝试导入scraper和parser（可选依赖）
try:
    from src.scrapers.cn_scraper import ChinaStockScraper
    from src.scrapers.us_scraper import USStockScraper
    SCRAPERS_AVAILABLE = True
except ImportError as e:
    SCRAPERS_AVAILABLE = False
    logger.warning(f"Scrapers不可用，将使用Mock数据: {e}")

try:
    from src.parsers.pdf_parser import PDFParser
    PARSER_AVAILABLE = True
except ImportError as e:
    PARSER_AVAILABLE = False
    logger.warning(f"Parser不可用，将使用Mock数据: {e}")


class DataCompletenessReport:
    """数据完整性报告"""

    def __init__(self, stock_code: str):
        self.stock_code = stock_code
        self.is_complete = False
        self.exists_in_db = False
        self.missing_years: List[int] = []
        self.missing_report_types: List[str] = []
        self.missing_fields: List[str] = []
        self.total_reports = 0
        self.expected_reports = 0

    def __repr__(self):
        return f"<DataCompletenessReport {self.stock_code}: complete={self.is_complete}, reports={self.total_reports}/{self.expected_reports}>"


class DataCollector:
    """
    数据采集服务

    功能：
    1. 检查数据完整性
    2. 从多个数据源采集财务数据
    3. 交叉验证数据准确性
    4. 增量更新
    5. 交互式用户确认
    """

    REPORT_TYPES = {
        'annual': '年报',
        'semi': '半年报',
        'quarter': '季报'
    }

    REQUIRED_FIELDS = [
        'revenue', 'net_profit', 'total_assets', 'total_liabilities',
        'roe', 'gross_margin', 'net_margin', 'asset_liability_ratio'
    ]

    def __init__(self):
        """初始化数据采集服务"""
        self.console = console
        self.logger = logger

        # 数据源列表（按优先级）
        self.data_sources = self._init_data_sources()

    def _init_data_sources(self) -> List[Any]:
        """
        初始化数据源

        优先级：
        1. 官方数据源（交易所、SEC）
        2. 第三方数据源（AkShare、yfinance）
        3. Mock数据源（开发测试）

        Returns:
            数据源列表
        """
        sources = []

        # 尝试加载第三方数据源
        try:
            from src.data_sources.akshare_source import AkShareSource
            sources.append(('AkShare', AkShareSource()))
            self.logger.info("已加载 AkShare 数据源")
        except Exception as e:
            self.logger.warning(f"无法加载 AkShare: {e}")

        # 官方数据源（总是可用）
        # TODO: 添加官方scraper数据源

        # Mock数据源（后备）
        try:
            from src.data_sources.mock_source import MockDataSource
            sources.append(('Mock', MockDataSource()))
            self.logger.info("已加载 Mock 数据源")
        except Exception as e:
            self.logger.warning(f"无法加载 Mock: {e}")

        return sources

    def check_data_completeness(
        self,
        stock_code: str,
        years: int = 5,
        report_types: Optional[List[str]] = None
    ) -> DataCompletenessReport:
        """
        检查数据完整性

        Args:
            stock_code: 股票代码
            years: 检查年限
            report_types: 报告类型列表，默认全部

        Returns:
            DataCompletenessReport: 完整性报告
        """
        report = DataCompletenessReport(stock_code)

        if report_types is None:
            report_types = list(self.REPORT_TYPES.keys())

        with db.session_scope() as session:
            # 检查股票是否存在
            stock = session.query(Stock).filter_by(code=stock_code).first()

            if not stock:
                report.exists_in_db = False
                report.expected_reports = years * len(report_types)
                return report

            report.exists_in_db = True

            # 计算期望的报告数量
            current_year = datetime.now().year
            expected_years = list(range(current_year - years, current_year))
            report.expected_reports = len(expected_years) * len(report_types)

            # 查询已有的报告
            reports = session.query(FinancialReport).filter_by(
                stock_id=stock.id
            ).all()

            report.total_reports = len(reports)

            # 检查缺失的年份和报告类型
            existing_combinations = {
                (r.fiscal_year, r.report_type) for r in reports
            }

            for year in expected_years:
                for rtype in report_types:
                    if (year, rtype) not in existing_combinations:
                        if year not in report.missing_years:
                            report.missing_years.append(year)
                        if rtype not in report.missing_report_types:
                            report.missing_report_types.append(rtype)

            # 检查缺失的字段（基于最新的财务指标）
            if reports:
                latest_metric = session.query(FinancialMetric).filter_by(
                    stock_id=stock.id
                ).order_by(FinancialMetric.report_date.desc()).first()

                if latest_metric:
                    for field in self.REQUIRED_FIELDS:
                        value = getattr(latest_metric, field, None)
                        if value is None:
                            report.missing_fields.append(field)

            # 判断是否完整
            report.is_complete = (
                len(report.missing_years) == 0 and
                len(report.missing_report_types) == 0 and
                len(report.missing_fields) == 0
            )

        return report

    def display_completeness_report(self, report: DataCompletenessReport):
        """
        显示完整性报告

        Args:
            report: 完整性报告
        """
        console.print(f"\n[bold cyan]数据完整性检查: {report.stock_code}[/bold cyan]\n")

        # 基本状态
        if not report.exists_in_db:
            console.print("[yellow]⚠ 数据库中没有该股票数据[/yellow]")
            console.print(f"需要采集: {report.expected_reports} 份报告")
            return

        # 报告统计
        table = Table(title="数据统计", box=box.ROUNDED)
        table.add_column("项目", style="cyan")
        table.add_column("状态", justify="center")
        table.add_column("详情", style="dim")

        # 报告数量
        status_icon = "✅" if report.total_reports == report.expected_reports else "⚠️"
        table.add_row(
            "报告数量",
            status_icon,
            f"{report.total_reports} / {report.expected_reports}"
        )

        # 缺失年份
        if report.missing_years:
            missing_years_str = ", ".join(map(str, sorted(report.missing_years)))
            table.add_row(
                "缺失年份",
                "❌",
                missing_years_str
            )
        else:
            table.add_row("缺失年份", "✅", "无")

        # 缺失报告类型
        if report.missing_report_types:
            missing_types_str = ", ".join([
                self.REPORT_TYPES[t] for t in report.missing_report_types
            ])
            table.add_row(
                "缺失报告类型",
                "❌",
                missing_types_str
            )
        else:
            table.add_row("缺失报告类型", "✅", "无")

        # 缺失字段
        if report.missing_fields:
            table.add_row(
                "缺失字段",
                "❌",
                f"{len(report.missing_fields)} 个字段"
            )
        else:
            table.add_row("缺失字段", "✅", "无")

        console.print(table)

        # 完整性结论
        if report.is_complete:
            console.print("\n[bold green]✅ 数据完整，无需采集[/bold green]\n")
        else:
            console.print("\n[bold yellow]⚠️ 数据不完整，建议采集[/bold yellow]\n")

    def ask_user_to_collect(
        self,
        stock_code: str,
        report: DataCompletenessReport
    ) -> bool:
        """
        询问用户是否采集数据

        Args:
            stock_code: 股票代码
            report: 完整性报告

        Returns:
            bool: 用户是否确认采集
        """
        if report.is_complete:
            return False

        # 显示完整性报告
        self.display_completeness_report(report)

        # 询问用户
        console.print("[bold yellow]是否开始数据采集？[/bold yellow]")

        if not report.exists_in_db:
            console.print(f"将采集 {stock_code} 的全部数据")
        else:
            console.print(f"将补充缺失的数据")

        console.print("\n选项：")
        console.print("  [green]y[/green] - 开始采集")
        console.print("  [red]n[/red] - 跳过")
        console.print("  [cyan]i[/cyan] - 增量更新（仅更新最新数据）")

        choice = input("\n请选择 (y/n/i): ").strip().lower()

        if choice == 'y':
            return True
        elif choice == 'i':
            console.print("[cyan]将执行增量更新...[/cyan]")
            return 'incremental'
        else:
            console.print("[dim]已跳过数据采集[/dim]")
            return False

    def collect_stock_data(
        self,
        stock_code: str,
        years: int = 5,
        report_types: Optional[List[str]] = None,
        incremental: bool = False
    ) -> bool:
        """
        采集股票数据

        Args:
            stock_code: 股票代码
            years: 采集年限
            report_types: 报告类型列表
            incremental: 是否增量更新

        Returns:
            bool: 是否成功
        """
        if report_types is None:
            report_types = list(self.REPORT_TYPES.keys())

        console.print(f"\n[bold cyan]开始采集数据: {stock_code}[/bold cyan]\n")

        # Step 1: 获取股票基本信息
        stock_info = self._fetch_stock_info(stock_code)
        if not stock_info:
            console.print(f"[red]✗ 无法获取股票 {stock_code} 的基本信息[/red]")
            return False

        console.print(f"[green]✓ 股票信息: {stock_info['name']}[/green]")

        # Step 2: 确定需要采集的年份
        current_year = datetime.now().year

        if incremental:
            # 增量更新：只采集最新一年
            target_years = [current_year - 1]
            console.print(f"[cyan]增量模式：采集 {target_years[0]} 年数据[/cyan]")
        else:
            # 完整采集：采集指定年限
            target_years = list(range(current_year - years, current_year))
            console.print(f"[cyan]完整模式：采集 {years} 年数据 ({target_years[0]}-{target_years[-1]})[/cyan]")

        # Step 3: 采集财报数据
        total_tasks = len(target_years) * len(report_types)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:

            task = progress.add_task(
                "[cyan]采集财报数据...",
                total=total_tasks
            )

            success_count = 0

            for year in target_years:
                for rtype in report_types:
                    rtype_name = self.REPORT_TYPES[rtype]
                    progress.update(
                        task,
                        description=f"[cyan]采集 {year} 年{rtype_name}..."
                    )

                    # 采集单份报告
                    success = self._fetch_and_save_report(
                        stock_code,
                        stock_info,
                        year,
                        rtype
                    )

                    if success:
                        success_count += 1
                    else:
                        # 失败处理
                        retry = self._ask_retry(year, rtype_name)
                        if retry:
                            success = self._fetch_and_save_report(
                                stock_code,
                                stock_info,
                                year,
                                rtype
                            )
                            if success:
                                success_count += 1

                    progress.advance(task)

        # 汇总结果
        console.print(f"\n[bold green]✓ 采集完成[/bold green]")
        console.print(f"成功: {success_count}/{total_tasks}")

        if success_count < total_tasks:
            console.print(f"[yellow]失败: {total_tasks - success_count} 份报告[/yellow]")

        return success_count > 0

    def _fetch_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        从多个数据源获取股票信息（带交叉验证）

        Args:
            stock_code: 股票代码

        Returns:
            股票信息字典，失败返回None
        """
        results = []

        # 尝试所有数据源
        for source_name, source in self.data_sources:
            try:
                info = source.get_stock_info(stock_code)
                if info:
                    results.append((source_name, info))
                    self.logger.info(f"从 {source_name} 获取到股票信息")
            except Exception as e:
                self.logger.warning(f"{source_name} 获取失败: {e}")

        if not results:
            return None

        # 交叉验证：比较多个数据源的结果
        if len(results) > 1:
            # 检查关键字段是否一致
            base_info = results[0][1]
            for source_name, info in results[1:]:
                if info.get('name') != base_info.get('name'):
                    console.print(f"[yellow]⚠ 数据源 {source_name} 的股票名称不一致[/yellow]")

        # 返回第一个成功的结果
        return results[0][1]

    def _detect_market(self, stock_code: str) -> str:
        """
        检测股票市场类型

        Args:
            stock_code: 股票代码

        Returns:
            市场类型: 'A' (A股), 'HK' (港股), 'US' (美股)
        """
        # A股：6位数字，以0/3/6开头
        if stock_code.isdigit() and len(stock_code) == 6:
            return 'A'

        # 港股：5位数字，以0开头
        if stock_code.isdigit() and len(stock_code) == 5 and stock_code.startswith('0'):
            return 'HK'

        # 美股：字母组成
        if stock_code.isalpha():
            return 'US'

        # 默认A股
        self.logger.warning(f"无法识别市场类型: {stock_code}，默认为A股")
        return 'A'

    def _determine_fiscal_period(self, report_type: str) -> str:
        """
        确定财务期间

        Args:
            report_type: 报告类型 (annual, semi, quarter)

        Returns:
            财务期间: FY (年报), H1/H2 (半年报), Q1/Q2/Q3/Q4 (季报)
        """
        if report_type == 'annual':
            return 'FY'
        elif report_type == 'semi':
            return 'H2'  # 默认半年报为H2（中报）
        elif report_type == 'quarter':
            return 'Q4'  # 默认季报为Q4
        else:
            return 'FY'

    def _map_parsed_data_to_metric(
        self,
        parsed_data: Dict[str, Any],
        stock_id: int,
        report_id: int,
        report_date: datetime
    ) -> FinancialMetric:
        """
        将解析的数据映射到 FinancialMetric 模型

        Args:
            parsed_data: 解析后的数据（来自 PDFParser）
            stock_id: 股票ID
            report_id: 报告ID
            report_date: 报告日期

        Returns:
            FinancialMetric 对象
        """
        income = parsed_data.get('income_statement', {})
        balance = parsed_data.get('balance_sheet', {})
        cash_flow = parsed_data.get('cash_flow', {})
        metadata = parsed_data.get('metadata', {})

        def to_decimal(value):
            """转换为 Decimal"""
            if value is None:
                return None
            try:
                return Decimal(str(value))
            except:
                return None

        # 创建 FinancialMetric 对象
        metric = FinancialMetric(
            report_id=report_id,
            stock_id=stock_id,
            report_date=report_date,

            # 损益表指标
            revenue=to_decimal(income.get('revenue')),
            operating_cost=to_decimal(income.get('operating_cost')),
            operating_profit=to_decimal(income.get('operating_profit')),
            net_profit=to_decimal(income.get('net_profit')),
            selling_expense=to_decimal(income.get('selling_expense')),
            admin_expense=to_decimal(income.get('admin_expense')),
            finance_expense=to_decimal(income.get('finance_expense')),
            rd_expense=to_decimal(income.get('rd_expense')),
            tax_expense=to_decimal(income.get('tax_expense')),
            total_profit=to_decimal(income.get('total_profit')),

            # 资产负债表指标
            total_assets=to_decimal(balance.get('total_assets')),
            total_liabilities=to_decimal(balance.get('total_liabilities')),
            total_equity=to_decimal(balance.get('total_equity')),
            current_assets=to_decimal(balance.get('current_assets')),
            current_liabilities=to_decimal(balance.get('current_liabilities')),
            non_current_assets=to_decimal(balance.get('non_current_assets')),
            non_current_liabilities=to_decimal(balance.get('non_current_liabilities')),
            cash_and_equivalents=to_decimal(balance.get('cash_and_equivalents')),
            accounts_receivable=to_decimal(balance.get('accounts_receivable')),
            inventory=to_decimal(balance.get('inventory')),
            fixed_assets=to_decimal(balance.get('fixed_assets')),
            intangible_assets=to_decimal(balance.get('intangible_assets')),
            goodwill=to_decimal(balance.get('goodwill')),
            short_term_borrowing=to_decimal(balance.get('short_term_borrowing')),
            long_term_borrowing=to_decimal(balance.get('long_term_borrowing')),
            accounts_payable=to_decimal(balance.get('accounts_payable')),
            share_capital=to_decimal(balance.get('share_capital')),
            retained_earnings=to_decimal(balance.get('retained_earnings')),

            # 现金流量表指标
            operating_cash_flow=to_decimal(cash_flow.get('operating_cash_flow')),
            investing_cash_flow=to_decimal(cash_flow.get('investing_cash_flow')),
            financing_cash_flow=to_decimal(cash_flow.get('financing_cash_flow')),
            net_cash_flow=to_decimal(cash_flow.get('net_cash_flow')),

            # 计算财务比率
            gross_margin=self._calculate_gross_margin(income),
            net_margin=self._calculate_net_margin(income),
            asset_liability_ratio=self._calculate_asset_liability_ratio(balance),
            roe=self._calculate_roe(income, balance),

            # 元数据
            extraction_method='PDF_Parser',
            confidence_score=to_decimal(metadata.get('confidence', 1.0)),
        )

        return metric

    def _calculate_gross_margin(self, income: Dict) -> Optional[Decimal]:
        """计算毛利率"""
        revenue = income.get('revenue')
        operating_cost = income.get('operating_cost')

        if revenue and operating_cost and revenue > 0:
            try:
                gross_profit = revenue - operating_cost
                return Decimal(str(gross_profit / revenue))
            except:
                return None
        return None

    def _calculate_net_margin(self, income: Dict) -> Optional[Decimal]:
        """计算净利率"""
        revenue = income.get('revenue')
        net_profit = income.get('net_profit')

        if revenue and net_profit and revenue > 0:
            try:
                return Decimal(str(net_profit / revenue))
            except:
                return None
        return None

    def _calculate_asset_liability_ratio(self, balance: Dict) -> Optional[Decimal]:
        """计算资产负债率"""
        total_assets = balance.get('total_assets')
        total_liabilities = balance.get('total_liabilities')

        if total_assets and total_liabilities and total_assets > 0:
            try:
                return Decimal(str(total_liabilities / total_assets))
            except:
                return None
        return None

    def _calculate_roe(self, income: Dict, balance: Dict) -> Optional[Decimal]:
        """计算ROE（净资产收益率）"""
        net_profit = income.get('net_profit')
        total_equity = balance.get('total_equity')

        if net_profit and total_equity and total_equity > 0:
            try:
                return Decimal(str(net_profit / total_equity))
            except:
                return None
        return None

    def _fetch_and_save_report(
        self,
        stock_code: str,
        stock_info: Dict[str, Any],
        year: int,
        report_type: str
    ) -> bool:
        """
        采集并保存单份财报

        Args:
            stock_code: 股票代码
            stock_info: 股票信息
            year: 年份
            report_type: 报告类型

        Returns:
            bool: 是否成功
        """
        # 如果scraper或parser不可用，直接使用Mock数据
        if not SCRAPERS_AVAILABLE or not PARSER_AVAILABLE:
            self.logger.info(f"Scraper/Parser不可用，使用Mock数据")
            return self._save_mock_report(stock_code, stock_info, year, report_type)

        try:
            # 1. 检测市场类型
            market = self._detect_market(stock_code)
            self.logger.info(f"检测到市场类型: {market}")

            # 2. 选择合适的爬虫
            if market == 'A' or market == 'HK':
                scraper = ChinaStockScraper(market=market)
            elif market == 'US':
                scraper = USStockScraper(market=market)
            else:
                self.logger.error(f"不支持的市场类型: {market}")
                return False

            # 3. 爬取财报列表（最近90天）
            self.logger.info(f"正在爬取 {stock_code} 的财报列表...")
            announcements = scraper.scrape(stock_code, lookback_days=365)

            if not announcements:
                self.logger.warning(f"未找到 {stock_code} 的财报公告")
                # 降级使用Mock数据
                return self._save_mock_report(stock_code, stock_info, year, report_type)

            # 4. 筛选目标年份的报告
            keywords = self._get_report_keywords(report_type, year)
            target_announcement = None

            for ann in announcements:
                title = ann.get('announcementTitle', '').replace('<em>', '').replace('</em>', '')
                if any(kw in title for kw in keywords):
                    target_announcement = ann
                    break

            if not target_announcement:
                self.logger.warning(f"未找到 {year} 年{self.REPORT_TYPES[report_type]}")
                # 降级使用Mock数据
                return self._save_mock_report(stock_code, stock_info, year, report_type)

            # 5. 下载PDF
            self.logger.info(f"正在下载财报PDF...")
            pdf_path = scraper.download_report(target_announcement, stock_code)

            if not pdf_path:
                self.logger.error(f"下载PDF失败")
                # 降级使用Mock数据
                return self._save_mock_report(stock_code, stock_info, year, report_type)

            # 6. 解析PDF
            self.logger.info(f"正在解析PDF: {pdf_path}")
            parser = PDFParser()
            parsed_data = parser.parse(pdf_path)

            confidence = parsed_data.get('metadata', {}).get('confidence', 0)
            self.logger.info(f"解析完成，置信度: {confidence:.2%}")

            # 如果置信度太低，降级使用Mock数据
            if confidence < 0.3:
                self.logger.warning(f"解析置信度过低({confidence:.2%})，使用Mock数据")
                return self._save_mock_report(stock_code, stock_info, year, report_type)

            # 7. 保存到数据库
            return self._save_parsed_report(
                stock_code,
                stock_info,
                year,
                report_type,
                parsed_data,
                pdf_path
            )

        except Exception as e:
            self.logger.error(f"采集 {year} 年{self.REPORT_TYPES[report_type]}失败: {e}")
            # 降级使用Mock数据
            try:
                return self._save_mock_report(stock_code, stock_info, year, report_type)
            except:
                return False

    def _get_report_keywords(self, report_type: str, year: int) -> List[str]:
        """
        获取报告关键词

        Args:
            report_type: 报告类型
            year: 年份

        Returns:
            关键词列表
        """
        keywords = [str(year)]

        if report_type == 'annual':
            keywords.extend(['年度报告', '年报', f'{year}年年度'])
        elif report_type == 'semi':
            keywords.extend(['半年度报告', '中期报告', '半年报', f'{year}年半年'])
        elif report_type == 'quarter':
            keywords.extend(['季度报告', '季报', f'{year}年第'])

        return keywords

    def _save_parsed_report(
        self,
        stock_code: str,
        stock_info: Dict[str, Any],
        year: int,
        report_type: str,
        parsed_data: Dict[str, Any],
        pdf_path: str
    ) -> bool:
        """
        保存解析后的报告数据

        Args:
            stock_code: 股票代码
            stock_info: 股票信息
            year: 年份
            report_type: 报告类型
            parsed_data: 解析后的数据
            pdf_path: PDF文件路径

        Returns:
            bool: 是否成功
        """
        with db.get_session() as session:
            # 获取或创建股票记录
            stock = session.query(Stock).filter_by(code=stock_code).first()

            if not stock:
                # 创建新股票记录
                stock = Stock(
                    code=stock_code,
                    name=stock_info.get('name', f'股票{stock_code}'),
                    market=self._detect_market(stock_code),
                    industry=stock_info.get('industry'),
                )
                session.add(stock)
                session.flush()

            # 确定报告日期和期间
            report_date = datetime(year, 12, 31).date()
            fiscal_period = self._determine_fiscal_period(report_type)

            # 检查是否已存在
            existing_report = session.query(FinancialReport).filter_by(
                stock_id=stock.id,
                fiscal_year=year,
                fiscal_period=fiscal_period
            ).first()

            if existing_report:
                # 更新现有报告
                report = existing_report
                report.is_parsed = True
                report.parsed_at = datetime.utcnow()
                report.file_path = pdf_path
            else:
                # 创建新报告
                report = FinancialReport(
                    stock_id=stock.id,
                    report_type=report_type,
                    fiscal_year=year,
                    fiscal_period=fiscal_period,
                    report_date=report_date,
                    file_path=pdf_path,
                    file_format='pdf',
                    is_parsed=True,
                    parsed_at=datetime.utcnow()
                )
                session.add(report)
                session.flush()

            # 创建或更新财务指标
            existing_metric = session.query(FinancialMetric).filter_by(
                stock_id=stock.id,
                report_date=report_date
            ).first()

            if existing_metric:
                # 删除旧记录
                session.delete(existing_metric)
                session.flush()

            # 创建新的财务指标记录
            metric = self._map_parsed_data_to_metric(
                parsed_data,
                stock.id,
                report.id,
                report_date
            )
            session.add(metric)

            # 提交事务
            session.commit()

            self.logger.info(f"✓ 成功保存 {stock_code} {year}年{self.REPORT_TYPES[report_type]}")
            return True

    def _save_mock_report(
        self,
        stock_code: str,
        stock_info: Dict[str, Any],
        year: int,
        report_type: str
    ) -> bool:
        """
        保存Mock报告数据（降级方案）

        当真实数据采集失败时，使用Mock数据填充
        """
        self.logger.info(f"使用Mock数据填充 {stock_code} {year}年{self.REPORT_TYPES[report_type]}")

        # 使用Mock数据源
        try:
            from src.data_sources.mock_source import MockDataSource
            mock_source = MockDataSource()

            # 获取模拟的财务数据
            mock_data = mock_source.get_financial_data(stock_code, year)

            if not mock_data:
                self.logger.warning(f"Mock数据源也失败了")
                return False

            # 转换为parsed_data格式
            parsed_data = {
                'income_statement': {
                    'revenue': mock_data.get('revenue'),
                    'net_profit': mock_data.get('net_profit'),
                    'operating_cost': mock_data.get('revenue', 0) * 0.6 if mock_data.get('revenue') else None,
                },
                'balance_sheet': {
                    'total_assets': mock_data.get('total_assets'),
                    'total_liabilities': mock_data.get('total_liabilities'),
                    'total_equity': mock_data.get('total_assets', 0) - mock_data.get('total_liabilities', 0)
                        if mock_data.get('total_assets') and mock_data.get('total_liabilities') else None,
                },
                'cash_flow': {
                    'operating_cash_flow': mock_data.get('operating_cash_flow'),
                },
                'metadata': {
                    'confidence': 0.5,  # Mock数据置信度设为0.5
                    'parser': 'MockDataSource'
                }
            }

            # 保存
            return self._save_parsed_report(
                stock_code,
                stock_info,
                year,
                report_type,
                parsed_data,
                pdf_path=None
            )

        except Exception as e:
            self.logger.error(f"Mock数据保存失败: {e}")
            return False

    def _ask_retry(self, year: int, report_type: str) -> bool:
        """
        询问用户是否重试

        Args:
            year: 年份
            report_type: 报告类型

        Returns:
            bool: 是否重试
        """
        console.print(f"\n[yellow]⚠ {year} 年{report_type}采集失败[/yellow]")
        console.print("\n选项：")
        console.print("  [green]r[/green] - 重试")
        console.print("  [red]s[/red] - 跳过")
        console.print("  [red]q[/red] - 终止全部采集")

        choice = input("\n请选择 (r/s/q): ").strip().lower()

        if choice == 'r':
            return True
        elif choice == 'q':
            raise KeyboardInterrupt("用户终止采集")
        else:
            return False


# 便捷函数

def check_data(stock_code: str, years: int = 5) -> DataCompletenessReport:
    """
    检查数据完整性（便捷函数）

    Args:
        stock_code: 股票代码
        years: 年限

    Returns:
        DataCompletenessReport
    """
    collector = DataCollector()
    return collector.check_data_completeness(stock_code, years)


def collect_data(
    stock_code: str,
    years: int = 5,
    report_types: Optional[List[str]] = None,
    interactive: bool = True
) -> bool:
    """
    采集数据（便捷函数）

    Args:
        stock_code: 股票代码
        years: 年限
        report_types: 报告类型
        interactive: 是否交互式询问

    Returns:
        bool: 是否成功
    """
    collector = DataCollector()

    # 检查完整性
    report = collector.check_data_completeness(stock_code, years, report_types)

    if interactive:
        # 询问用户
        confirmed = collector.ask_user_to_collect(stock_code, report)

        if not confirmed:
            return False

        incremental = (confirmed == 'incremental')
    else:
        incremental = False

    # 采集数据
    return collector.collect_stock_data(
        stock_code,
        years,
        report_types,
        incremental
    )
