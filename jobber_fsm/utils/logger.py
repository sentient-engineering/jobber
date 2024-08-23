import logging
import os
from typing import Union

# Create a logs directory if it doesn't exist
log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s {%(filename)s:%(lineno)d} - %(message)s",
)

# Remove all handlers from the root logger
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logger = logging.getLogger(__name__)
logger.addHandler(logging.FileHandler(os.path.join(log_directory, "app.log")))
logger.setLevel(logging.INFO)

# logging.getLogger("httpcore").setLevel(logging.WARNING)
# logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("matplotlib.pyplot").setLevel(logging.WARNING)
# logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
# logging.getLogger("PIL.Image").setLevel(logging.WARNING)


def set_log_level(level: Union[str, int]) -> None:
    """
    Set the log level for the logger.

    Parameters:
    - level (Union[str, int]): A string or logging level such as 'debug', 'info', 'warning', 'error', or 'critical', or the corresponding logging constants like logging.DEBUG, logging.INFO, etc.
    """
    if isinstance(level, str):
        level = level.upper()
        numeric_level = getattr(logging, level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Invalid log level: {level}")
        logger.setLevel(numeric_level)
    else:
        logger.setLevel(level)
