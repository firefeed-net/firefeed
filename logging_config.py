import logging
import sys
from config import LOG_LEVEL


def setup_logging():
    """Глобальная настройка логирования для всего приложения."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),  # Преобразуем строку в уровень
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),  # Вывод в stderr для systemd/journalctl
        ],
    )
