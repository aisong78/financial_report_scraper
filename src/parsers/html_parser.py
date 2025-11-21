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

        Args:
            text: 文本内容

        Returns:
            单位倍数
        """
        text_lower = text.lower()

        # 美股常见单位
        if 'in thousands' in text_lower or '(in thousands)' in text_lower:
            return 1_000
        elif 'in millions' in text_lower or '(in millions)' in text_lower:
            return 1_000_000
        elif 'in billions' in text_lower or '(in billions)' in text_lower:
            return 1_000_000_000
        else:
            # 默认假设是千为单位（SEC最常见）
            return 1_000

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
        keyword_map = {
            'revenue': 'revenue',
            'total revenue': 'revenue',
            'net sales': 'revenue',
            'cost of revenue': 'operating_cost',
            'cost of goods sold': 'operating_cost',
            'cogs': 'operating_cost',
            'operating income': 'operating_profit',
            'operating profit': 'operating_profit',
            'income before tax': 'total_profit',
            'pretax income': 'total_profit',
            'net income': 'net_profit',
            'net earnings': 'net_profit',
            'income tax': 'tax_expense',
            'tax expense': 'tax_expense',
            'selling, general': 'selling_expense',  # Selling, General & Administrative
            'research and development': 'rd_expense',
            'r&d': 'rd_expense',
        }

        # 提取行
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            # 第一列是指标名
            indicator_text = cells[0].get_text().strip().lower()

            # 查找匹配的关键词
            for keyword, field_name in keyword_map.items():
                if keyword in indicator_text:
                    # 尝试提取数值（通常在后面的列）
                    for cell in cells[1:]:
                        value = self.clean_value(cell.get_text())
                        if value is not None:
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

            indicator_text = cells[0].get_text().strip().lower()

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

            indicator_text = cells[0].get_text().strip().lower()

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
