"""
数据库连接和操作工具

提供数据库初始化、连接管理、基础CRUD操作
"""

import os
from contextlib import contextmanager
from typing import Optional, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


# 全局变量
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def get_database_url(db_path: Optional[str] = None) -> str:
    """
    获取数据库连接 URL

    Args:
        db_path: 数据库文件路径，如果为 None 则使用默认路径

    Returns:
        数据库连接 URL
    """
    if db_path is None:
        # 默认路径：项目根目录的 data/database.db
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.join(project_root, "data", "database.db")

    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # SQLite URL
    return f"sqlite:///{db_path}"


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    为 SQLite 连接设置 PRAGMA
    启用外键约束支持
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_engine(database_url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    初始化数据库引擎

    Args:
        database_url: 数据库连接 URL，如果为 None 则使用默认
        echo: 是否打印 SQL 语句（调试用）

    Returns:
        SQLAlchemy Engine 实例
    """
    global _engine, _SessionLocal

    if database_url is None:
        database_url = get_database_url()

    # 创建引擎
    # SQLite 特殊配置
    if database_url.startswith("sqlite"):
        _engine = create_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},  # SQLite 多线程支持
            poolclass=StaticPool,  # 使用静态连接池
        )
    else:
        # PostgreSQL 配置
        _engine = create_engine(
            database_url,
            echo=echo,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # 连接前测试
        )

    # 创建 Session 工厂
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine
    )

    return _engine


def get_engine() -> Engine:
    """
    获取数据库引擎（单例模式）

    Returns:
        SQLAlchemy Engine 实例
    """
    global _engine
    if _engine is None:
        init_engine()
    return _engine


def get_session() -> Session:
    """
    获取数据库 Session

    Returns:
        SQLAlchemy Session 实例

    注意：使用完后需要手动 close
    """
    global _SessionLocal
    if _SessionLocal is None:
        init_engine()
    return _SessionLocal()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    提供数据库 Session 的上下文管理器

    使用示例:
        with session_scope() as session:
            stock = session.query(Stock).filter_by(code="600519").first()

    自动处理：
    - Session 创建
    - 事务提交
    - 异常回滚
    - Session 关闭
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables(drop_existing: bool = False):
    """
    创建所有数据表

    Args:
        drop_existing: 是否先删除已存在的表（危险操作！）
    """
    engine = get_engine()

    if drop_existing:
        print("警告：正在删除所有现有表...")
        Base.metadata.drop_all(bind=engine)

    print("正在创建数据表...")
    Base.metadata.create_all(bind=engine)
    print("数据表创建完成")


def init_database(db_path: Optional[str] = None, reset: bool = False, echo: bool = False):
    """
    初始化数据库（一站式）

    Args:
        db_path: 数据库文件路径
        reset: 是否重置数据库（删除所有表重新创建）
        echo: 是否打印 SQL 语句
    """
    # 初始化引擎
    database_url = get_database_url(db_path) if db_path else None
    init_engine(database_url, echo=echo)

    # 创建表
    create_tables(drop_existing=reset)

    # 插入初始数据
    if reset:
        insert_initial_data()

    print(f"数据库初始化完成: {database_url or get_database_url()}")


def insert_initial_data():
    """
    插入初始数据（内置分析框架等）
    """
    from .models import Framework

    with session_scope() as session:
        # 检查是否已存在
        existing = session.query(Framework).filter_by(name="value_investing").first()
        if existing:
            print("初始数据已存在，跳过")
            return

        # 价值投资框架
        value_framework = Framework(
            name="value_investing",
            version="1.0",
            type="value",
            description="价值投资框架（巴菲特风格）",
            is_builtin=True,
            config={
                "dimensions": [
                    {
                        "name": "profitability",
                        "name_zh": "盈利能力",
                        "weight": 0.4,
                        "metrics": [
                            {"indicator": "roe", "threshold": [
                                {"min": 0.15, "score": 100, "label": "优秀"},
                                {"min": 0.10, "max": 0.15, "score": 70, "label": "良好"},
                                {"max": 0.10, "score": 40, "label": "一般"}
                            ]}
                        ]
                    },
                    {
                        "name": "financial_health",
                        "name_zh": "财务健康",
                        "weight": 0.3,
                        "metrics": [
                            {"indicator": "asset_liability_ratio", "threshold": [
                                {"max": 0.40, "score": 100, "label": "优秀"},
                                {"min": 0.40, "max": 0.60, "score": 70, "label": "良好"},
                                {"min": 0.60, "score": 40, "label": "警示"}
                            ]}
                        ]
                    },
                    {
                        "name": "growth",
                        "name_zh": "成长性",
                        "weight": 0.20,
                        "metrics": [
                            {"indicator": "revenue_yoy", "threshold": [
                                {"min": 0.15, "score": 100, "label": "优秀"},
                                {"min": 0.05, "max": 0.15, "score": 70, "label": "良好"},
                                {"max": 0.05, "score": 40, "label": "一般"}
                            ]}
                        ]
                    },
                    {
                        "name": "valuation",
                        "name_zh": "估值",
                        "weight": 0.10,
                        "metrics": [
                            {"indicator": "pe_ratio", "threshold": [
                                {"max": 15, "score": 100, "label": "低估"},
                                {"min": 15, "max": 25, "score": 70, "label": "合理"},
                                {"min": 25, "score": 40, "label": "高估"}
                            ]}
                        ]
                    }
                ]
            }
        )

        # 成长投资框架
        growth_framework = Framework(
            name="growth_investing",
            version="1.0",
            type="growth",
            description="成长投资框架（彼得·林奇风格）",
            is_builtin=True,
            config={
                "dimensions": [
                    {
                        "name": "high_growth",
                        "name_zh": "高成长",
                        "weight": 0.5,
                        "metrics": [
                            {"indicator": "revenue_yoy", "threshold": [
                                {"min": 0.30, "score": 100, "label": "优秀"},
                                {"min": 0.20, "max": 0.30, "score": 80, "label": "良好"},
                                {"min": 0.10, "max": 0.20, "score": 60, "label": "一般"}
                            ]},
                            {"indicator": "net_profit_yoy", "threshold": [
                                {"min": 0.30, "score": 100, "label": "优秀"},
                                {"min": 0.20, "max": 0.30, "score": 80, "label": "良好"}
                            ]}
                        ]
                    },
                    {
                        "name": "profitability_quality",
                        "name_zh": "盈利质量",
                        "weight": 0.3,
                        "metrics": [
                            {"indicator": "gross_margin", "threshold": [
                                {"min": 0.40, "score": 100, "label": "优秀"},
                                {"min": 0.30, "max": 0.40, "score": 70, "label": "良好"}
                            ]}
                        ]
                    },
                    {
                        "name": "market_position",
                        "name_zh": "市场地位",
                        "weight": 0.2,
                        "metrics": [
                            {"indicator": "rd_ratio", "threshold": [
                                {"min": 0.10, "score": 100, "label": "优秀"},
                                {"min": 0.05, "max": 0.10, "score": 70, "label": "良好"}
                            ]}
                        ]
                    }
                ]
            }
        )

        session.add(value_framework)
        session.add(growth_framework)

        print("初始数据插入完成：2 个内置分析框架")


# 便捷的 CRUD 操作函数

def add_stock(code: str, name: str, market: str, **kwargs) -> int:
    """
    添加股票

    Args:
        code: 股票代码
        name: 股票名称
        market: 市场类型（A, HK, US）
        **kwargs: 其他字段

    Returns:
        新建股票的 ID
    """
    from .models import Stock

    with session_scope() as session:
        stock = Stock(code=code, name=name, market=market, **kwargs)
        session.add(stock)
        session.flush()  # 获取 ID
        return stock.id


def get_stock_by_code(code: str):
    """根据代码获取股票"""
    from .models import Stock

    with session_scope() as session:
        return session.query(Stock).filter_by(code=code).first()


def get_or_create_stock(code: str, name: str, market: str, **kwargs):
    """
    获取或创建股票

    Returns:
        (stock, created) tuple
    """
    from .models import Stock

    with session_scope() as session:
        stock = session.query(Stock).filter_by(code=code).first()
        if stock:
            return stock, False
        else:
            stock = Stock(code=code, name=name, market=market, **kwargs)
            session.add(stock)
            session.flush()
            return stock, True


if __name__ == "__main__":
    # 测试：初始化数据库
    init_database(reset=True, echo=True)

    # 测试：添加股票
    stock_id = add_stock(
        code="600519",
        name="贵州茅台",
        market="A",
        exchange="SSE",
        industry="白酒"
    )
    print(f"添加股票成功，ID: {stock_id}")

    # 测试：查询股票
    stock = get_stock_by_code("600519")
    print(f"查询股票: {stock}")
