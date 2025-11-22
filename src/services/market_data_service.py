"""
市场数据服务

负责获取和存储市场数据（市值、估值、分红等）
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from ..database import db
from ..database.models import Stock, FinancialMetric, FinancialReport
from ..data_sources import AkShareSource

logger = logging.getLogger(__name__)


class MarketDataService:
    """市场数据服务"""

    def __init__(self, data_source=None):
        """
        初始化

        Args:
            data_source: 数据源实例，默认使用 AkShareSource
        """
        self.data_source = data_source or AkShareSource()
        logger.info(f"市场数据服务初始化，使用数据源: {self.data_source.name}")

    def fetch_and_save_market_cap_history(
        self,
        stock_code: str,
        years: int = 5
    ) -> bool:
        """
        获取并保存历史市值数据

        Args:
            stock_code: 股票代码
            years: 年数

        Returns:
            True 如果成功，False 否则
        """
        try:
            logger.info(f"开始获取市值历史数据: {stock_code}, {years}年")

            # 从数据源获取数据
            market_cap_data = self.data_source.get_market_cap_history(stock_code, years)

            if not market_cap_data:
                logger.warning(f"未获取到市值数据: {stock_code}")
                return False

            # 保存到数据库
            with db.session_scope() as session:
                # 查找股票
                stock = session.query(Stock).filter_by(code=stock_code).first()
                if not stock:
                    logger.error(f"数据库中未找到股票: {stock_code}")
                    return False

                # 更新每年的财务指标
                updated_count = 0
                for year_data in market_cap_data:
                    year = year_data['year']
                    market_cap = year_data['market_cap']

                    # 查找对应年份的年报
                    report = session.query(FinancialReport).filter_by(
                        stock_id=stock.id,
                        report_type='annual',
                        fiscal_year=year
                    ).first()

                    if report:
                        # 查找对应的财务指标
                        metric = session.query(FinancialMetric).filter_by(
                            stock_id=stock.id,
                            report_id=report.id
                        ).first()

                        if metric:
                            # 更新 extra_metrics
                            if not metric.extra_metrics:
                                metric.extra_metrics = {}

                            metric.extra_metrics['market_cap'] = float(market_cap)
                            metric.extra_metrics['market_cap_date'] = year_data['date'].isoformat()

                            # 如果有净利润，计算 PE
                            if metric.net_profit and metric.net_profit > 0:
                                pe_ratio = market_cap / metric.net_profit
                                metric.pe_ratio = Decimal(str(pe_ratio))
                                metric.extra_metrics['pe_ratio_calculated'] = float(pe_ratio)

                            session.add(metric)
                            updated_count += 1
                            logger.debug(f"更新 {year} 年市值: {market_cap / 1e8:.2f}亿")

                logger.info(f"成功更新 {updated_count} 条市值数据: {stock_code}")
                return updated_count > 0

        except Exception as e:
            logger.error(f"获取市值历史失败 {stock_code}: {e}")
            return False

    def fetch_and_save_dividend_data(
        self,
        stock_code: str,
        years: int = 5
    ) -> bool:
        """
        获取并保存分红数据

        Args:
            stock_code: 股票代码
            years: 年数

        Returns:
            True 如果成功，False 否则
        """
        try:
            logger.info(f"开始获取分红数据: {stock_code}, {years}年")

            # 计算年份范围
            current_year = datetime.now().year
            start_year = current_year - years
            end_year = current_year

            # 从数据源获取数据
            dividend_data = self.data_source.get_dividend_data(
                stock_code,
                start_year,
                end_year
            )

            if not dividend_data:
                logger.warning(f"未获取到分红数据: {stock_code}")
                return False

            # 保存到数据库
            with db.session_scope() as session:
                # 查找股票
                stock = session.query(Stock).filter_by(code=stock_code).first()
                if not stock:
                    logger.error(f"数据库中未找到股票: {stock_code}")
                    return False

                # 更新每年的财务指标
                updated_count = 0
                for div_data in dividend_data:
                    year = div_data['year']
                    dividend_per_share = div_data['dividend_per_share']

                    # 查找对应年份的年报
                    report = session.query(FinancialReport).filter_by(
                        stock_id=stock.id,
                        report_type='annual',
                        fiscal_year=year
                    ).first()

                    if report:
                        # 查找对应的财务指标
                        metric = session.query(FinancialMetric).filter_by(
                            stock_id=stock.id,
                            report_id=report.id
                        ).first()

                        if metric:
                            # 更新 extra_metrics
                            if not metric.extra_metrics:
                                metric.extra_metrics = {}

                            # 计算总分红金额（假设股本不变）
                            # 实际应该使用当年的总股本
                            # 这里简化处理
                            metric.extra_metrics['dividend_per_share'] = float(dividend_per_share)

                            # 如果有净利润，计算分红率
                            if metric.net_profit and metric.net_profit > 0 and dividend_per_share > 0:
                                # 需要知道总股本才能计算总分红金额
                                # 这里留待后续完善
                                pass

                            session.add(metric)
                            updated_count += 1
                            logger.debug(f"更新 {year} 年分红: 每股{dividend_per_share}元")

                logger.info(f"成功更新 {updated_count} 条分红数据: {stock_code}")
                return updated_count > 0

        except Exception as e:
            logger.error(f"获取分红数据失败 {stock_code}: {e}")
            return False

    def enrich_financial_metrics(
        self,
        stock_code: str,
        years: int = 5
    ) -> bool:
        """
        补充财务指标的市场数据

        集成执行：
        1. 市值历史
        2. 分红数据
        3. 估值指标

        Args:
            stock_code: 股票代码
            years: 年数

        Returns:
            True 如果成功，False 否则
        """
        logger.info(f"开始补充市场数据: {stock_code}")

        success = True

        # 1. 市值历史
        if not self.fetch_and_save_market_cap_history(stock_code, years):
            logger.warning(f"市值数据获取失败: {stock_code}")
            success = False

        # 2. 分红数据
        if not self.fetch_and_save_dividend_data(stock_code, years):
            logger.warning(f"分红数据获取失败: {stock_code}")
            success = False

        if success:
            logger.info(f"✓ 市场数据补充完成: {stock_code}")
        else:
            logger.warning(f"⚠ 市场数据部分失败: {stock_code}")

        return success

    def get_stock_valuation_history(
        self,
        stock_code: str,
        years: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取股票估值历史（从数据库）

        Args:
            stock_code: 股票代码
            years: 年数

        Returns:
            估值历史列表，每个元素包含：
            - year: 年份
            - pe_ratio: 市盈率
            - pb_ratio: 市净率
            - market_cap: 市值
        """
        try:
            with db.session_scope() as session:
                # 查找股票
                stock = session.query(Stock).filter_by(code=stock_code).first()
                if not stock:
                    return []

                # 查询最近N年的年报指标
                current_year = datetime.now().year
                start_year = current_year - years

                metrics = (
                    session.query(FinancialMetric)
                    .join(FinancialReport)
                    .filter(
                        FinancialMetric.stock_id == stock.id,
                        FinancialReport.report_type == 'annual',
                        FinancialReport.fiscal_year >= start_year
                    )
                    .order_by(FinancialReport.fiscal_year.desc())
                    .all()
                )

                # 提取估值数据
                result = []
                for metric in metrics:
                    if metric.report:
                        result.append({
                            'year': metric.report.fiscal_year,
                            'pe_ratio': float(metric.pe_ratio) if metric.pe_ratio else None,
                            'pb_ratio': float(metric.pb_ratio) if metric.pb_ratio else None,
                            'market_cap': metric.extra_metrics.get('market_cap') if metric.extra_metrics else None,
                        })

                return result

        except Exception as e:
            logger.error(f"获取估值历史失败: {e}")
            return []
