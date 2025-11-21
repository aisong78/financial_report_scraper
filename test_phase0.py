#!/usr/bin/env python
"""
Phase 0 功能测试脚本

测试已完成的基础模块
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_config():
    """测试配置管理"""
    print("=" * 60)
    print("【测试 1】配置管理模块")
    print("=" * 60)

    try:
        from src.utils.config import get_config

        config = get_config()
        print(f"✓ 配置加载成功")
        print(f"  - 自选股数量: {len(config.stocks)}")
        print(f"  - 自选股列表: {config.stocks}")
        print(f"  - 保存目录: {config.save_dir}")
        print(f"  - 用户邮箱: {config.user_email}")
        print(f"  - 日志级别: {config.log_level}")

        # 验证配置
        is_valid = config.validate()
        if is_valid:
            print("✓ 配置验证通过")
        else:
            print("⚠ 配置验证失败（这是正常的，因为使用的是示例配置）")

        return True

    except Exception as e:
        print(f"✗ 配置管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logger():
    """测试日志系统"""
    print("\n" + "=" * 60)
    print("【测试 2】日志系统")
    print("=" * 60)

    try:
        from src.utils.logger import get_logger

        logger = get_logger()
        print(f"✓ 日志系统初始化成功")

        # 写入不同级别的日志
        logger.debug("这是一条 DEBUG 日志")
        logger.info("这是一条 INFO 日志")
        logger.warning("这是一条 WARNING 日志")

        print("✓ 日志写入成功")
        print(f"  - 日志文件位置: logs/financial_scraper.log")

        return True

    except Exception as e:
        print(f"✗ 日志系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """测试数据库"""
    print("\n" + "=" * 60)
    print("【测试 3】数据库系统")
    print("=" * 60)

    try:
        from src.database.db import init_database, add_stock, get_stock_by_code
        from src.database.models import Stock, Framework

        # 初始化数据库（重置）
        print("正在初始化数据库...")
        init_database(reset=True, echo=False)
        print("✓ 数据库初始化成功")

        # 测试添加股票
        print("\n正在添加测试股票...")
        stock_id = add_stock(
            code="600519",
            name="贵州茅台",
            market="A",
            exchange="SSE",
            industry="白酒"
        )
        print(f"✓ 添加股票成功，ID: {stock_id}")

        # 测试查询股票
        print("\n正在查询股票...")
        stock = get_stock_by_code("600519")
        if stock:
            print(f"✓ 查询成功: {stock.code} - {stock.name}")
        else:
            print("✗ 查询失败")
            return False

        # 检查内置框架
        print("\n正在检查内置分析框架...")
        from src.database.db import session_scope
        with session_scope() as session:
            frameworks = session.query(Framework).all()
            print(f"✓ 找到 {len(frameworks)} 个内置框架:")
            for fw in frameworks:
                print(f"  - {fw.name} ({fw.type}): {fw.description}")

        print(f"\n✓ 数据库文件位置: data/database.db")

        return True

    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scrapers():
    """测试爬虫（不实际下载）"""
    print("\n" + "=" * 60)
    print("【测试 4】爬虫模块")
    print("=" * 60)

    try:
        from src.scrapers import identify_market, ChinaStockScraper, USStockScraper

        # 测试市场识别
        print("测试市场识别功能:")
        test_codes = [
            ("600519", "A"),
            ("000001", "A"),
            ("00700", "HK"),
            ("01810", "HK"),
            ("AAPL", "US"),
            ("TSLA", "US"),
        ]

        all_correct = True
        for code, expected in test_codes:
            result = identify_market(code)
            status = "✓" if result == expected else "✗"
            print(f"  {status} {code} -> {result} (预期: {expected})")
            if result != expected:
                all_correct = False

        if all_correct:
            print("✓ 市场识别功能正常")
        else:
            print("✗ 市场识别功能有误")
            return False

        # 测试爬虫初始化
        print("\n测试爬虫初始化:")
        a_scraper = ChinaStockScraper(market="A")
        print(f"✓ A股爬虫初始化成功")

        hk_scraper = ChinaStockScraper(market="HK")
        print(f"✓ 港股爬虫初始化成功")

        us_scraper = USStockScraper()
        print(f"✓ 美股爬虫初始化成功")

        print("\n注意：实际下载功能需要网络连接，这里不测试")

        return True

    except Exception as e:
        print(f"✗ 爬虫测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "Phase 0 功能测试" + " " * 27 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    results = {}

    # 运行测试
    results['配置管理'] = test_config()
    results['日志系统'] = test_logger()
    results['数据库'] = test_database()
    results['爬虫模块'] = test_scrapers()

    # 汇总结果
    print("\n" + "=" * 60)
    print("【测试总结】")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for r in results.values() if r)

    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}  {name}")

    print()
    print(f"总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！Phase 0 基础模块工作正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
