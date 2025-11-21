"""
HTML财报解析器

支持美股SEC EDGAR格式的HTML财报
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from .base_parser import BaseParser


class HTMLParser(BaseParser):
    """HTML财报解析器（美股）"""

    def __init__(self):
        """初始化"""
        super().__init__()
        self.supported_formats = ['.html', '.htm']

        if BeautifulSoup is None:
            raise ImportError("请安装 beautifulsoup4: pip install beautifulsoup4 lxml")

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析HTML财报

        Args:
            file_path: HTML文件路径

        Returns:
            解析结果字典
        """
        # 验证文件
        if not self.validate_file(file_path):
            raise ValueError(f"无效的文件: {file_path}")

        result = {
            'income_statement': {},
            'balance_sheet': {},
            'cash_flow': {},
            'metadata': self.create_metadata('HTMLParser')
        }

        # 读取HTML
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'lxml')

        # 检测单位（美股通常以千或百万为单位）
        unit_text = soup.get_text()[:5000]  # 只检查前5000字符
        unit_multiplier = self._detect_us_unit(unit_text)

        # 提取所有表格
        tables = soup.find_all('table')

        for table in tables:
            # 识别表格类型
            statement_type = self._identify_table_type_html(table)

            if statement_type == 'income_statement':
                result['income_statement'].update(
                    self._parse_income_statement_html(table, unit_multiplier)
                )
            elif statement_type == 'balance_sheet':
                result['balance_sheet'].update(
                    self._parse_balance_sheet_html(table, unit_multiplier)
                )
            elif statement_type == 'cash_flow':
                result['cash_flow'].update(
                    self._parse_cash_flow_html(table, unit_multiplier)
                )

        # 计算置信度
        confidence = self._calculate_confidence(result)
        result['metadata']['confidence'] = confidence
        result['metadata']['unit_multiplier'] = unit_multiplier

        return result

    def _detect_us_unit(self, text: str) -> float:
        """
        检测美股报表单位

        优先检测"Amounts in"相关描述（用于金额单位）
        避免被"shares in thousands"等股数单位干扰

        Args:
            text: 文本内容

        Returns:
            单位倍数
        """
        text_lower = text.lower()

        # 优先检查明确的金额单位说明（"Amounts in..."）
        # 这些通常出现在表格底部或页脚
        if 'amounts in billions' in text_lower:
            return 1_000_000_000
        elif 'amounts in millions' in text_lower:
            return 1_000_000
        elif 'amounts in thousands' in text_lower:
            return 1_000

        # 检查常见的单位标记（按从大到小的顺序，优先匹配大单位）
        # 美股10-K通常用millions，偶尔用billions
        if 'in billions' in text_lower or '(in billions)' in text_lower:
            return 1_000_000_000
        elif 'in millions' in text_lower or '(in millions)' in text_lower:
            return 1_000_000
        elif 'in thousands' in text_lower or '(in thousands)' in text_lower:
            # 注意：如果只找到thousands，可能是股数单位
            # 但如果同时存在财务数据，默认认为是金额单位
            return 1_000
        else:
            # 默认假设是百万为单位（美股10-K最常见）
            return 1_000_000

    def _normalize_text(self, text: str) -> str:
        """
        规范化文本（用于关键词匹配）

        去除标点符号，统一为小写，方便关键词匹配

        Args:
            text: 原始文本

        Returns:
            规范化后的文本
        """
        # 转小写
        text = text.lower()
        # 移除常见标点符号（但保留空格和连字符）
        # 主要是去除撇号 ', 引号 ", 括号 (), 冒号 : 等
        text = text.replace("'", "").replace('"', '')
        text = text.replace('(', '').replace(')', '')
        text = text.replace(':', '')
        text = text.replace(',', '')
        return text.strip()

    def _identify_table_type_html(self, table) -> Optional[str]:
        """
        识别HTML表格类型

        Args:
            table: BeautifulSoup table对象

        Returns:
            表格类型
        """
        # 获取表格文本
        table_text = table.get_text().lower()

        # 利润表关键词（美股）
        income_keywords = [
            'income statement', 'statement of operations', 'statement of earnings',
            'revenue', 'net income', 'operating income', 'total revenue'
        ]

        # 资产负债表关键词
        balance_keywords = [
            'balance sheet', 'statement of financial position',
            'total assets', 'total liabilities', 'stockholders equity', 'shareholders equity'
        ]

        # 现金流量表关键词
        cashflow_keywords = [
            'cash flow', 'statement of cash flows',
            'operating activities', 'investing activities', 'financing activities'
        ]

        income_score = sum(1 for kw in income_keywords if kw in table_text)
        balance_score = sum(1 for kw in balance_keywords if kw in table_text)
        cashflow_score = sum(1 for kw in cashflow_keywords if kw in table_text)

        max_score = max(income_score, balance_score, cashflow_score)

        if max_score == 0:
            return None

        if income_score == max_score:
            return 'income_statement'
        elif balance_score == max_score:
            return 'balance_sheet'
        else:
            return 'cash_flow'

    def _parse_income_statement_html(self, table, multiplier: float = 1) -> Dict:
        """
        解析HTML格式的利润表

        Args:
            table: BeautifulSoup table对象
            multiplier: 单位倍数

        Returns:
            利润表指标字典
        """
        result = {}

        # 关键指标映射（英文 -> 字段名）
        # 注意：顺序很重要！更具体的关键词应该放在前面
        keyword_map = {
            # 营收（Revenue/Sales）
            'total net sales': 'revenue',  # Apple用的格式
            'total revenue': 'revenue',
            'net sales': 'revenue',
            'revenue': 'revenue',
            # 营业成本（Cost of Sales/COGS）
            'total cost of sales': 'operating_cost',  # Apple用的格式
            'cost of sales': 'operating_cost',
            'cost of revenue': 'operating_cost',
            'cost of goods sold': 'operating_cost',
            'cogs': 'operating_cost',
            # 毛利（Gross Margin/Profit）
            'gross margin': 'gross_profit',
            'gross profit': 'gross_profit',
            # 营业利润（Operating Income）
            'operating income': 'operating_profit',
            'operating profit': 'operating_profit',
            # 税前利润（Pretax Income）
            'income before provision for income taxes': 'total_profit',  # Apple格式
            'income before tax': 'total_profit',
            'pretax income': 'total_profit',
            # 净利润（Net Income）
            'net income': 'net_profit',
            'net earnings': 'net_profit',
            # 税费（Tax Expense）
            'provision for income taxes': 'tax_expense',  # Apple格式
            'income tax expense': 'tax_expense',
            'income tax': 'tax_expense',
            'tax expense': 'tax_expense',
            # 销售及管理费用（SG&A）
            'selling, general and administrative': 'selling_expense',
            'selling, general': 'selling_expense',
            # 研发费用（R&D）
            'research and development': 'rd_expense',
            'r&d expense': 'rd_expense',
            'r&d': 'rd_expense',
            # 每股收益（EPS）
            'diluted': 'eps_diluted',  # 稀释每股收益
            'basic': 'eps_basic',      # 基本每股收益
        }

        # 提取行
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            # 第一列是指标名（规范化处理，去除标点）
            indicator_text = self._normalize_text(cells[0].get_text())

            # 查找匹配的关键词
            for keyword, field_name in keyword_map.items():
                if keyword in indicator_text:
                    # 尝试提取数值（通常在后面的列）
                    for cell in cells[1:]:
                        value = self.clean_value(cell.get_text())
                        if value is not None:
                            # EPS是"per share"值，不需要乘以单位倍数
                            if field_name in ['eps_basic', 'eps_diluted']:
                                result[field_name] = value
                            else:
                                result[field_name] = value * multiplier
                            break
                    break

        return result

    def _parse_balance_sheet_html(self, table, multiplier: float = 1) -> Dict:
        """
        解析HTML格式的资产负债表

        Args:
            table: BeautifulSoup table对象
            multiplier: 单位倍数

        Returns:
            资产负债表指标字典
        """
        result = {}

        # 关键指标映射
        keyword_map = {
            'total assets': 'total_assets',
            'total current assets': 'current_assets',
            'current assets': 'current_assets',
            'non-current assets': 'non_current_assets',
            'noncurrent assets': 'non_current_assets',
            'cash and cash equivalents': 'cash_and_equivalents',
            'cash': 'cash_and_equivalents',
            'accounts receivable': 'accounts_receivable',
            'receivables': 'accounts_receivable',
            'inventory': 'inventory',
            'inventories': 'inventory',
            'property, plant': 'fixed_assets',  # Property, Plant & Equipment
            'fixed assets': 'fixed_assets',
            'intangible assets': 'intangible_assets',
            'goodwill': 'goodwill',
            'total liabilities': 'total_liabilities',
            'total current liabilities': 'current_liabilities',
            'current liabilities': 'current_liabilities',
            'non-current liabilities': 'non_current_liabilities',
            'noncurrent liabilities': 'non_current_liabilities',
            'short-term debt': 'short_term_borrowing',
            'short-term borrowings': 'short_term_borrowing',
            'long-term debt': 'long_term_borrowing',
            'long-term borrowings': 'long_term_borrowing',
            'accounts payable': 'accounts_payable',
            'payables': 'accounts_payable',
            'total equity': 'total_equity',
            'stockholders equity': 'total_equity',
            'shareholders equity': 'total_equity',
            'total stockholders': 'total_equity',
            'common stock': 'share_capital',
            'retained earnings': 'retained_earnings',
        }

        # 提取行
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            # 规范化处理（去除标点）
            indicator_text = self._normalize_text(cells[0].get_text())

            # 跳过复合行（包含"and"的通常是平衡行，如"total liabilities and equity"）
            # 但"cash and cash equivalents"等是例外，所以只跳过total开头+and的组合
            if indicator_text.startswith('total') and ' and ' in indicator_text:
                # 检查是否是平衡行（如"total liabilities and equity"）
                if ('liabilities and' in indicator_text or
                    'assets and' in indicator_text):
                    continue

            for keyword, field_name in keyword_map.items():
                if keyword in indicator_text:
                    for cell in cells[1:]:
                        value = self.clean_value(cell.get_text())
                        if value is not None:
                            result[field_name] = value * multiplier
                            break
                    break

        return result

    def _parse_cash_flow_html(self, table, multiplier: float = 1) -> Dict:
        """
        解析HTML格式的现金流量表

        Args:
            table: BeautifulSoup table对象
            multiplier: 单位倍数

        Returns:
            现金流量表指标字典
        """
        result = {}

        # 关键指标映射
        keyword_map = {
            'cash provided by operating': 'operating_cash_flow',
            'net cash from operating': 'operating_cash_flow',
            'operating activities': 'operating_cash_flow',
            'cash used in investing': 'investing_cash_flow',
            'net cash from investing': 'investing_cash_flow',
            'investing activities': 'investing_cash_flow',
            'cash provided by financing': 'financing_cash_flow',
            'net cash from financing': 'financing_cash_flow',
            'financing activities': 'financing_cash_flow',
            'net increase in cash': 'net_cash_flow',
            'net change in cash': 'net_cash_flow',
        }

        # 提取行
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            # 规范化处理（去除标点）
            indicator_text = self._normalize_text(cells[0].get_text())

            for keyword, field_name in keyword_map.items():
                if keyword in indicator_text:
                    for cell in cells[1:]:
                        value = self.clean_value(cell.get_text())
                        if value is not None:
                            result[field_name] = value * multiplier
                            break
                    break

        return result

    def _calculate_confidence(self, result: Dict) -> float:
        """
        计算解析置信度

        Args:
            result: 解析结果

        Returns:
            置信度 (0-1)
        """
        # 必需指标列表
        required_fields = {
            'income_statement': ['revenue', 'net_profit'],
            'balance_sheet': ['total_assets', 'total_liabilities', 'total_equity'],
            'cash_flow': ['operating_cash_flow']
        }

        total_required = 0
        found_required = 0

        for statement_type, fields in required_fields.items():
            for field in fields:
                total_required += 1
                if result.get(statement_type, {}).get(field) is not None:
                    found_required += 1

        if total_required == 0:
            return 0.0

        base_confidence = found_required / total_required
        return round(base_confidence, 4)


# 便捷函数

def parse_html_report(file_path: str) -> Dict[str, Any]:
    """
    解析HTML财报（便捷函数）

    Args:
        file_path: HTML文件路径

    Returns:
        解析结果
    """
    parser = HTMLParser()
    return parser.parse(file_path)


if __name__ == '__main__':
    # 测试
    import sys

    if len(sys.argv) < 2:
        print("用法: python html_parser.py <html_file>")
        sys.exit(1)

    html_file = sys.argv[1]
    result = parse_html_report(html_file)

    print("=" * 60)
    print("HTML解析结果")
    print("=" * 60)

    for statement_type, data in result.items():
        if statement_type == 'metadata':
            continue
        print(f"\n{statement_type}:")
        for key, value in data.items():
            print(f"  {key}: {value}")

    print(f"\n置信度: {result['metadata']['confidence']}")
