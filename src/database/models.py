"""
数据库模型定义

使用 SQLAlchemy ORM 定义所有数据表模型
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey,
    Integer, String, Text, Numeric, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


class Stock(Base):
    """股票基本信息表"""
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    market: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # A, HK, US
    industry: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(50))
    exchange: Mapped[Optional[str]] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(10), default="CNY")
    listing_date: Mapped[Optional[datetime]] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON)  # 元数据（避免使用保留字 metadata）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    financial_reports = relationship("FinancialReport", back_populates="stock", cascade="all, delete-orphan")
    watchlist_entries = relationship("Watchlist", back_populates="stock", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="stock", cascade="all, delete-orphan")
    market_expectations = relationship("MarketExpectation", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Stock(code='{self.code}', name='{self.name}', market='{self.market}')>"


class Watchlist(Base):
    """自选股列表表"""
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)  # Phase 4 多用户支持
    tags: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    stock = relationship("Stock", back_populates="watchlist_entries")

    def __repr__(self) -> str:
        return f"<Watchlist(stock_id={self.stock_id}, priority={self.priority})>"


class FinancialReport(Base):
    """财报元数据表"""
    __tablename__ = "financial_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # annual, semi_annual, quarterly
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period: Mapped[Optional[str]] = mapped_column(String(10))  # Q1, Q2, Q3, Q4, H1, H2, FY
    report_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    publish_date: Mapped[Optional[datetime]] = mapped_column(Date)
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    file_format: Mapped[Optional[str]] = mapped_column(String(10))  # pdf, html, xml
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    is_parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    parsed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON)  # 元数据（避免使用保留字 metadata）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 唯一约束
    __table_args__ = (
        UniqueConstraint('stock_id', 'fiscal_year', 'fiscal_period', name='uq_report'),
    )

    # 关系
    stock = relationship("Stock", back_populates="financial_reports")
    financial_metrics = relationship("FinancialMetric", back_populates="report", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="report")

    def __repr__(self) -> str:
        return f"<FinancialReport(stock_id={self.stock_id}, type='{self.report_type}', period='{self.fiscal_year}{self.fiscal_period}')>"


class FinancialMetric(Base):
    """财务指标表"""
    __tablename__ = "financial_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("financial_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    report_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10))

    # 损益表指标
    revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    revenue_yoy: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    revenue_qoq: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    operating_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    net_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    net_profit_yoy: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    net_profit_qoq: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    eps: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    gross_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    operating_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    net_margin: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))

    # 资产负债表指标
    total_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    total_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    total_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    current_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    current_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    # 财务比率
    asset_liability_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    current_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    quick_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    roe: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    roa: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))

    # 现金流量表指标
    operating_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    investing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    financing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    free_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    # 估值指标
    pe_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    pb_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    ps_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))

    # 其他指标
    rd_expense: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    rd_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))

    # 元数据
    extraction_method: Mapped[Optional[str]] = mapped_column(String(50))
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 唯一约束
    __table_args__ = (
        UniqueConstraint('stock_id', 'report_date', name='uq_metric'),
    )

    # 关系
    report = relationship("FinancialReport", back_populates="financial_metrics")

    def __repr__(self) -> str:
        return f"<FinancialMetric(stock_id={self.stock_id}, date={self.report_date}, revenue={self.revenue})>"


class AnalysisResult(Base):
    """分析结果表"""
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id: Mapped[Optional[int]] = mapped_column(ForeignKey("financial_reports.id", ondelete="SET NULL"), index=True)
    framework_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    framework_version: Mapped[Optional[str]] = mapped_column(String(20))

    # 评分
    overall_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    overall_rating: Mapped[Optional[str]] = mapped_column(String(10))
    dimension_scores: Mapped[Optional[dict]] = mapped_column(JSON)

    # 投资建议
    recommendation: Mapped[Optional[str]] = mapped_column(String(20))  # BUY, HOLD, SELL
    recommendation_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    reasoning: Mapped[Optional[str]] = mapped_column(Text)

    # 风险和机会
    risks: Mapped[Optional[dict]] = mapped_column(JSON)
    opportunities: Mapped[Optional[dict]] = mapped_column(JSON)

    # AI 分析结果
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    ai_insights: Mapped[Optional[dict]] = mapped_column(JSON)

    # 元数据
    analysis_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    execution_time: Mapped[Optional[int]] = mapped_column(Integer)  # 毫秒

    # 关系
    stock = relationship("Stock", back_populates="analysis_results")
    report = relationship("FinancialReport", back_populates="analysis_results")

    def __repr__(self) -> str:
        return f"<AnalysisResult(stock_id={self.stock_id}, framework='{self.framework_name}', rating='{self.overall_rating}')>"


class Framework(Base):
    """分析框架配置表"""
    __tablename__ = "frameworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    type: Mapped[Optional[str]] = mapped_column(String(20), index=True)  # value, growth, custom
    description: Mapped[Optional[str]] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Framework(name='{self.name}', type='{self.type}', version='{self.version}')>"


class MarketExpectation(Base):
    """市场预期数据表"""
    __tablename__ = "market_expectations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period: Mapped[Optional[str]] = mapped_column(String(10))

    # 预期指标
    expected_revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    expected_net_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    expected_eps: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))

    # 预期范围
    revenue_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    revenue_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    profit_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))
    profit_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2))

    # 数据来源
    source: Mapped[Optional[str]] = mapped_column(String(50))
    analyst_count: Mapped[Optional[int]] = mapped_column(Integer)
    consensus_rating: Mapped[Optional[str]] = mapped_column(String(20))

    # 元数据
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index('idx_expectations_period', 'fiscal_year', 'fiscal_period'),
    )

    # 关系
    stock = relationship("Stock", back_populates="market_expectations")

    def __repr__(self) -> str:
        return f"<MarketExpectation(stock_id={self.stock_id}, period='{self.fiscal_year}{self.fiscal_period}')>"
