"""
日志系统模块

提供统一的日志记录功能
"""

import os
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "financial_scraper",
    log_dir: Optional[str] = None,
    log_level: str = "INFO",
    console: bool = True,
    file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_dir: 日志文件目录
        log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        console: 是否输出到控制台
        file: 是否输出到文件
        max_bytes: 单个日志文件最大字节数
        backup_count: 保留的日志文件数量

    Returns:
        配置好的 Logger 实例
    """
    # 创建 logger
    logger = logging.getLogger(name)

    # 防止重复添加 handler
    if logger.handlers:
        return logger

    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台 handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件 handler
    if file:
        # 确定日志目录
        if log_dir is None:
            # 默认日志目录：项目根目录的 logs/
            project_root = Path(__file__).resolve().parent.parent.parent
            log_dir = project_root / "logs"
        else:
            log_dir = Path(log_dir)

        # 创建日志目录
        log_dir.mkdir(parents=True, exist_ok=True)

        # 日志文件路径
        log_file = log_dir / f"{name}.log"

        # 使用 RotatingFileHandler（自动轮转）
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 全局 logger 实例
_logger_instance: Optional[logging.Logger] = None


def get_logger(
    name: str = "financial_scraper",
    log_dir: Optional[str] = None,
    log_level: str = "INFO"
) -> logging.Logger:
    """
    获取全局 logger 实例（单例模式）

    Args:
        name: 日志记录器名称
        log_dir: 日志目录
        log_level: 日志级别

    Returns:
        Logger 实例
    """
    global _logger_instance

    if _logger_instance is None:
        # 尝试从配置读取
        try:
            from .config import get_config
            config = get_config()
            log_dir = log_dir or config.log_dir
            log_level = log_level or config.log_level
        except Exception:
            pass

        _logger_instance = setup_logger(
            name=name,
            log_dir=log_dir,
            log_level=log_level
        )

    return _logger_instance


# 便捷函数

def debug(msg: str, *args, **kwargs):
    """记录 DEBUG 级别日志"""
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """记录 INFO 级别日志"""
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """记录 WARNING 级别日志"""
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """记录 ERROR 级别日志"""
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """记录 CRITICAL 级别日志"""
    get_logger().critical(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """记录异常日志（包含堆栈信息）"""
    get_logger().exception(msg, *args, **kwargs)


if __name__ == "__main__":
    # 测试日志系统
    logger = get_logger(log_level="DEBUG")

    logger.debug("这是一条 DEBUG 消息")
    logger.info("这是一条 INFO 消息")
    logger.warning("这是一条 WARNING 消息")
    logger.error("这是一条 ERROR 消息")

    # 测试异常记录
    try:
        1 / 0
    except Exception:
        logger.exception("捕获到异常")

    print("日志测试完成，请查看 logs/financial_scraper.log")
