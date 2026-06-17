"""
日志工具模块
使用 loguru 实现美化日志输出
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    log_file: str = "data/bot.log",
    level: str = "INFO",
    rotation: str = "10 MB"
):
    """
    配置日志系统

    Args:
        log_file: 日志文件路径
        level: 日志级别
        rotation: 日志轮转大小
    """
    # 移除默认的控制台输出
    logger.remove()

    # 添加控制台输出（带颜色）
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=level,
        colorize=True
    )

    # 添加文件输出
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_path),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=level,
        rotation=rotation,
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )

    return logger


# 创建默认的 logger 实例
bot_logger = setup_logger()
