#!/usr/bin/env python
"""
财报下载演示脚本

展示如何使用爬虫下载财报
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def demo_a_stock():
    """演示下载A股财报"""
    print("\n" + "=" * 60)
    print("【演示 1】下载 A股财报")
    print("=" * 60)

    try:
        from src.scrapers import scrape_a_stock

        print("\n正在下载贵州茅台（600519）最近365天的财报...")
        print("注意：这会实际从网络下载文件，可能需要一些时间\n")

        files = scrape_a_stock(
            stock_code="600519",
            lookback_days=365
        )

        print(f"\n✓ 下载完成！共 {len(files)} 份财报")
        print("\n下载的文件：")
        for f in files:
            print(f"  - {f}")

        print(f"\n文件保存在: reports/A/ 目录")

        return True

    except Exception as e:
        print(f"\n✗ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_hk_stock():
    """演示下载港股财报"""
    print("\n" + "=" * 60)
    print("【演示 2】下载 港股财报")
    print("=" * 60)

    try:
        from src.scrapers import scrape_hk_stock

        print("\n正在下载腾讯控股（00700）最近365天的财报...")
        print("注意：这会实际从网络下载文件，可能需要一些时间\n")

        files = scrape_hk_stock(
            stock_code="00700",
            lookback_days=365
        )

        print(f"\n✓ 下载完成！共 {len(files)} 份财报")
        print("\n下载的文件：")
        for f in files:
            print(f"  - {f}")

        print(f"\n文件保存在: reports/HK/ 目录")

        return True

    except Exception as e:
        print(f"\n✗ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_us_stock():
    """演示下载美股财报"""
    print("\n" + "=" * 60)
    print("【演示 3】下载 美股财报")
    print("=" * 60)

    print("\n⚠️  美股下载需要先配置邮箱")
    print("请按照以下步骤操作：")
    print("  1. 复制 config.json.example 为 config.json")
    print("  2. 修改 config.json 中的 user_email 为你的真实邮箱")
    print("  3. 重新运行此脚本")
    print()

    # 检查配置
    config_file = project_root / "config.json"
    if not config_file.exists():
        print("❌ 未找到 config.json 文件")
        print("   请先创建配置文件")
        return False

    try:
        from src.utils.config import get_config
        config = get_config()

        if "example.com" in config.user_email:
            print("❌ 请在 config.json 中设置真实邮箱")
            print(f"   当前邮箱: {config.user_email}")
            return False

    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return False

    # 尝试下载
    try:
        from src.scrapers import scrape_us_stock

        print("\n正在下载苹果公司（AAPL）最近365天的财报...")
        print("注意：这会实际从SEC网站下载文件，可能需要一些时间\n")

        files = scrape_us_stock(
            ticker="AAPL",
            lookback_days=365
        )

        print(f"\n✓ 下载完成！共 {len(files)} 份财报")
        print("\n下载的文件：")
        for f in files:
            print(f"  - {f}")

        print(f"\n文件保存在: reports/US/ 目录")

        return True

    except Exception as e:
        print(f"\n✗ 下载失败: {e}")
        print("\n可能的原因：")
        print("  - SEC网站访问限制（403错误）")
        print("  - 网络连接问题")
        print("  - 邮箱格式不正确")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "财报下载演示" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("这个脚本会实际下载财报文件，演示爬虫功能")
    print("下载的文件会保存在 reports/ 目录")
    print()

    # 询问用户想下载哪个市场
    print("请选择要演示的市场：")
    print("  1. A股（如：贵州茅台 600519）")
    print("  2. 港股（如：腾讯控股 00700）")
    print("  3. 美股（如：苹果 AAPL）- 需要先配置邮箱")
    print("  4. 全部演示")
    print("  0. 退出")
    print()

    choice = input("请输入选项 (0-4): ").strip()

    if choice == "0":
        print("\n已退出")
        return

    elif choice == "1":
        demo_a_stock()

    elif choice == "2":
        demo_hk_stock()

    elif choice == "3":
        demo_us_stock()

    elif choice == "4":
        print("\n开始全部演示...\n")
        demo_a_stock()
        demo_hk_stock()
        demo_us_stock()

    else:
        print("\n无效选项")
        return

    print("\n" + "=" * 60)
    print("演示结束")
    print("=" * 60)
    print()
    print("📁 下载的文件在: reports/ 目录")
    print("📊 下一步: Phase 1 将实现财报解析和分析功能")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
