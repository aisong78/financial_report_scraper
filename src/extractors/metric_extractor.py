"""
财务指标提取器

从解析结果中提取和计算46个财务指标（P0+P1）
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from ..database.db import session_scope
from ..database.models import FinancialMetric
from ..utils.logger import get_logger


class MetricExtractor:
    """财务指标提取器"""

    def __init__(self):
        """初始化"""
        self.logger = get_logger()

    def extract(self, parsed_data: Dict[str, Any], stock_id: int, report_date: datetime) -> Dict[str, Any]:
        """
        提取财务指标

        Args:
            parsed_data: 解析结果（来自 Parser）
            stock_id: 股票ID
            report_date: 报告日期

        Returns:
            指标字典（46个P0+P1指标）
        """
        metrics = {}

        # 1. 从三大报表提取原始数据
        income = parsed_data.get('income_statement', {})
        balance = parsed_data.get('balance_sheet', {})
        cashflow = parsed_data.get('cash_flow', {})

        # === P0指标（15个核心指标）===

        # 损益表核心指标
        metrics['revenue'] = income.get('revenue')
        metrics['net_profit'] = income.get('net_profit')
        metrics['operating_profit'] = income.get('operating_profit')
        metrics['eps'] = income.get('eps')  # 如果解析结果中有

        # 资产负债表核心指标
        metrics['total_assets'] = balance.get('total_assets')
        metrics['total_liabilities'] = balance.get('total_liabilities')
        metrics['total_equity'] = balance.get('total_equity')
        metrics['current_assets'] = balance.get('current_assets')
        metrics['current_liabilities'] = balance.get('current_liabilities')

        # 现金流核心指标
        metrics['operating_cash_flow'] = cashflow.get('operating_cash_flow')

        # 这些比率指标需要计算，稍后处理
        # revenue_yoy, net_profit_yoy, asset_liability_ratio, roe, gross_margin,
        # net_margin, pe_ratio, pb_ratio

        # === P1补充指标（31个）===

        # 损益表补充（9个）
        metrics['operating_cost'] = income.get('operating_cost')
        metrics['selling_expense'] = income.get('selling_expense')
        metrics['admin_expense'] = income.get('admin_expense')
        metrics['finance_expense'] = income.get('finance_expense')
        metrics['tax_expense'] = income.get('tax_expense')
        metrics['total_profit'] = income.get('total_profit')
        metrics['eps_diluted'] = income.get('eps_diluted')
        # ebitda_margin, bps 需要计算

        # 资产负债表补充（13个）
        metrics['non_current_assets'] = balance.get('non_current_assets')
        metrics['cash_and_equivalents'] = balance.get('cash_and_equivalents')
        metrics['accounts_receivable'] = balance.get('accounts_receivable')
        metrics['inventory'] = balance.get('inventory')
        metrics['fixed_assets'] = balance.get('fixed_assets')
        metrics['intangible_assets'] = balance.get('intangible_assets')
        metrics['goodwill'] = balance.get('goodwill')
        metrics['non_current_liabilities'] = balance.get('non_current_liabilities')
        metrics['short_term_borrowing'] = balance.get('short_term_borrowing')
        metrics['long_term_borrowing'] = balance.get('long_term_borrowing')
        metrics['accounts_payable'] = balance.get('accounts_payable')
        metrics['share_capital'] = balance.get('share_capital')
        metrics['retained_earnings'] = balance.get('retained_earnings')

        # 现金流补充（4个）
        metrics['investing_cash_flow'] = cashflow.get('investing_cash_flow')
        metrics['financing_cash_flow'] = cashflow.get('financing_cash_flow')
        metrics['net_cash_flow'] = cashflow.get('net_cash_flow')
        # fcf_per_share, fcf_to_revenue, ocf_to_net_profit 需要计算

        # 研发
        metrics['rd_expense'] = income.get('rd_expense')

        # 2. 计算衍生指标（比率、增长率等）
        metrics = self.calculate_ratios(metrics)

        # 3. 计算增长率（需要历史数据）
        metrics = self.calculate_growth(stock_id, report_date, metrics)

        # 4. 计算运营效率指标
        metrics = self.calculate_efficiency(metrics)

        return metrics

    def calculate_ratios(self, metrics: Dict) -> Dict:
        """
        计算比率指标

        Args:
            metrics: 原始指标字典

        Returns:
            添加了比率的指标字典
        """
        # 毛利率 = (营收 - 成本) / 营收
        if metrics.get('revenue') and metrics.get('operating_cost'):
            metrics['gross_margin'] = float(
                (metrics['revenue'] - metrics['operating_cost']) / metrics['revenue']
            )

        # 营业利润率 = 营业利润 / 营收
        if metrics.get('operating_profit') and metrics.get('revenue'):
            metrics['operating_margin'] = float(
                metrics['operating_profit'] / metrics['revenue']
            )

        # 净利率 = 净利润 / 营收
        if metrics.get('net_profit') and metrics.get('revenue'):
            metrics['net_margin'] = float(
                metrics['net_profit'] / metrics['revenue']
            )

        # 资产负债率 = 总负债 / 总资产
        if metrics.get('total_liabilities') and metrics.get('total_assets'):
            metrics['asset_liability_ratio'] = float(
                metrics['total_liabilities'] / metrics['total_assets']
            )

        # 流动比率 = 流动资产 / 流动负债
        if metrics.get('current_assets') and metrics.get('current_liabilities'):
            if metrics['current_liabilities'] != 0:
                metrics['current_ratio'] = float(
                    metrics['current_assets'] / metrics['current_liabilities']
                )

        # 速动比率 = (流动资产 - 存货) / 流动负债
        if metrics.get('current_assets') and metrics.get('inventory') and metrics.get('current_liabilities'):
            if metrics['current_liabilities'] != 0:
                metrics['quick_ratio'] = float(
                    (metrics['current_assets'] - metrics['inventory']) / metrics['current_liabilities']
                )

        # ROE = 净利润 / 平均净资产（这里简化为期末净资产）
        if metrics.get('net_profit') and metrics.get('total_equity'):
            if metrics['total_equity'] != 0:
                metrics['roe'] = float(
                    metrics['net_profit'] / metrics['total_equity']
                )

        # ROA = 净利润 / 平均总资产（简化）
        if metrics.get('net_profit') and metrics.get('total_assets'):
            if metrics['total_assets'] != 0:
                metrics['roa'] = float(
                    metrics['net_profit'] / metrics['total_assets']
                )

        # 自由现金流 = 经营现金流 - 资本支出（投资现金流的一部分）
        if metrics.get('operating_cash_flow') and metrics.get('investing_cash_flow'):
            # 注意：investing_cash_flow通常是负数
            # 这里简化处理，实际应该提取其中的capex部分
            metrics['free_cash_flow'] = metrics['operating_cash_flow'] + metrics['investing_cash_flow']

        # FCF / 营收
        if metrics.get('free_cash_flow') and metrics.get('revenue'):
            if metrics['revenue'] != 0:
                metrics['fcf_to_revenue'] = float(
                    metrics['free_cash_flow'] / metrics['revenue']
                )

        # 经营现金流 / 净利润（盈利质量）
        if metrics.get('operating_cash_flow') and metrics.get('net_profit'):
            if metrics['net_profit'] != 0:
                metrics['ocf_to_net_profit'] = float(
                    metrics['operating_cash_flow'] / metrics['net_profit']
                )

        # 研发费用率
        if metrics.get('rd_expense') and metrics.get('revenue'):
            if metrics['revenue'] != 0:
                metrics['rd_ratio'] = float(
                    metrics['rd_expense'] / metrics['revenue']
                )

        # BPS（每股净资产）= 净资产 / 股本（需要股本数据）
        # EPS 已在解析中获取，或者可以计算：净利润 / 股本
        # 估值指标（PE、PB、PS）需要股价数据，这里暂时无法计算

        return metrics

    def calculate_growth(self, stock_id: int, current_date: datetime, metrics: Dict) -> Dict:
        """
        计算增长率（需要历史数据）

        Args:
            stock_id: 股票ID
            current_date: 当前报告日期
            metrics: 当前指标字典

        Returns:
            添加了增长率的指标字典
        """
        try:
            # 查询去年同期数据
            last_year_date = datetime(current_date.year - 1, current_date.month, current_date.day)

            with session_scope() as session:
                last_year_metric = session.query(FinancialMetric).filter(
                    FinancialMetric.stock_id == stock_id,
                    FinancialMetric.report_date == last_year_date
                ).first()

                if last_year_metric:
                    # 营收同比增长率
                    if last_year_metric.revenue and metrics.get('revenue'):
                        if last_year_metric.revenue != 0:
                            metrics['revenue_yoy'] = float(
                                (metrics['revenue'] - float(last_year_metric.revenue)) / float(last_year_metric.revenue)
                            )

                    # 净利润同比增长率
                    if last_year_metric.net_profit and metrics.get('net_profit'):
                        if last_year_metric.net_profit != 0:
                            metrics['net_profit_yoy'] = float(
                                (metrics['net_profit'] - float(last_year_metric.net_profit)) / float(last_year_metric.net_profit)
                            )

                # 查询上一季度数据（环比）
                # 简化处理，暂不实现

        except Exception as e:
            self.logger.warning(f"计算增长率失败: {e}")

        return metrics

    def calculate_efficiency(self, metrics: Dict) -> Dict:
        """
        计算运营效率指标

        Args:
            metrics: 指标字典

        Returns:
            添加了效率指标的指标字典
        """
        # 总资产周转率 = 营收 / 平均总资产（简化）
        if metrics.get('revenue') and metrics.get('total_assets'):
            if metrics['total_assets'] != 0:
                metrics['asset_turnover'] = float(
                    metrics['revenue'] / metrics['total_assets']
                )

        # 存货周转率 = 营业成本 / 平均存货（简化）
        if metrics.get('operating_cost') and metrics.get('inventory'):
            if metrics['inventory'] != 0:
                metrics['inventory_turnover'] = float(
                    metrics['operating_cost'] / metrics['inventory']
                )

        # 应收账款周转率 = 营收 / 平均应收（简化）
        if metrics.get('revenue') and metrics.get('accounts_receivable'):
            if metrics['accounts_receivable'] != 0:
                metrics['receivable_turnover'] = float(
                    metrics['revenue'] / metrics['accounts_receivable']
                )

        # 现金周转周期 = 存货周转天数 + 应收账款天数 - 应付账款天数
        inventory_days = None
        receivable_days = None
        payable_days = None

        if metrics.get('inventory_turnover') and metrics['inventory_turnover'] != 0:
            inventory_days = 365 / metrics['inventory_turnover']

        if metrics.get('receivable_turnover') and metrics['receivable_turnover'] != 0:
            receivable_days = 365 / metrics['receivable_turnover']

        # 应付账款周转率（如果有应付和成本数据）
        if metrics.get('operating_cost') and metrics.get('accounts_payable'):
            if metrics['accounts_payable'] != 0:
                payable_turnover = float(metrics['operating_cost']) / float(metrics['accounts_payable'])
                payable_days = 365 / payable_turnover

        # 计算CCC
        if inventory_days is not None and receivable_days is not None and payable_days is not None:
            metrics['cash_conversion_cycle'] = float(
                inventory_days + receivable_days - payable_days
            )

        return metrics

    def save_to_database(self, metrics: Dict, report_id: int, stock_id: int, report_date: datetime) -> int:
        """
        保存指标到数据库

        Args:
            metrics: 指标字典
            report_id: 财报ID
            stock_id: 股票ID
            report_date: 报告日期

        Returns:
            新建记录的ID
        """
        with session_scope() as session:
            # 创建FinancialMetric对象
            metric_obj = FinancialMetric(
                report_id=report_id,
                stock_id=stock_id,
                report_date=report_date
            )

            # 设置所有字段
            for field_name, value in metrics.items():
                if value is not None and hasattr(metric_obj, field_name):
                    # 转换为Decimal（数据库需要）
                    if isinstance(value, (int, float)):
                        setattr(metric_obj, field_name, Decimal(str(value)))
                    else:
                        setattr(metric_obj, field_name, value)

            # 保存
            session.add(metric_obj)
            session.flush()

            metric_id = metric_obj.id
            self.logger.info(f"财务指标已保存到数据库: ID={metric_id}")

            return metric_id


# 便捷函数

def extract_metrics(parsed_data: Dict[str, Any], stock_id: int, report_date: datetime) -> Dict:
    """
    提取财务指标（便捷函数）

    Args:
        parsed_data: 解析结果
        stock_id: 股票ID
        report_date: 报告日期

    Returns:
        指标字典
    """
    extractor = MetricExtractor()
    return extractor.extract(parsed_data, stock_id, report_date)


if __name__ == '__main__':
    # 测试
    print("MetricExtractor模块")
    print("用法: 在其他模块中导入使用")
