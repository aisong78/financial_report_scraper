"""
财务指标验证器

验证提取的指标是否合理、一致
"""

from typing import Dict, List, Tuple
from ..utils.logger import get_logger


class MetricValidator:
    """指标验证器"""

    def __init__(self):
        """初始化"""
        self.logger = get_logger()

    def validate(self, metrics: Dict) -> Tuple[bool, List[str]]:
        """
        验证指标合理性

        Args:
            metrics: 指标字典

        Returns:
            (是否通过, 错误列表)
        """
        errors = []

        # 1. 必填字段检查
        errors.extend(self._check_required_fields(metrics))

        # 2. 数值范围检查
        errors.extend(self._check_value_ranges(metrics))

        # 3. 逻辑一致性检查
        errors.extend(self._check_logical_consistency(metrics))

        # 4. 比率合理性检查
        errors.extend(self._check_ratio_reasonability(metrics))

        is_valid = len(errors) == 0

        if not is_valid:
            self.logger.warning(f"指标验证失败，共 {len(errors)} 个错误")
            for error in errors:
                self.logger.warning(f"  - {error}")

        return is_valid, errors

    def _check_required_fields(self, metrics: Dict) -> List[str]:
        """
        检查必填字段

        Args:
            metrics: 指标字典

        Returns:
            错误列表
        """
        errors = []

        # P0核心指标（必须有）
        required_fields = [
            'revenue',  # 营收
            'net_profit',  # 净利润
            'total_assets',  # 总资产
            'total_liabilities',  # 总负债
            'total_equity',  # 股东权益
        ]

        for field in required_fields:
            if field not in metrics or metrics[field] is None:
                errors.append(f"缺少必填字段: {field}")

        return errors

    def _check_value_ranges(self, metrics: Dict) -> List[str]:
        """
        检查数值范围

        Args:
            metrics: 指标字典

        Returns:
            错误列表
        """
        errors = []

        # 营收应该 > 0
        if metrics.get('revenue') is not None:
            if metrics['revenue'] < 0:
                errors.append(f"营收不能为负数: {metrics['revenue']}")

        # 总资产应该 > 0
        if metrics.get('total_assets') is not None:
            if metrics['total_assets'] <= 0:
                errors.append(f"总资产应大于0: {metrics['total_assets']}")

        # 资产负债率应在 [0, 1.5] 范围（超过1.5可能资不抵债）
        if metrics.get('asset_liability_ratio') is not None:
            ratio = metrics['asset_liability_ratio']
            if ratio < 0 or ratio > 1.5:
                errors.append(f"资产负债率超出合理范围 [0, 1.5]: {ratio}")

        # 流动比率应在 [0.5, 10] 范围
        if metrics.get('current_ratio') is not None:
            ratio = metrics['current_ratio']
            if ratio < 0 or ratio > 10:
                errors.append(f"流动比率超出合理范围 [0.5, 10]: {ratio}")

        # ROE应在 [-1, 1] 范围（即 -100% 到 100%）
        if metrics.get('roe') is not None:
            roe = metrics['roe']
            if roe < -1 or roe > 1:
                errors.append(f"ROE超出合理范围 [-1, 1]: {roe}")

        # 毛利率应在 [-0.5, 1] 范围
        if metrics.get('gross_margin') is not None:
            margin = metrics['gross_margin']
            if margin < -0.5 or margin > 1:
                errors.append(f"毛利率超出合理范围 [-0.5, 1]: {margin}")

        # 净利率应在 [-1, 1] 范围
        if metrics.get('net_margin') is not None:
            margin = metrics['net_margin']
            if margin < -1 or margin > 1:
                errors.append(f"净利率超出合理范围 [-1, 1]: {margin}")

        return errors

    def _check_logical_consistency(self, metrics: Dict) -> List[str]:
        """
        检查逻辑一致性

        Args:
            metrics: 指标字典

        Returns:
            错误列表
        """
        errors = []

        # 1. 资产负债表平衡：总资产 = 总负债 + 股东权益
        if all(metrics.get(f) is not None for f in ['total_assets', 'total_liabilities', 'total_equity']):
            assets = metrics['total_assets']
            liabilities = metrics['total_liabilities']
            equity = metrics['total_equity']

            # 允许1%的误差
            if abs(assets - (liabilities + equity)) / assets > 0.01:
                errors.append(
                    f"资产负债表不平衡: 总资产={assets}, 总负债={liabilities}, 股东权益={equity}"
                )

        # 2. 流动资产 <= 总资产
        if metrics.get('current_assets') and metrics.get('total_assets'):
            if metrics['current_assets'] > metrics['total_assets'] * 1.01:  # 允许1%误差
                errors.append(
                    f"流动资产({metrics['current_assets']})超过总资产({metrics['total_assets']})"
                )

        # 3. 流动负债 <= 总负债
        if metrics.get('current_liabilities') and metrics.get('total_liabilities'):
            if metrics['current_liabilities'] > metrics['total_liabilities'] * 1.01:
                errors.append(
                    f"流动负债({metrics['current_liabilities']})超过总负债({metrics['total_liabilities']})"
                )

        # 4. 营业成本 <= 营业收入（通常）
        if metrics.get('operating_cost') and metrics.get('revenue'):
            if metrics['operating_cost'] > metrics['revenue'] * 1.5:  # 允许一定范围
                errors.append(
                    f"营业成本({metrics['operating_cost']})远超营业收入({metrics['revenue']})"
                )

        # 5. 毛利率 = (营收 - 成本) / 营收
        if all(metrics.get(f) is not None for f in ['revenue', 'operating_cost', 'gross_margin']):
            expected_margin = (metrics['revenue'] - metrics['operating_cost']) / metrics['revenue']
            actual_margin = metrics['gross_margin']

            if abs(expected_margin - actual_margin) > 0.01:
                errors.append(
                    f"毛利率计算不一致: 期望={expected_margin:.4f}, 实际={actual_margin:.4f}"
                )

        return errors

    def _check_ratio_reasonability(self, metrics: Dict) -> List[str]:
        """
        检查比率合理性

        Args:
            metrics: 指标字典

        Returns:
            错误列表
        """
        errors = []

        # 盈利质量：经营现金流/净利润 应接近1（健康企业）
        if metrics.get('ocf_to_net_profit') is not None:
            ratio = metrics['ocf_to_net_profit']
            # 如果比率 < 0.5 或 > 3，给出警告（不是错误）
            if ratio < 0 or ratio > 5:
                errors.append(
                    f"盈利质量异常: 经营现金流/净利润 = {ratio}"
                )

        # 资产周转率应 > 0
        if metrics.get('asset_turnover') is not None:
            if metrics['asset_turnover'] <= 0:
                errors.append(
                    f"资产周转率应大于0: {metrics['asset_turnover']}"
                )

        # 存货周转率应 > 0
        if metrics.get('inventory_turnover') is not None:
            if metrics['inventory_turnover'] <= 0:
                errors.append(
                    f"存货周转率应大于0: {metrics['inventory_turnover']}"
                )

        return errors

    def calculate_confidence_score(self, metrics: Dict, errors: List[str]) -> float:
        """
        计算指标置信度

        Args:
            metrics: 指标字典
            errors: 错误列表

        Returns:
            置信度 (0-1)
        """
        # 基础分：根据提取到的P0指标数量
        p0_fields = [
            'revenue', 'net_profit', 'total_assets', 'total_liabilities', 'total_equity',
            'revenue_yoy', 'net_profit_yoy', 'asset_liability_ratio',
            'roe', 'gross_margin', 'net_margin', 'operating_cash_flow',
            'pe_ratio', 'pb_ratio', 'eps'
        ]

        found_p0 = sum(1 for field in p0_fields if metrics.get(field) is not None)
        base_score = found_p0 / len(p0_fields)

        # 错误惩罚：每个错误扣5%
        error_penalty = len(errors) * 0.05

        # 最终得分
        confidence = max(0, base_score - error_penalty)

        return round(confidence, 4)


# 便捷函数

def validate_metrics(metrics: Dict) -> Tuple[bool, List[str]]:
    """
    验证指标（便捷函数）

    Args:
        metrics: 指标字典

    Returns:
        (是否通过, 错误列表)
    """
    validator = MetricValidator()
    return validator.validate(metrics)


if __name__ == '__main__':
    # 测试
    print("MetricValidator模块")
    print("用法: 在其他模块中导入使用")
