"""
演示财报解析功能

展示如何从财报数据中提取和计算46个财务指标
"""

from src.extractors import MetricExtractor
from src.extractors.validator import MetricValidator
from datetime import datetime
from decimal import Decimal


def create_sample_report_data():
    """
    创建模拟的财报数据（基于真实财报结构）
    这里使用小米集团2023年报的简化数据作为示例
    """
    return {
        'income_statement': {
            # 损益表核心数据
            'revenue': Decimal('270898000000'),  # 营业收入：2708.98亿元
            'operating_cost': Decimal('230000000000'),  # 营业成本：2300亿元
            'gross_profit': Decimal('40898000000'),  # 毛利润
            'selling_expense': Decimal('8500000000'),  # 销售费用：85亿
            'admin_expense': Decimal('3200000000'),  # 管理费用：32亿
            'rd_expense': Decimal('18700000000'),  # 研发费用：187亿
            'finance_expense': Decimal('1200000000'),  # 财务费用：12亿
            'operating_profit': Decimal('23000000000'),  # 营业利润：230亿
            'total_profit': Decimal('24500000000'),  # 利润总额：245亿
            'tax_expense': Decimal('5200000000'),  # 所得税：52亿
            'net_profit': Decimal('19300000000'),  # 净利润：193亿
            'eps': Decimal('0.77'),  # 每股收益：0.77元
            'eps_diluted': Decimal('0.75'),  # 稀释每股收益
        },
        'balance_sheet': {
            # 资产负债表核心数据
            'total_assets': Decimal('395000000000'),  # 总资产：3950亿
            'current_assets': Decimal('280000000000'),  # 流动资产：2800亿
            'non_current_assets': Decimal('115000000000'),  # 非流动资产：1150亿
            'cash_and_equivalents': Decimal('140000000000'),  # 现金：1400亿
            'accounts_receivable': Decimal('45000000000'),  # 应收账款：450亿
            'inventory': Decimal('55000000000'),  # 存货：550亿
            'fixed_assets': Decimal('26000000000'),  # 固定资产：260亿
            'intangible_assets': Decimal('8500000000'),  # 无形资产：85亿
            'goodwill': Decimal('3200000000'),  # 商誉：32亿

            'total_liabilities': Decimal('245000000000'),  # 总负债：2450亿
            'current_liabilities': Decimal('195000000000'),  # 流动负债：1950亿
            'non_current_liabilities': Decimal('50000000000'),  # 非流动负债：500亿
            'short_term_borrowing': Decimal('28000000000'),  # 短期借款：280亿
            'long_term_borrowing': Decimal('12000000000'),  # 长期借款：120亿
            'accounts_payable': Decimal('115000000000'),  # 应付账款：1150亿

            'total_equity': Decimal('150000000000'),  # 股东权益：1500亿
            'share_capital': Decimal('2500000000'),  # 股本：25亿股
            'retained_earnings': Decimal('95000000000'),  # 未分配利润：950亿
        },
        'cash_flow': {
            # 现金流量表核心数据
            'operating_cash_flow': Decimal('25000000000'),  # 经营现金流：250亿
            'investing_cash_flow': Decimal('-15000000000'),  # 投资现金流：-150亿（负数表示投资支出）
            'financing_cash_flow': Decimal('-8000000000'),  # 筹资现金流：-80亿
            'net_cash_flow': Decimal('2000000000'),  # 现金净增加额：20亿
        }
    }


