"""
美股数据处理流程演示

展示英文财报如何被提取成中文指标（无需翻译）
"""

from decimal import Decimal


def demo_html_parsing():
    """演示HTML解析（模拟）"""
    print("=" * 60)
    print("【步骤 1】从英文财报中提取数据")
    print("=" * 60)
    print()

    # 模拟美股10-K财报的HTML内容
    html_content = """
    <table>
        <tr><th colspan="2">CONSOLIDATED STATEMENTS OF OPERATIONS</th></tr>
        <tr><td>Net sales</td><td>383,285</td></tr>
        <tr><td>Cost of sales</td><td>214,137</td></tr>
        <tr><td>Gross margin</td><td>169,148</td></tr>
        <tr><td>Operating income</td><td>114,301</td></tr>
        <tr><td>Net income</td><td>96,995</td></tr>
    </table>

    <p><i>Amounts in millions</i></p>
    """

    print("📄 原始英文财报片段:")
    print(html_content)
    print()

    # 解析器工作
    print("🔍 HTMLParser 解析中...")
    print()
    print("识别到的英文关键词:")
    print("  - 'Net sales' → 映射到 'revenue'")
    print("  - 'Cost of sales' → 映射到 'operating_cost'")
    print("  - 'Net income' → 映射到 'net_profit'")
    print("  - 'Amounts in millions' → 单位倍数 = 1,000,000")
    print()

    # 提取结果（只有数字！）
    extracted_data = {
        'revenue': 383285 * 1_000_000,           # 3832.85亿美元
        'operating_cost': 214137 * 1_000_000,    # 2141.37亿美元
        'net_profit': 96995 * 1_000_000,         # 969.95亿美元
    }

    print("✓ 提取完成！")
    print()
    return extracted_data


def demo_data_storage(data):
    """演示数据存储"""
    print("=" * 60)
    print("【步骤 2】存入数据库（中文字段名）")
    print("=" * 60)
    print()

    print("📊 FinancialMetric 表结构（中文注释）:")
    print()
    print("  字段名             | 数值                    | 说明")
    print("  ------------------|------------------------|----------")
    print(f"  revenue           | {data['revenue']:,}  | 营业收入")
    print(f"  operating_cost    | {data['operating_cost']:,}  | 营业成本")
    print(f"  net_profit        | {data['net_profit']:,}  | 净利润")
    print()

    print("💡 注意：数据库字段名是英文，但有中文注释")
    print("   这是标准做法，便于代码维护")
    print()


def demo_metric_calculation(data):
    """演示指标计算"""
    print("=" * 60)
    print("【步骤 3】计算财务指标（中文展示）")
    print("=" * 60)
    print()

    # 计算指标
    revenue = data['revenue']
    cost = data['operating_cost']
    profit = data['net_profit']

    gross_margin = (revenue - cost) / revenue
    net_margin = profit / revenue

    print("📈 计算结果:")
    print()
    print(f"  营业收入:  ${revenue / 1_000_000_000:.2f} 亿美元")
    print(f"  营业成本:  ${cost / 1_000_000_000:.2f} 亿美元")
    print(f"  净利润:    ${profit / 1_000_000_000:.2f} 亿美元")
    print()
    print(f"  毛利率:    {gross_margin * 100:.2f}%")
    print(f"  净利率:    {net_margin * 100:.2f}%")
    print()


def demo_user_display():
    """演示用户界面显示"""
    print("=" * 60)
    print("【步骤 4】用户界面展示（完全中文）")
    print("=" * 60)
    print()

    print("📱 给用户看到的内容:")
    print()
    print("┌─────────────────────────────────────┐")
    print("│  苹果公司 (AAPL) - 2023年年报        │")
    print("├─────────────────────────────────────┤")
    print("│  营业收入:     3,832.85 亿美元       │")
    print("│  净利润:         969.95 亿美元       │")
    print("│  毛利率:          44.13%            │")
    print("│  净利率:          25.31%            │")
    print("│  ROE:             28.5%             │")
    print("│                                     │")
    print("│  💡 评分: 85分 (优秀)                │")
    print("│  📈 建议: 买入                       │")
    print("└─────────────────────────────────────┘")
    print()


