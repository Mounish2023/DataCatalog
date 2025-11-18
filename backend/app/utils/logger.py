from loguru import logger
import sys
from pathlib import Path

# Remove default handler
logger.remove()

# Add console handler with custom format
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Add file handler
log_path = Path("logs")
log_path.mkdir(exist_ok=True)

logger.add(
    log_path / "app.log",   
    rotation="10 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Add error file handler
logger.add(
    log_path / "error.log",
    level="ERROR",
    rotation="10 MB", 
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

__all__ = ["logger"]