def format_number(value, unit='亿元', decimals=2):
    """格式化数字显示"""
    if value is None:
        return 'N/A'

    if isinstance(value, (Decimal, float)):
        if unit == '亿元':
            return f'{float(value) / 100000000:,.{decimals}f} {unit}'
        elif unit == '%':
            return f'{float(value) * 100:.{decimals}f}%'
        else:
            return f'{float(value):.{decimals}f}'
    return str(value)


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          财报解析演示 - 小米集团（示例数据）            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # 1. 创建模拟财报数据
    print("【步骤 1】加载财报数据")
    print("=" * 60)
    parsed_data = create_sample_report_data()
    print("✓ 财报数据已加载（基于小米集团2023年报简化数据）")
    print()

    # 2. 提取指标
    print("【步骤 2】提取和计算46个财务指标")
    print("=" * 60)

    extractor = MetricExtractor()
    stock_id = 1  # 模拟股票ID
    report_date = datetime(2023, 12, 31)  # 2023年年报

    metrics = extractor.extract(parsed_data, stock_id, report_date)
    print(f"✓ 成功提取 {len([v for v in metrics.values() if v is not None])} 个有效指标")
    print()

    # 3. 展示核心指标（P0 - 15个）
    print("【步骤 3】P0 核心指标（15个）")
    print("=" * 60)
    print()

    print("📊 损益表指标：")
    print(f"  营业收入:        {format_number(metrics.get('revenue'))}")
    print(f"  净利润:          {format_number(metrics.get('net_profit'))}")
    print(f"  营业利润:        {format_number(metrics.get('operating_profit'))}")
    print(f"  EPS (每股收益):  {format_number(metrics.get('eps'), '元', 2)}")
    print()

    print("💰 资产负债表指标：")
    print(f"  总资产:          {format_number(metrics.get('total_assets'))}")
    print(f"  总负债:          {format_number(metrics.get('total_liabilities'))}")
    print(f"  股东权益:        {format_number(metrics.get('total_equity'))}")
    print(f"  流动资产:        {format_number(metrics.get('current_assets'))}")
    print(f"  流动负债:        {format_number(metrics.get('current_liabilities'))}")
    print()

    print("💵 现金流指标：")
    print(f"  经营现金流:      {format_number(metrics.get('operating_cash_flow'))}")
    print()

    print("📈 关键比率（计算得出）：")
    print(f"  毛利率:          {format_number(metrics.get('gross_margin'), '%')}")
    print(f"  净利率:          {format_number(metrics.get('net_margin'), '%')}")
    print(f"  资产负债率:      {format_number(metrics.get('asset_liability_ratio'), '%')}")
    print(f"  ROE (净资产收益率): {format_number(metrics.get('roe'), '%')}")
    print()

    # 4. 展示补充指标（P1 - 31个）
    print("【步骤 4】P1 补充指标（部分展示）")
    print("=" * 60)
    print()

    print("💼 运营效率：")
    print(f"  流动比率:        {format_number(metrics.get('current_ratio'), '倍', 2)}")
    print(f"  速动比率:        {format_number(metrics.get('quick_ratio'), '倍', 2)}")
    print(f"  资产周转率:      {format_number(metrics.get('asset_turnover'), '次', 2)}")
    print(f"  存货周转率:      {format_number(metrics.get('inventory_turnover'), '次', 2)}")
    print()

    print("💡 研发投入：")
    print(f"  研发费用:        {format_number(metrics.get('rd_expense'))}")
    print(f"  研发费用率:      {format_number(metrics.get('rd_ratio'), '%')}")
    print()

    print("💸 现金流质量：")
    print(f"  自由现金流:      {format_number(metrics.get('free_cash_flow'))}")
    print(f"  FCF/营收:        {format_number(metrics.get('fcf_to_revenue'), '%')}")
    print(f"  经营现金流/净利润: {format_number(metrics.get('ocf_to_net_profit'), '倍', 2)}")
    print()

    print("💎 资产结构：")
    print(f"  现金及等价物:    {format_number(metrics.get('cash_and_equivalents'))}")
    print(f"  应收账款:        {format_number(metrics.get('accounts_receivable'))}")
    print(f"  存货:            {format_number(metrics.get('inventory'))}")
    print(f"  固定资产:        {format_number(metrics.get('fixed_assets'))}")
    print(f"  商誉:            {format_number(metrics.get('goodwill'))}")
    print()

    # 5. 数据验证
    print("【步骤 5】数据验证和置信度评分")
    print("=" * 60)

    validator = MetricValidator()
    is_valid, errors = validator.validate(metrics)
    confidence = validator.calculate_confidence_score(metrics, errors)

    if is_valid:
        print("✓ 数据验证通过")
    else:
        print(f"⚠ 发现 {len(errors)} 个问题:")
        for error in errors[:5]:  # 只显示前5个
            print(f"  - {error}")

    print(f"\n📊 置信度评分: {confidence * 100:.1f}%")
    if confidence >= 0.9:
        print("   评级: 优秀 ⭐⭐⭐⭐⭐")
    elif confidence >= 0.8:
        print("   评级: 良好 ⭐⭐⭐⭐")
    elif confidence >= 0.7:
        print("   评级: 合格 ⭐⭐⭐")
    else:
        print("   评级: 需检查 ⭐⭐")
    print()

    # 6. 总结
    print("【总结】")
    print("=" * 60)
    print()
    print("本演示展示了程序的核心能力：")
    print("✓ 从财报中提取46个财务指标（P0 + P1）")
    print("✓ 自动计算衍生指标（毛利率、ROE、周转率等）")
    print("✓ 数据验证和一致性检查")
    print("✓ 置信度评分（判断数据质量）")
    print()
    print("💡 小米集团财务特点（基于示例数据）：")
    print(f"  • 营收规模: {format_number(metrics.get('revenue'))}")
    print(f"  • 盈利能力: 净利率 {format_number(metrics.get('net_margin'), '%')}，ROE {format_number(metrics.get('roe'), '%')}")
    print(f"  • 研发投入: {format_number(metrics.get('rd_ratio'), '%')} 的营收用于研发")
    print(f"  • 现金储备: {format_number(metrics.get('cash_and_equivalents'))} 现金")
    print(f"  • 财务健康: 流动比率 {format_number(metrics.get('current_ratio'), '倍', 2)}")
    print()
    print("🚀 下一步：Phase 2 会基于这些指标进行智能分析，")
    print("   给出投资建议（买入/持有/卖出）")
    print()
    print("=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
