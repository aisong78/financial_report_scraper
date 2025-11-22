"""
分析框架引擎

负责加载框架配置、执行评分规则、生成投资建议
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from ..utils.logger import get_logger


@dataclass
class MetricScore:
    """单个指标的评分结果"""
    name: str
    display_name: str
    value: Any
    score: float
    max_score: float
    comment: str
    unit: str = ""


@dataclass
class CategoryScore:
    """分类得分"""
    name: str
    description: str
    score: float
    max_score: float
    metrics: List[MetricScore] = field(default_factory=list)

    @property
    def score_percentage(self) -> float:
        """得分率"""
        return (self.score / self.max_score * 100) if self.max_score > 0 else 0


@dataclass
class AnalysisResult:
    """分析结果"""
    framework_name: str
    framework_description: str
    total_score: float
    max_score: float
    category_scores: List[CategoryScore]
    recommendation: str
    reasoning: str
    risk_level: str
    risk_alerts: List[str] = field(default_factory=list)

    @property
    def score_percentage(self) -> float:
        """总得分率"""
        return (self.total_score / self.max_score * 100) if self.max_score > 0 else 0

    @property
    def grade(self) -> str:
        """评级"""
        score = self.score_percentage
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        else:
            return "F"


class FrameworkEngine:
    """分析框架引擎"""

    def __init__(self, config_path: str):
        """
        初始化框架引擎

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
            self.logger.info(f"加载框架配置: {config['name']}")
            return config
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            raise

    def analyze(self, metrics: Dict[str, Any]) -> AnalysisResult:
        """
        分析财务指标，返回评分和建议

        Args:
            metrics: 财务指标字典，键为指标名，值为指标值

        Returns:
            AnalysisResult: 分析结果
        """
        self.logger.info(f"开始分析，使用框架: {self.config['name']}")

        # 1. 计算各分类得分
        category_scores = []
        total_score = 0
        max_score = 0

        for category in self.config['categories']:
            category_result = self._evaluate_category(category, metrics)
            category_scores.append(category_result)
            total_score += category_result.score
            max_score += category_result.max_score

        # 2. 生成投资建议
        recommendation, reasoning, risk_level = self._generate_recommendation(total_score)

        # 3. 检查风险提示
        risk_alerts = self._check_risk_alerts(metrics)

        # 4. 构建结果
        result = AnalysisResult(
            framework_name=self.config['name'],
            framework_description=self.config['description'],
            total_score=total_score,
            max_score=max_score,
            category_scores=category_scores,
            recommendation=recommendation,
            reasoning=reasoning,
            risk_level=risk_level,
            risk_alerts=risk_alerts
        )

        self.logger.info(f"分析完成，总分: {total_score:.1f}/{max_score}, 评级: {result.grade}")
        return result

    def _evaluate_category(self, category: Dict, metrics: Dict[str, Any]) -> CategoryScore:
        """
        评估单个分类

        Args:
            category: 分类配置
            metrics: 指标数据

        Returns:
            CategoryScore: 分类得分
        """
        category_name = category['name']
        category_weight = category['weight']

        metric_scores = []
        total_score = 0

        for metric_config in category['metrics']:
            metric_name = metric_config['name']
            metric_weight = metric_config['weight']
            metric_value = metrics.get(metric_name)

            # 计算该指标得分
            score, comment = self._evaluate_metric(metric_config, metric_value)

            metric_score = MetricScore(
                name=metric_name,
                display_name=metric_config['display_name'],
                value=metric_value,
                score=score,
                max_score=metric_weight,
                comment=comment,
                unit=metric_config.get('unit', '')
            )

            metric_scores.append(metric_score)
            total_score += score

        return CategoryScore(
            name=category_name,
            description=category['description'],
            score=total_score,
            max_score=category_weight,
            metrics=metric_scores
        )

    def _evaluate_metric(self, metric_config: Dict, value: Any) -> tuple[float, str]:
        """
        评估单个指标

        Args:
            metric_config: 指标配置
            value: 指标值

        Returns:
            (score, comment): 得分和评语
        """
        # 如果值不存在，返回0分
        if value is None:
            return 0, "数据缺失"

        rules = metric_config['rules']
        max_score = metric_config['weight']

        # 遍历规则，找到第一个匹配的
        for rule in rules:
            # 默认规则
            if 'default' in rule:
                return rule['default'], rule.get('comment', '')

            # 条件规则
            condition = rule['condition']
            try:
                # 评估条件
                # 注意：这里使用eval有安全风险，但在配置文件可信的情况下可以使用
                # 生产环境应该使用更安全的表达式解析器
                if self._evaluate_condition(condition, value):
                    return rule['score'], rule.get('comment', '')
            except Exception as e:
                self.logger.warning(f"条件评估失败: {condition}, 错误: {e}")
                continue

        # 如果没有匹配的规则，返回0分
        return 0, "未匹配到评分规则"

    def _evaluate_condition(self, condition: str, value: Any) -> bool:
        """
        安全地评估条件表达式

        Args:
            condition: 条件字符串，如 "value >= 0.20"
            value: 变量值

        Returns:
            bool: 条件是否满足
        """
        # 创建安全的命名空间
        namespace = {'value': value}

        try:
            # 评估条件
            result = eval(condition, {"__builtins__": {}}, namespace)
            return bool(result)
        except Exception as e:
            self.logger.warning(f"条件评估失败: {condition}, value={value}, 错误: {e}")
            return False

    def _generate_recommendation(self, total_score: float) -> tuple[str, str, str]:
        """
        根据总分生成投资建议

        Args:
            total_score: 总分

        Returns:
            (action, reasoning, risk_level): 操作建议、理由、风险等级
        """
        recommendations = self.config['recommendations']

        for rec in recommendations:
            score_min, score_max = rec['score_range']
            if score_min <= total_score <= score_max:
                return (
                    rec['action'],
                    rec['reasoning'],
                    rec['risk_level']
                )

        # 默认建议
        return "观察", "评分异常，建议人工审核", "未知"

    def _check_risk_alerts(self, metrics: Dict[str, Any]) -> List[str]:
        """
        检查风险提示

        Args:
            metrics: 指标数据

        Returns:
            List[str]: 风险提示列表
        """
        risk_alerts = []

        for alert_config in self.config.get('risk_alerts', []):
            condition = alert_config['condition']

            # 解析条件中的指标名
            # 简单的字符串解析，假设条件格式为 "metric_name > value"
            try:
                # 构建命名空间，包含所有指标（过滤None值以避免比较错误）
                namespace = {k: v for k, v in metrics.items() if v is not None}

                # 直接评估条件（如果条件中引用的指标不存在或为None，跳过）
                if eval(condition, {"__builtins__": {}}, namespace):
                    alert_message = f"[{alert_config['level']}] {alert_config['message']}"
                    risk_alerts.append(alert_message)
            except (KeyError, NameError, TypeError) as e:
                # KeyError/NameError: 指标不存在，TypeError: None值比较
                # 这些情况下跳过该风险检查
                pass
            except Exception as e:
                self.logger.warning(f"风险检查失败: {condition}, 错误: {e}")
                continue

        return risk_alerts


def load_framework(framework_name: str) -> FrameworkEngine:
    """
    快速加载框架

    Args:
        framework_name: 框架名称（value_investing 或 growth_investing）

    Returns:
        FrameworkEngine: 框架引擎实例
    """
    # 获取配置文件路径
    config_dir = Path(__file__).parent.parent.parent / "config" / "frameworks"
    config_path = config_dir / f"{framework_name}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"框架配置文件不存在: {config_path}")

    return FrameworkEngine(str(config_path))
