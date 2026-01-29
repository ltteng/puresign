from pathlib import Path
import sys

from loguru import logger


def setup_logger() -> None:
    """
    配置 Loguru 日志系统
    - 自动创建 logs 目录
    - 每天轮转日志 (rotation)
    - 保留日志历史 (retention)
    """
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)

    # 移除默认的 handler (为了避免重复或自定义格式)
    logger.remove()

    # 1. 添加控制台输出 (Console)
    logger.add(
        sys.stderr,
        level="INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # 2. 添加文件输出 (File)
    # rotation="00:00": 每天零点创建一个新文件 (自动回滚/轮转)
    # retention="3 months": 只保留最近 3 个月的日志 (自动清理)
    # compression="zip": 压缩旧日志以节省空间
    logger.add(
        log_path / "puresign_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="3 months",
        compression="zip",
        level="INFO",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    logger.info("Logging system configured successfully")
