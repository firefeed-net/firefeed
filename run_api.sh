#!/bin/bash

# Активируем виртуальное окружение
source /var/www/firefeed/data/www/firefeed.net/integrations/telegram/venv/bin/activate

# Запускаем FastAPI через uvicorn
uvicorn api.main:app --host 127.0.0.1 --port 8000
