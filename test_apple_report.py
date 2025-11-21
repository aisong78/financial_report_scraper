"""
测试苹果财报解析

使用真实的10-K财报HTML文件测试完整流程
"""

import os
from datetime import datetime
from src.parsers import HTMLParser
from src.extractors import MetricExtractor
from src.extractors.validator import MetricValidator


def test_apple_10k(file_path: str):
    """
    测试苹果10-K财报解析

    Args:
        file_path: HTML文件路径
    """
    print("=" * 60)
    print("测试苹果公司 10-K 财报解析")
    print("=" * 60)
    print()

    # 检查文件
    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        print()
        print("请把苹果10-K的HTML文件放到这个位置:")
        print(f"  {file_path}")
        print()
        print("或者使用其他路径，运行:")
        print("  python test_apple_report.py /path/to/your/file.html")
        return

    file_size_mb = os.path.getsize(file_path) / 1024 / 1024
    print(f"✓ 找到文件: {os.path.basename(file_path)}")
    print(f"  大小: {file_size_mb:.2f} MB")
    print()

    # 步骤1: 解析HTML
    print("【步骤 1】解析HTML财报")
    print("-" * 60)

    try:
        parser = HTMLParser()
        print("正在解析...")

        parsed_data = parser.parse(file_path)

        print("✓ 解析成功！")
        print()

        # 显示解析结果摘要
        print("解析结果摘要:")

        # 利润表
        income = parsed_data.get('income_statement', {})
        print()
        print("📊 利润表 (Income Statement):")
        if income:
            print(f"  营业收入:     {format_number(income.get('revenue'))}")
            print(f"  营业成本:     {format_number(income.get('operating_cost'))}")
            print(f"  营业利润:     {format_number(income.get('operating_profit'))}")
            print(f"  净利润:       {format_number(income.get('net_profit'))}")
            # EPS显示（Basic和Diluted）
            eps_basic = income.get('eps_basic')
            eps_diluted = income.get('eps_diluted')
            if eps_basic or eps_diluted:
                eps_str = f"${eps_basic:.2f}" if eps_basic else "N/A"
                if eps_diluted:
                    eps_str += f" (稀释: ${eps_diluted:.2f})"
                print(f"  EPS:          {eps_str}")
            else:
                print(f"  EPS:          N/A")
        else:
            print("  ⚠ 未找到利润表数据")

        # 资产负债表
        balance = parsed_data.get('balance_sheet', {})
        print()
        print("💰 资产负债表 (Balance Sheet):")
        if balance:
            print(f"  总资产:       {format_number(balance.get('total_assets'))}")
            print(f"  总负债:       {format_number(balance.get('total_liabilities'))}")
            print(f"  股东权益:     {format_number(balance.get('total_equity'))}")
            print(f"  流动资产:     {format_number(balance.get('current_assets'))}")
            print(f"  流动负债:     {format_number(balance.get('current_liabilities'))}")
        else:
            print("  ⚠ 未找到资产负债表数据")

        # 现金流量表
        cashflow = parsed_data.get('cash_flow', {})
        print()
        print("💵 现金流量表 (Cash Flow):")
        if cashflow:
            print(f"  经营现金流:   {format_number(cashflow.get('operating_cash_flow'))}")
            print(f"  投资现金流:   {format_number(cashflow.get('investing_cash_flow'))}")
            print(f"  筹资现金流:   {format_number(cashflow.get('financing_cash_flow'))}")
        else:
            print("  ⚠ 未找到现金流量表数据")

        print()

        # 步骤2: 提取指标
        print("【步骤 2】提取财务指标")
        print("-" * 60)

        extractor = MetricExtractor()
        stock_id = 1  # 模拟股票ID
        report_date = datetime(2024, 9, 28)  # 苹果财年结束日期

        print("正在提取46个财务指标...")
        metrics = extractor.extract(parsed_data, stock_id, report_date)

        valid_metrics = [k for k, v in metrics.items() if v is not None]
        print(f"✓ 成功提取 {len(valid_metrics)} 个有效指标")
        print()

        # 显示关键指标
        print("关键指标:")
        print()
        print(f"  盈利能力:")
        print(f"    毛利率:         {format_percent(metrics.get('gross_margin'))}")
        print(f"    净利率:         {format_percent(metrics.get('net_margin'))}")
        print(f"    ROE:            {format_percent(metrics.get('roe'))}")
        print(f"    ROA:            {format_percent(metrics.get('roa'))}")
        print()

        print(f"  财务健康:")
        print(f"    资产负债率:     {format_percent(metrics.get('asset_liability_ratio'))}")
        print(f"    流动比率:       {format_ratio(metrics.get('current_ratio'))}")
        print(f"    速动比率:       {format_ratio(metrics.get('quick_ratio'))}")
        print()

        print(f"  运营效率:")
        print(f"    资产周转率:     {format_ratio(metrics.get('asset_turnover'))}")
        print(f"    存货周转率:     {format_ratio(metrics.get('inventory_turnover'))}")
        print()

        print(f"  现金流:")
        print(f"    自由现金流:     {format_number(metrics.get('free_cash_flow'))}")
        print(f"    FCF/营收:       {format_percent(metrics.get('fcf_to_revenue'))}")
        print(f"    OCF/净利润:     {format_ratio(metrics.get('ocf_to_net_profit'))}")
        print()

        # 步骤3: 验证数据
        print("【步骤 3】数据验证")
        print("-" * 60)

        validator = MetricValidator()
        is_valid, errors = validator.validate(metrics)
        confidence = validator.calculate_confidence_score(metrics, errors)

        if is_valid:
            print("✓ 数据验证通过")
        else:
            print(f"⚠ 发现 {len(errors)} 个问题:")
            for i, error in enumerate(errors[:5], 1):
                print(f"  {i}. {error}")
            if len(errors) > 5:
                print(f"  ... 还有 {len(errors) - 5} 个问题")

        print()
        print(f"📊 置信度评分: {confidence * 100:.1f}%")

        if confidence >= 0.9:
            print("   评级: 优秀 ⭐⭐⭐⭐⭐")
        elif confidence >= 0.8:
            print("   评级: 良好 ⭐⭐⭐⭐")
        elif confidence >= 0.7:
            print("   评级: 合格 ⭐⭐⭐")
        else:
            print("   评级: 需检查 ⭐⭐")

        print()

        # 总结
        print("=" * 60)
        print("【测试总结】")
        print("=" * 60)
        print()
        print(f"✓ HTML解析:      成功")
        print(f"✓ 指标提取:      {len(valid_metrics)}/46 个")
        print(f"✓ 数据验证:      {'通过' if is_valid else '部分通过'}")
        print(f"✓ 置信度:        {confidence * 100:.1f}%")
        print()

        if confidence >= 0.7:
            print("🎉 测试成功！财报解析功能正常工作。")
        else:
            print("⚠ 测试完成，但置信度较低，建议检查数据。")

        print()

        return parsed_data, metrics

    except Exception as e:
        print(f"✗ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def format_number(value):
    """格式化数字"""
    if value is None:
        return 'N/A'

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f'${value / 1_000_000_000:,.2f}B'
    elif abs(value) >= 1_000_000:
        return f'${value / 1_000_000:,.2f}M'
    else:
        return f'${value:,.0f}'


def format_percent(value):
    """格式化百分比"""
    if value is None:
        return 'N/A'
    return f'{float(value) * 100:.2f}%'


def format_ratio(value):
    """格式化比率"""
    if value is None:
        return 'N/A'
    return f'{float(value):.2f}'


if __name__ == '__main__':
    import sys

    # 默认文件路径
    default_path = 'test_data/apple_10k.html'

    # 如果命令行提供了路径，使用命令行路径
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = default_path

    print()
    test_apple_10k(file_path)
    print()