def demo_translation_comparison():
    """对比：需要翻译 vs 不需要翻译"""
    print("=" * 60)
    print("【对比】什么需要翻译？什么不需要？")
    print("=" * 60)
    print()

    print("❌ 不需要翻译的内容:")
    print()
    print("1. 财务数据（数字）")
    print("   原文: Net sales: $383,285 million")
    print("   处理: 直接提取 383285000000")
    print()

    print("2. 表格标题（通过关键词识别）")
    print("   原文: CONSOLIDATED STATEMENTS OF OPERATIONS")
    print("   处理: 识别为 'income_statement'（利润表）")
    print()

    print("3. 财务指标计算")
    print("   全是数学运算，无需翻译")
    print()

    print("✅ 可能需要翻译的内容（可选功能）:")
    print()
    print("1. 管理层讨论与分析（MD&A）")
    print("   原文: 'The Company's net sales increased due to...'")
    print("   翻译: '公司的净销售额增加是由于...'")
    print("   → 这是文字分析，可以用AI翻译")
    print()

    print("2. 风险披露")
    print("   原文: 'Risk Factors: The Company faces risks...'")
    print("   翻译: '风险因素：公司面临的风险...'")
    print()

    print("3. 脚注说明")
    print("   原文: 'Amounts in millions except per share'")
    print("   翻译: '金额以百万为单位，每股数据除外'")
    print()


def demo_future_translation():
    """演示未来的翻译功能（可选）"""
    print("=" * 60)
    print("【未来功能】AI智能翻译（Phase 3可选）")
    print("=" * 60)
    print()

    print("如果你需要翻译MD&A等文字内容，可以这样实现:")
    print()
    print("```python")
    print("def translate_mda_section(english_text: str) -> str:")
    print('    """使用Claude API翻译"""')
    print("    ")
    print("    # 调用AI翻译")
    print('    prompt = f"将以下财报MD&A翻译成中文：\\n\\n{english_text}"')
    print("    response = claude_api.translate(prompt)")
    print("    ")
    print("    return response.chinese_text")
    print("```")
    print()

    print("优点:")
    print("  ✓ 准确理解财务术语")
    print("  ✓ 保持专业性")
    print("  ✓ 上下文连贯")
    print()

    print("成本:")
    print("  - Claude API: ~$0.01/1000字")
    print("  - 一份MD&A约5000-10000字")
    print("  - 每份财报翻译成本: $0.05-0.10")
    print()


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     美股数据处理流程演示 - 无需翻译！                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # 步骤1: 解析英文HTML
    data = demo_html_parsing()

    # 步骤2: 存储数据
    demo_data_storage(data)

    # 步骤3: 计算指标
    demo_metric_calculation(data)

    # 步骤4: 用户界面
    demo_user_display()

    # 对比说明
    demo_translation_comparison()

    # 未来功能
    demo_future_translation()

    print("=" * 60)
    print("【总结】")
    print("=" * 60)
    print()
    print("🎯 核心观点:")
    print("  1. 财务数据分析 = 数字运算，不需要翻译")
    print("  2. 英文关键词识别 → 提取数字 → 中文展示")
    print("  3. 翻译是可选功能，用于阅读原文（Phase 3）")
    print()
    print("💡 建议:")
    print("  - Phase 1-2: 不翻译，专注数据准确性")
    print("  - Phase 3+: 可选添加AI翻译（MD&A等文字内容）")
    print()
    print("💰 成本对比:")
    print("  - 不翻译: 免费，实时")
    print("  - AI翻译: ~$0.1/份，需几秒")
    print()


if __name__ == '__main__':
    main()
