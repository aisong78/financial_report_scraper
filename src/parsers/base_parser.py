"""
财报解析器基类
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class BaseParser(ABC):
    """
    财报解析器基类

    所有解析器都继承此类并实现parse方法
    """

    def __init__(self):
        """初始化解析器"""
        self.supported_formats = []

    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析财报文件

        Args:
            file_path: 财报文件路径

        Returns:
            解析结果字典，包含三大报表数据

        格式：
        {
            'income_statement': {  # 利润表
                'revenue': 100000,
                'operating_cost': 60000,
                'net_profit': 20000,
                ...
            },
            'balance_sheet': {  # 资产负债表
                'total_assets': 500000,
                'total_liabilities': 300000,
                'total_equity': 200000,
                ...
            },
            'cash_flow': {  # 现金流量表
                'operating_cash_flow': 30000,
                'investing_cash_flow': -10000,
                'financing_cash_flow': 5000,
                ...
            },
            'metadata': {  # 元数据
                'report_date': '2024-12-31',
                'company_name': '贵州茅台',
                'report_type': 'annual',
                'parser': 'PDFParser',
                'parse_time': '2024-xx-xx',
                'confidence': 0.95
            }
        }
        """
        pass

    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否存在且格式正确

        Args:
            file_path: 文件路径

        Returns:
            是否有效
        """
        path = Path(file_path)

        # 检查文件是否存在
        if not path.exists():
            return False

        # 检查文件后缀
        if self.supported_formats:
            if path.suffix.lower() not in self.supported_formats:
                return False

        # 检查文件大小（不能为空，不能超过100MB）
        if path.stat().st_size == 0:
            return False

        if path.stat().st_size > 100 * 1024 * 1024:  # 100MB
            return False

        return True

    def clean_value(self, value: Any) -> Optional[float]:
        """
        清洗数值

        Args:
            value: 原始值（可能包含逗号、单位等）

        Returns:
            清洗后的数值
        """
        if value is None:
            return None

        # 转字符串
        if not isinstance(value, str):
            value = str(value)

        # 移除常见的非数字字符
        value = value.strip()
        value = value.replace(',', '')  # 移除千位分隔符
        value = value.replace('¥', '')
        value = value.replace('$', '')
        value = value.replace('元', '')
        value = value.replace(' ', '')

        # 尝试转换
        try:
            # 处理负数（括号表示）
            if value.startswith('(') and value.endswith(')'):
                value = '-' + value[1:-1]

            return float(value)
        except (ValueError, TypeError):
            return None

    def detect_unit_multiplier(self, text: str) -> float:
        """
        检测金额单位

        Args:
            text: 包含单位的文本（如"单位：万元"）

        Returns:
            倍数（万元=10000，亿元=100000000）
        """
        text = text.lower()

        if '亿' in text:
            return 100_000_000
        elif '万' in text or '千' in text:
            return 10_000
        elif 'million' in text:
            return 1_000_000
        elif 'billion' in text:
            return 1_000_000_000
        else:
            return 1

    def extract_tables(self, content: Any) -> List[Dict]:
        """
        提取表格

        子类可以重写此方法实现特定的表格提取逻辑

        Args:
            content: 文件内容

        Returns:
            表格列表
        """
        return []

    def identify_statement_type(self, table: Dict) -> Optional[str]:
        """
        识别表格类型（利润表、资产负债表、现金流量表）

        Args:
            table: 表格数据

        Returns:
            表格类型：income_statement, balance_sheet, cash_flow, 或 None
        """
        # 转换为文本进行关键词匹配
        text = str(table).lower()

        # 利润表关键词
        income_keywords = ['利润表', 'income statement', '营业收入', 'revenue', '净利润', 'net profit']
        balance_keywords = ['资产负债表', 'balance sheet', '总资产', 'total assets', '股东权益', 'equity']
        cashflow_keywords = ['现金流量表', 'cash flow', '经营活动', 'operating activities', '投资活动']

        income_score = sum(1 for keyword in income_keywords if keyword in text)
        balance_score = sum(1 for keyword in balance_keywords if keyword in text)
        cashflow_score = sum(1 for keyword in cashflow_keywords if keyword in text)

        # 选择得分最高的
        max_score = max(income_score, balance_score, cashflow_score)

        if max_score == 0:
            return None

        if income_score == max_score:
            return 'income_statement'
        elif balance_score == max_score:
            return 'balance_sheet'
        else:
            return 'cash_flow'

    def create_metadata(self, parser_name: str, confidence: float = 1.0) -> Dict[str, Any]:
        """
        创建元数据

        Args:
            parser_name: 解析器名称
            confidence: 置信度

        Returns:
            元数据字典
        """
        return {
            'parser': parser_name,
            'parse_time': datetime.now().isoformat(),
            'confidence': confidence
        }
