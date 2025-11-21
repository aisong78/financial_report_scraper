"""
PDF财报解析器

支持A股和港股PDF格式财报
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from .base_parser import BaseParser


class PDFParser(BaseParser):
    """PDF财报解析器（中文）"""

    def __init__(self):
        """初始化"""
        super().__init__()
        self.supported_formats = ['.pdf']

        if pdfplumber is None:
            raise ImportError("请安装 pdfplumber: pip install pdfplumber")

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析PDF财报

        Args:
            file_path: PDF文件路径

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
            'metadata': self.create_metadata('PDFParser')
        }

        # 打开PDF
        with pdfplumber.open(file_path) as pdf:
            # 提取所有表格
            all_tables = []
            unit_multiplier = 1

            for page in pdf.pages:
                # 提取页面文本（用于检测单位）
                page_text = page.extract_text() or ''

                # 检测单位
                multiplier = self.detect_unit_multiplier(page_text)
                if multiplier > unit_multiplier:
                    unit_multiplier = multiplier

                # 提取表格
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)

            # 解析表格
            for table in all_tables:
                if not table:
                    continue

                # 识别表格类型
                statement_type = self._identify_table_type(table)

                if statement_type == 'income_statement':
                    result['income_statement'].update(
                        self._parse_income_statement(table, unit_multiplier)
                    )
                elif statement_type == 'balance_sheet':
                    result['balance_sheet'].update(
                        self._parse_balance_sheet(table, unit_multiplier)
                    )
                elif statement_type == 'cash_flow':
                    result['cash_flow'].update(
                        self._parse_cash_flow(table, unit_multiplier)
                    )

        # 计算置信度
        confidence = self._calculate_confidence(result)
        result['metadata']['confidence'] = confidence
        result['metadata']['unit_multiplier'] = unit_multiplier

        return result

    def _identify_table_type(self, table: List[List]) -> Optional[str]:
        """
        识别表格类型

        Args:
            table: 表格数据（二维列表）

        Returns:
            表格类型
        """
        # 将表格转为文本
        table_text = ' '.join([
            ' '.join([str(cell) if cell else '' for cell in row])
            for row in table
        ]).lower()

        # 利润表关键词
        if any(keyword in table_text for keyword in ['利润表', '损益表', '营业收入', '净利润']):
            return 'income_statement'

        # 资产负债表关键词
        if any(keyword in table_text for keyword in ['资产负债表', '总资产', '流动资产', '股东权益']):
            return 'balance_sheet'

        # 现金流量表关键词
        if any(keyword in table_text for keyword in ['现金流量表', '经营活动产生的现金流量', '投资活动']):
            return 'cash_flow'

        return None

    def _parse_income_statement(self, table: List[List], multiplier: float = 1) -> Dict:
        """
        解析利润表

        Args:
            table: 表格数据
            multiplier: 单位倍数

        Returns:
            利润表指标字典
        """
        result = {}

        # 关键指标映射（中文 -> 字段名）
        keyword_map = {
            '营业收入': 'revenue',
            '营业总收入': 'revenue',
            '营业成本': 'operating_cost',
            '营业总成本': 'operating_cost',
            '销售费用': 'selling_expense',
            '管理费用': 'admin_expense',
            '财务费用': 'finance_expense',
            '研发费用': 'rd_expense',
            '营业利润': 'operating_profit',
            '利润总额': 'total_profit',
            '净利润': 'net_profit',
            '归属于母公司': 'net_profit',  # 归属于母公司所有者的净利润
            '所得税费用': 'tax_expense',
        }

        # 遍历表格行
        for row in table:
            if not row or len(row) < 2:
                continue

            # 第一列是指标名称
            indicator = str(row[0]).strip() if row[0] else ''

            # 查找匹配的关键词
            for keyword, field_name in keyword_map.items():
                if keyword in indicator:
                    # 尝试提取数值（通常在第二列或第三列）
                    for col_idx in range(1, len(row)):
                        value = self.clean_value(row[col_idx])
                        if value is not None:
                            result[field_name] = value * multiplier
                            break
                    break

        return result

    def _parse_balance_sheet(self, table: List[List], multiplier: float = 1) -> Dict:
        """
        解析资产负债表

        Args:
            table: 表格数据
            multiplier: 单位倍数

        Returns:
            资产负债表指标字典
        """
        result = {}

        # 关键指标映射
        keyword_map = {
            '资产总计': 'total_assets',
            '总资产': 'total_assets',
            '流动资产合计': 'current_assets',
            '流动资产': 'current_assets',
            '非流动资产合计': 'non_current_assets',
            '非流动资产': 'non_current_assets',
            '货币资金': 'cash_and_equivalents',
            '应收账款': 'accounts_receivable',
            '存货': 'inventory',
            '固定资产': 'fixed_assets',
            '无形资产': 'intangible_assets',
            '商誉': 'goodwill',
            '负债合计': 'total_liabilities',
            '总负债': 'total_liabilities',
            '流动负债合计': 'current_liabilities',
            '流动负债': 'current_liabilities',
            '非流动负债合计': 'non_current_liabilities',
            '非流动负债': 'non_current_liabilities',
            '短期借款': 'short_term_borrowing',
            '长期借款': 'long_term_borrowing',
            '应付账款': 'accounts_payable',
            '股东权益合计': 'total_equity',
            '所有者权益合计': 'total_equity',
            '股本': 'share_capital',
            '未分配利润': 'retained_earnings',
        }

        # 遍历表格
        for row in table:
            if not row or len(row) < 2:
                continue

            indicator = str(row[0]).strip() if row[0] else ''

            for keyword, field_name in keyword_map.items():
                if keyword in indicator:
                    for col_idx in range(1, len(row)):
                        value = self.clean_value(row[col_idx])
                        if value is not None:
                            result[field_name] = value * multiplier
                            break
                    break

        return result

    def _parse_cash_flow(self, table: List[List], multiplier: float = 1) -> Dict:
        """
        解析现金流量表

        Args:
            table: 表格数据
            multiplier: 单位倍数

        Returns:
            现金流量表指标字典
        """
        result = {}

        # 关键指标映射
        keyword_map = {
            '经营活动产生的现金流量净额': 'operating_cash_flow',
            '经营活动现金流量净额': 'operating_cash_flow',
            '投资活动产生的现金流量净额': 'investing_cash_flow',
            '投资活动现金流量净额': 'investing_cash_flow',
            '筹资活动产生的现金流量净额': 'financing_cash_flow',
            '筹资活动现金流量净额': 'financing_cash_flow',
            '现金及现金等价物净增加额': 'net_cash_flow',
        }

        # 遍历表格
        for row in table:
            if not row or len(row) < 2:
                continue

            indicator = str(row[0]).strip() if row[0] else ''

            for keyword, field_name in keyword_map.items():
                if keyword in indicator:
                    for col_idx in range(1, len(row)):
                        value = self.clean_value(row[col_idx])
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

        # 基础置信度
        if total_required == 0:
            return 0.0

        base_confidence = found_required / total_required

        # 如果所有必需字段都找到，置信度为1.0
        # 否则按比例计算
        return round(base_confidence, 4)


# 便捷函数

def parse_pdf_report(file_path: str) -> Dict[str, Any]:
    """
    解析PDF财报（便捷函数）

    Args:
        file_path: PDF文件路径

    Returns:
        解析结果
    """
    parser = PDFParser()
    return parser.parse(file_path)


if __name__ == '__main__':
    # 测试
    import sys

    if len(sys.argv) < 2:
        print("用法: python pdf_parser.py <pdf_file>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    result = parse_pdf_report(pdf_file)

    print("=" * 60)
    print("PDF解析结果")
    print("=" * 60)

    for statement_type, data in result.items():
        if statement_type == 'metadata':
            continue
        print(f"\n{statement_type}:")
        for key, value in data.items():
            print(f"  {key}: {value}")

    print(f"\n置信度: {result['metadata']['confidence']}")
