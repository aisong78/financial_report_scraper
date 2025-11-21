"""
分析模块

提供投资分析框架
"""

from .framework_engine import (
    FrameworkEngine,
    AnalysisResult,
    CategoryScore,
    MetricScore,
    load_framework
)

__all__ = [
    'FrameworkEngine',
    'AnalysisResult',
    'CategoryScore',
    'MetricScore',
    'load_framework',
]
