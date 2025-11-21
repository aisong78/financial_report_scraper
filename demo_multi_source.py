"""
多数据源使用演示

展示如何使用数据源管理器自动切换数据源
"""

from src.scrapers.data_source_manager import DataSourceManager, get_financial_data


def demo_basic():
    """基础演示：使用默认配置"""
    print("=" * 60)
    print("【演示 1】基础使用 - 默认配置")
    print("=" * 60)
    print()

    # 创建数据源管理器（使用默认配置）
    manager = DataSourceManager()

    print(f"✓ 可用数据源: {[s.name for s in manager.available_sources]}")
    print()

    # 尝试获取数据
    print("正在获取贵州茅台（600519）的财报...")
    data = manager.fetch_data('600519', lookback_days=180)

    if data:
        print(f"✓ 成功！")
        print(f"  数据来源: {data['source']}")
        print(f"  数据类型: {data['data_type']}")

        if data['data_type'] == 'pdf':
            print(f"  文件路径: {data['file_path']}")
        elif data['data_type'] == 'dataframe':
            print(f"  报表数量: 3 (资产负债表、利润表、现金流量表)")

    else:
        print("✗ 获取数据失败（可能是网络限制）")

    print()


def demo_with_config():
    """高级演示：使用自定义配置"""
    print("=" * 60)
    print("【演示 2】自定义配置 - 启用多数据源")
    print("=" * 60)
    print()

    # 自定义配置
    config = {
        'preferred_source': 'akshare',  # 优先使用 AkShare
        'enable_akshare': True,          # 启用 AkShare（需要先安装）
    }

    manager = DataSourceManager(config)

    print(f"配置的首选数据源: {config['preferred_source']}")
    print(f"实际可用数据源: {[s.name for s in manager.available_sources]}")
    print()

    # 如果 AkShare 没安装，会自动降级到巨潮资讯
    if len(manager.available_sources) == 0:
        print("⚠ 没有可用的数据源！")
        print("提示：如果想使用 AkShare，请运行: pip install akshare")
        return

    print("正在获取数据...")
    data = manager.fetch_data('600519')

    if data:
        print(f"✓ 成功从 {data['source']} 获取数据")
    else:
        print("✗ 所有数据源都失败了")

    print()


def demo_convenience_function():
    """便捷函数演示"""
    print("=" * 60)
    print("【演示 3】便捷函数 - 一行代码获取数据")
    print("=" * 60)
    print()

    # 使用便捷函数（最简单的方式）
    data = get_financial_data('600519', lookback_days=180)

    if data:
        print(f"✓ 成功！数据来源: {data['source']}")
    else:
        print("✗ 获取失败")

    print()


def demo_check_sources():
    """查看所有可用数据源"""
    print("=" * 60)
    print("【演示 4】查看可用数据源")
    print("=" * 60)
    print()

    manager = DataSourceManager()

    print(f"总数据源数量: {len(manager.sources)}")
    print(f"可用数据源数量: {len(manager.available_sources)}")
    print()

    print("数据源详情:")
    for i, source in enumerate(manager.sources, 1):
        status = "✓ 可用" if source.is_available() else "✗ 不可用"
        print(f"  {i}. {source.name:12} - {status}")

    print()

    if len(manager.available_sources) == 1:
        print("💡 提示: 只有巨潮资讯可用")
        print("   如需更多数据源，请安装:")
        print("   - pip install akshare  (推荐)")
        print("   - pip install tushare  (需要注册)")

    print()


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          多数据源使用演示                                ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # 演示 1: 基础使用
    demo_basic()

    # 演示 2: 自定义配置
    demo_with_config()

    # 演示 3: 便捷函数
    demo_convenience_function()

    # 演示 4: 查看数据源
    demo_check_sources()

    print("=" * 60)
    print("演示完成！")
    print("=" * 60)
    print()
    print("📖 更多用法请参考: 多数据源使用指南.md")
    print()


if __name__ == '__main__':
    main()
