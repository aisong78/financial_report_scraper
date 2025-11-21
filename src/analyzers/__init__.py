"""
分析模块

提供投资分析框架：评分型和筛选型
"""

from .framework_engine import (
    FrameworkEngine,
    AnalysisResult,
    CategoryScore,
    MetricScore,
    load_framework
)

from .screening_engine import (
    ScreeningEngine,
    ScreeningResult,
    CategoryResult,
    CriterionResult,
    load_screener
)

__all__ = [
    # 评分型框架
    'FrameworkEngine',
    'AnalysisResult',
    'CategoryScore',
    'MetricScore',
    'load_framework',
    # 筛选型框架
    'ScreeningEngine',
    'ScreeningResult',
    'CategoryResult',
    'CriterionResult',
    'load_screener',
]
