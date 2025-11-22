"""
筛选框架引擎

用于硬性门槛筛选，返回Pass/Fail结果
与评分引擎不同，这里关注的是"是否满足条件"而不是"得多少分"
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from ..utils.logger import get_logger


@dataclass
class CriterionResult:
    """单个标准的检查结果"""
    name: str
    description: str
    passed: bool
    actual_value: Any
    threshold: Any
    operator: str
    importance: str
    reason: str = ""

    @property
    def status_icon(self) -> str:
        """状态图标"""
        return "✅" if self.passed else "❌"


@dataclass
class CategoryResult:
    """分类检查结果"""
    name: str
    description: str
    required: bool
    passed: bool  # 该分类是否通过
    criteria_results: List[CriterionResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """通过率"""
        if not self.criteria_results:
            return 0.0
        passed_count = sum(1 for c in self.criteria_results if c.passed)
        return passed_count / len(self.criteria_results)

    @property
    def status_icon(self) -> str:
        """状态图标"""
        return "✅" if self.passed else "❌"


@dataclass
class ScreeningResult:
    """筛选结果"""
    framework_name: str
    framework_description: str
    passed: bool  # 总体是否通过
    result_type: str  # pass/fail/partial
    category_results: List[CategoryResult]
    failed_criteria: List[CriterionResult] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    @property
    def total_pass_rate(self) -> float:
        """总体通过率"""
        all_criteria = []
        for cat in self.category_results:
            all_criteria.extend(cat.criteria_results)
        if not all_criteria:
            return 0.0
        passed_count = sum(1 for c in all_criteria if c.passed)
        return passed_count / len(all_criteria)

    @property
    def status_icon(self) -> str:
        """状态图标"""
        if self.result_type == "pass":
            return "✅"
        elif self.result_type == "partial":
            return "⚠️"
        else:
            return "❌"


class ScreeningEngine:
    """筛选框架引擎"""

    def __init__(self, config_path: str):
        """
        初始化筛选引擎

        Args:
            config_path: 框架配置文件路径（YAML）
        """
        self.logger = get_logger()
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载框架配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"加载筛选框架: {config['name']}")
            return config
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            raise

    def screen(
        self,
        current_metrics: Dict[str, Any],
        historical_metrics: Optional[List[Dict[str, Any]]] = None,
        industry: Optional[str] = None
    ) -> ScreeningResult:
        """
        筛选股票

        Args:
            current_metrics: 当前财务指标
            historical_metrics: 历史财务指标列表（按时间倒序）
            industry: 所属行业（可选，用于行业特定调整）

        Returns:
            ScreeningResult: 筛选结果
        """
        self.logger.info(f"开始筛选，使用框架: {self.config['name']}")

        # 1. 应用行业调整（如果有）
        adjusted_config = self._apply_industry_adjustments(industry)

        # 2. 检查各分类
        category_results = []
        all_failed_criteria = []

        for category in adjusted_config['categories']:
            category_result = self._check_category(
                category,
                current_metrics,
                historical_metrics
            )
            category_results.append(category_result)

            # 收集未通过的条件
            for criterion in category_result.criteria_results:
                if not criterion.passed:
                    all_failed_criteria.append(criterion)

        # 3. 判断总体结果
        passed, result_type = self._determine_result(category_results)

        # 4. 生成建议
        suggestions = self._generate_suggestions(all_failed_criteria)

        # 5. 构建结果
        result = ScreeningResult(
            framework_name=self.config['name'],
            framework_description=self.config['description'],
            passed=passed,
            result_type=result_type,
            category_results=category_results,
            failed_criteria=all_failed_criteria,
            suggestions=suggestions
        )

        self.logger.info(
            f"筛选完成，结果: {result_type}, "
            f"通过率: {result.total_pass_rate:.1%}"
        )
        return result

    def _apply_industry_adjustments(self, industry: Optional[str]) -> Dict:
        """应用行业特定调整"""
        if not industry or 'industry_adjustments' not in self.config:
            return self.config

        adjustments = self.config['industry_adjustments'].get(industry)
        if not adjustments:
            return self.config

        # TODO: 实现行业调整逻辑
        # 这里暂时返回原配置
        self.logger.info(f"应用行业调整: {adjustments['name']}")
        return self.config

    def _check_category(
        self,
        category: Dict,
        current_metrics: Dict[str, Any],
        historical_metrics: Optional[List[Dict[str, Any]]]
    ) -> CategoryResult:
        """检查单个分类"""
        category_name = category['name']
        required = category.get('required', True)

        criteria_results = []

        for criterion in category['criteria']:
            result = self._check_criterion(
                criterion,
                current_metrics,
                historical_metrics
            )
            criteria_results.append(result)

        # 判断该分类是否通过
        if required:
            # 必须全部通过
            category_passed = all(c.passed for c in criteria_results)
        else:
            # 根据容错设置判断
            tolerance = self.config.get('tolerance', {})
            category_passed = self._check_with_tolerance(
                criteria_results,
                tolerance
            )

        return CategoryResult(
            name=category_name,
            description=category['description'],
            required=required,
            passed=category_passed,
            criteria_results=criteria_results
        )

    def _check_criterion(
        self,
        criterion: Dict,
        current_metrics: Dict[str, Any],
        historical_metrics: Optional[List[Dict[str, Any]]]
    ) -> CriterionResult:
        """检查单个标准"""
        check_type = criterion['check_type']

        if check_type == 'simple':
            return self._check_simple(criterion, current_metrics)
        elif check_type == 'consecutive_years':
            return self._check_consecutive_years(
                criterion, current_metrics, historical_metrics
            )
        elif check_type == 'cagr':
            return self._check_cagr(criterion, historical_metrics)
        elif check_type == 'latest_quarter':
            return self._check_latest_quarter(criterion, current_metrics)
        elif check_type == 'compare_benchmark':
            return self._check_compare_benchmark(criterion, current_metrics)
        elif check_type == 'negative_screen':
            return self._check_negative_screen(
                criterion, current_metrics, historical_metrics
            )
        elif check_type == 'rating':
            return self._check_rating(criterion, current_metrics)
        elif check_type == 'historical_percentile':
            return self._check_historical_percentile(
                criterion, current_metrics, historical_metrics
            )
        elif check_type == 'volatility':
            return self._check_volatility(criterion, historical_metrics)
        elif check_type == 'valuation_expansion':
            return self._check_valuation_expansion(criterion, historical_metrics)
        else:
            self.logger.warning(f"未知的检查类型: {check_type}")
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=None,
                operator="",
                importance=criterion.get('importance', 'medium'),
                reason="不支持的检查类型"
            )

    def _check_simple(
        self,
        criterion: Dict,
        metrics: Dict[str, Any]
    ) -> CriterionResult:
        """简单条件检查"""
        metric_name = criterion['metric']
        threshold = criterion['threshold']
        operator = criterion['operator']

        value = metrics.get(metric_name)

        if value is None:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason="数据缺失"
            )

        # 执行比较
        passed = self._compare(value, operator, threshold)
        reason = f"实际值: {self._format_value(value, metric_name)}"

        return CriterionResult(
            name=criterion['name'],
            description=criterion['description'],
            passed=passed,
            actual_value=value,
            threshold=threshold,
            operator=operator,
            importance=criterion.get('importance', 'medium'),
            reason=reason
        )

    def _check_consecutive_years(
        self,
        criterion: Dict,
        current_metrics: Dict[str, Any],
        historical_metrics: Optional[List[Dict[str, Any]]]
    ) -> CriterionResult:
        """连续N年满足条件"""
        metric_name = criterion['metric']
        threshold = criterion['threshold']
        operator = criterion['operator']
        required_years = criterion['years']

        if not historical_metrics or len(historical_metrics) < required_years:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason=f"历史数据不足（需要{required_years}年）"
            )

        # 检查最近N年
        consecutive_count = 0
        values = []

        for i, hist_data in enumerate(historical_metrics[:required_years]):
            value = hist_data.get(metric_name)
            if value is None:
                break

            values.append(value)
            if self._compare(value, operator, threshold):
                consecutive_count += 1
            else:
                break

        passed = consecutive_count >= required_years
        reason = f"连续{consecutive_count}/{required_years}年满足条件，" \
                f"近年值: {[self._format_value(v, metric_name) for v in values[:3]]}"

        return CriterionResult(
            name=criterion['name'],
            description=criterion['description'],
            passed=passed,
            actual_value=consecutive_count,
            threshold=required_years,
            operator=">=",
            importance=criterion.get('importance', 'medium'),
            reason=reason
        )

    def _check_cagr(
        self,
        criterion: Dict,
        historical_metrics: Optional[List[Dict[str, Any]]]
    ) -> CriterionResult:
        """复合增长率检查"""
        metric_name = criterion['metric']
        threshold = criterion['threshold']
        years = criterion['years']

        if not historical_metrics or len(historical_metrics) < years:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=">",
                importance=criterion.get('importance', 'medium'),
                reason=f"历史数据不足（需要{years}年）"
            )

        # 获取起始值和结束值
        start_value = historical_metrics[years - 1].get(metric_name)
        end_value = historical_metrics[0].get(metric_name)

        if start_value is None or end_value is None or start_value <= 0:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=">",
                importance=criterion.get('importance', 'medium'),
                reason="数据缺失或无效"
            )

        # 计算CAGR: (end/start)^(1/years) - 1
        cagr = (end_value / start_value) ** (1 / years) - 1
        passed = cagr > threshold
        reason = f"{years}年CAGR: {cagr:.1%}"

        return CriterionResult(
            name=criterion['name'],
            description=criterion['description'],
            passed=passed,
            actual_value=cagr,
            threshold=threshold,
            operator=">",
            importance=criterion.get('importance', 'medium'),
            reason=reason
        )

    def _check_latest_quarter(
        self,
        criterion: Dict,
        metrics: Dict[str, Any]
    ) -> CriterionResult:
        """最近季度数据检查"""
        # 这里简化处理，实际应该从季度数据中获取
        return self._check_simple(criterion, metrics)

    def _check_compare_benchmark(
        self,
        criterion: Dict,
        metrics: Dict[str, Any]
    ) -> CriterionResult:
        """与基准对比"""
        metric_name = criterion['metric']
        operator = criterion['operator']
        benchmark_value = criterion.get('benchmark_value', 0.025)

        value = metrics.get(metric_name)

        if value is None:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=benchmark_value,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason="数据缺失"
            )

        passed = self._compare(value, operator, benchmark_value)
        reason = f"实际: {value:.2%}, 基准: {benchmark_value:.2%}"

        return CriterionResult(
            name=criterion['name'],
            description=criterion['description'],
            passed=passed,
            actual_value=value,
            threshold=benchmark_value,
            operator=operator,
            importance=criterion.get('importance', 'medium'),
            reason=reason
        )

    def _check_negative_screen(
        self,
        criterion: Dict,
        current_metrics: Dict[str, Any],
        historical_metrics: Optional[List[Dict[str, Any]]]
    ) -> CriterionResult:
        """负面筛选（违规、造假等）"""
        metric_name = criterion['metric']
        threshold = criterion['threshold']

        # 这里需要从专门的数据源获取违规记录
        # 暂时简化处理
        value = current_metrics.get(metric_name, 0)
        passed = value == threshold  # 通常threshold为0，表示无违规
        reason = "无违规记录" if passed else f"发现{value}条违规记录"

        return CriterionResult(
            name=criterion['name'],
            description=criterion['description'],
            passed=passed,
            actual_value=value,
            threshold=threshold,
            operator="==",
            importance=criterion.get('importance', 'critical'),
            reason=reason
        )

    def _check_rating(
        self,
        criterion: Dict,
        metrics: Dict[str, Any]
    ) -> CriterionResult:
        """评级检查"""
        metric_name = criterion['metric']
        threshold = criterion['threshold']
        rating_scale = criterion.get('rating_scale', [])

        value = metrics.get(metric_name)

        if value is None:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=">=",
                importance=criterion.get('importance', 'medium'),
                reason="无评级数据"
            )

        # 比较评级
        try:
            value_index = rating_scale.index(value)
            threshold_index = rating_scale.index(threshold)
            passed = value_index >= threshold_index
            reason = f"评级: {value}"
        except ValueError:
            passed = False
            reason = f"评级无效: {value}"

        return CriterionResult(
            name=criterion['name'],
            description=criterion['description'],
            passed=passed,
            actual_value=value,
            threshold=threshold,
            operator=">=",
            importance=criterion.get('importance', 'medium'),
            reason=reason
        )

    def _compare(self, value: Any, operator: str, threshold: Any) -> bool:
        """执行比较操作"""
        try:
            if operator == '>':
                return value > threshold
            elif operator == '>=':
                return value >= threshold
            elif operator == '<':
                return value < threshold
            elif operator == '<=':
                return value <= threshold
            elif operator == '==':
                return value == threshold
            elif operator == '!=':
                return value != threshold
            else:
                return False
        except Exception:
            return False

    def _check_with_tolerance(
        self,
        criteria_results: List[CriterionResult],
        tolerance: Dict
    ) -> bool:
        """根据容错设置判断是否通过"""
        # 按重要性分组
        critical = [c for c in criteria_results if c.importance == 'critical']
        high = [c for c in criteria_results if c.importance == 'high']
        medium = [c for c in criteria_results if c.importance == 'medium']

        # critical必须全部通过
        if tolerance.get('critical_must_pass', True):
            if not all(c.passed for c in critical):
                return False

        # high至少达到指定通过率
        high_min_rate = tolerance.get('high_min_pass_rate', 0.8)
        if high:
            high_pass_rate = sum(1 for c in high if c.passed) / len(high)
            if high_pass_rate < high_min_rate:
                return False

        # medium至少达到指定通过率
        medium_min_rate = tolerance.get('medium_min_pass_rate', 0.6)
        if medium:
            medium_pass_rate = sum(1 for c in medium if c.passed) / len(medium)
            if medium_pass_rate < medium_min_rate:
                return False

        return True

    def _determine_result(
        self,
        category_results: List[CategoryResult]
    ) -> tuple[bool, str]:
        """判断总体结果"""
        # 检查必需分类是否全部通过
        required_categories = [c for c in category_results if c.required]
        all_required_passed = all(c.passed for c in required_categories)

        if all_required_passed:
            return True, "pass"

        # 检查是否允许部分通过
        tolerance = self.config.get('tolerance', {})
        if tolerance.get('allow_partial_pass', False):
            # 计算总体通过率
            total_rate = sum(c.pass_rate for c in category_results) / len(category_results)
            if total_rate >= 0.7:  # 70%以上算部分通过
                return False, "partial"

        return False, "fail"

    def _generate_suggestions(
        self,
        failed_criteria: List[CriterionResult]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 按重要性排序
        critical_failed = [c for c in failed_criteria if c.importance == 'critical']
        high_failed = [c for c in failed_criteria if c.importance == 'high']

        if critical_failed:
            suggestions.append(f"⚠️ 关键指标未达标（{len(critical_failed)}项）：")
            for criterion in critical_failed[:3]:  # 只显示前3个
                suggestions.append(f"  • {criterion.name}: {criterion.reason}")

        if high_failed:
            suggestions.append(f"📊 重要指标需改善（{len(high_failed)}项）：")
            for criterion in high_failed[:3]:
                suggestions.append(f"  • {criterion.name}: {criterion.reason}")

        return suggestions

    def _check_historical_percentile(
        self,
        criterion: Dict,
        current_metrics: Dict[str, Any],
        historical_metrics: Optional[List[Dict[str, Any]]]
    ) -> CriterionResult:
        """
        检查当前值与历史百分位的关系
        例如：当前PE < 5年PE中位数
        """
        metric_name = criterion['metric']
        operator = criterion['operator']
        percentile_type = criterion.get('percentile_type', 'median')
        years = criterion.get('years', 5)

        if not historical_metrics or len(historical_metrics) < years:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=None,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason=f"历史数据不足（需要{years}年）"
            )

        # 获取当前值
        current_value = current_metrics.get(metric_name)
        if current_value is None:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=None,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason="当前数据缺失"
            )

        # 收集历史值
        historical_values = []
        for hist_data in historical_metrics[:years]:
            value = hist_data.get(metric_name)
            if value is not None and value > 0:  # 排除负值和None
                historical_values.append(value)

        if len(historical_values) < 3:  # 至少需要3个历史点
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=current_value,
                threshold=None,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason=f"有效历史数据不足（仅{len(historical_values)}个）"
            )

        # 计算百分位值
        import statistics
        if percentile_type == 'median':
            threshold_value = statistics.median(historical_values)
        elif percentile_type == 'mean':
            threshold_value = statistics.mean(historical_values)
        elif percentile_type == '25th':
            historical_values.sort()
            threshold_value = historical_values[len(historical_values) // 4]
        elif percentile_type == '75th':
            historical_values.sort()
            threshold_value = historical_values[3 * len(historical_values) // 4]
        else:
            threshold_value = statistics.median(historical_values)

        # 比较
        passed = self._compare(current_value, operator, threshold_value)
        relative = current_value / threshold_value if threshold_value > 0 else 0
        reason = f"当前: {self._format_value(current_value, metric_name)}, " \
                f"{years}年{percentile_type}: {self._format_value(threshold_value, metric_name)}, " \
                f"相对位置: {relative:.2f}x"

        return CriterionResult(
            name=criterion['name'],
            description=criterion['description'],
            passed=passed,
            actual_value=current_value,
            threshold=threshold_value,
            operator=operator,
            importance=criterion.get('importance', 'medium'),
            reason=reason
        )

    def _check_volatility(
        self,
        criterion: Dict,
        historical_metrics: Optional[List[Dict[str, Any]]]
    ) -> CriterionResult:
        """
        检查波动率（变异系数）
        波动率 = 标准差 / 平均值
        """
        metric_name = criterion['metric']
        threshold = criterion['threshold']
        operator = criterion['operator']
        years = criterion.get('years', 5)

        if not historical_metrics or len(historical_metrics) < years:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason=f"历史数据不足（需要{years}年）"
            )

        # 收集历史值
        values = []
        for hist_data in historical_metrics[:years]:
            value = hist_data.get(metric_name)
            if value is not None and value > 0:
                values.append(value)

        if len(values) < 3:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason=f"有效数据不足（仅{len(values)}个）"
            )

        # 计算波动率
        import statistics
        mean_value = statistics.mean(values)
        if mean_value == 0:
            volatility = 999  # 平均值为0，波动率设为极大值
        else:
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            volatility = std_dev / mean_value

        # 比较
        passed = self._compare(volatility, operator, threshold)
        reason = f"{years}年波动率: {volatility:.1%}, " \
                f"均值: {self._format_value(mean_value, metric_name)}, " \
                f"标准差: {std_dev:.2f}"

        return CriterionResult(
            name=criterion['name'],
            description=criterion['description'],
            passed=passed,
            actual_value=volatility,
            threshold=threshold,
            operator=operator,
            importance=criterion.get('importance', 'medium'),
            reason=reason
        )

    def _check_valuation_expansion(
        self,
        criterion: Dict,
        historical_metrics: Optional[List[Dict[str, Any]]]
    ) -> CriterionResult:
        """
        检查估值扩张率
        估值扩张率 = 市值CAGR / 净利润CAGR
        """
        market_cap_metric = criterion.get('market_cap_metric', 'market_cap')
        profit_metric = criterion.get('profit_metric', 'net_profit')
        threshold = criterion['threshold']
        operator = criterion['operator']
        years = criterion.get('years', 5)

        if not historical_metrics or len(historical_metrics) < years:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason=f"历史数据不足（需要{years}年）"
            )

        # 获取起始和结束值
        start_market_cap = historical_metrics[years - 1].get(market_cap_metric)
        end_market_cap = historical_metrics[0].get(market_cap_metric)
        start_profit = historical_metrics[years - 1].get(profit_metric)
        end_profit = historical_metrics[0].get(profit_metric)

        # 检查数据有效性
        if None in [start_market_cap, end_market_cap, start_profit, end_profit]:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason="市值或利润数据缺失"
            )

        if start_market_cap <= 0 or start_profit <= 0:
            return CriterionResult(
                name=criterion['name'],
                description=criterion['description'],
                passed=False,
                actual_value=None,
                threshold=threshold,
                operator=operator,
                importance=criterion.get('importance', 'medium'),
                reason="起始数据无效（≤0）"
            )

        # 计算CAGR
        market_cap_cagr = (end_market_cap / start_market_cap) ** (1 / years) - 1
        profit_cagr = (end_profit / start_profit) ** (1 / years) - 1

        # 计算估值扩张率
        if profit_cagr <= 0:
            # 利润负增长，估值扩张率无意义
            expansion_ratio = 999  # 设为极大值，表示不合格
            reason = f"利润负增长（{profit_cagr:.1%}），估值扩张率无意义"
        else:
            expansion_ratio = market_cap_cagr / profit_cagr
            reason = f"市值CAGR: {market_cap_cagr:.1%}, " \
                    f"利润CAGR: {profit_cagr:.1%}, " \
                    f"扩张率: {expansion_ratio:.2f}x"

        # 比较
        passed = self._compare(expansion_ratio, operator, threshold)

        return CriterionResult(
            name=criterion['name'],
            description=criterion['description'],
            passed=passed,
            actual_value=expansion_ratio,
            threshold=threshold,
            operator=operator,
            importance=criterion.get('importance', 'medium'),
            reason=reason
        )

    def _format_value(self, value: Any, metric_name: str) -> str:
        """格式化数值显示"""
        if value is None:
            return "N/A"

        # 根据指标类型格式化
        if 'rate' in metric_name or 'margin' in metric_name or 'ratio' in metric_name:
            if 'debt' not in metric_name:  # 资产负债率等可能>1
                return f"{value:.1%}"

        if isinstance(value, float):
            return f"{value:.2f}"

        return str(value)


def load_screener(screener_name: str) -> ScreeningEngine:
    """
    快速加载筛选框架

    Args:
        screener_name: 筛选框架名称

    Returns:
        ScreeningEngine: 筛选引擎实例
    """
    config_dir = Path(__file__).parent.parent.parent / "config" / "frameworks"
    config_path = config_dir / f"{screener_name}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"筛选框架配置不存在: {config_path}")

    return ScreeningEngine(str(config_path))
