# FireFeed - AI-powered newsfeed

Тут будет нормальное описание

## Установка и зависимости

pip install -r requirements.txt

## Запуск

### Запуск через команды

python -m venv venv
source venv/bin/activate
python bot.py

### Запуск через bash-скрипт

chmod +x ./run_bot.sh
./run_bot.sh

### Запуск через systemd-юнит

```
[Unit]
Description=FireFeed Telegram Bot Service
After=network.target

[Service]
Type=simple
User=firefeed
Group=firefeed
WorkingDirectory=/var/www/firefeed/data/www/firefeed.net/integrations/telegram


ExecStartPre=/bin/sh -c 'pids=$(lsof -t -i:5000); [ -n "$pids" ] && kill -9 $pids || true'
ExecStart=/var/www/firefeed/data/www/firefeed.net/integrations/telegram/run_bot.sh
ExecStopPost=/bin/sh -c 'pids=$(lsof -t -i:5000); [ -n "$pids" ] && kill -9 $pids || true'

Restart=on-failure
RestartSec=10

TimeoutStopSec=5
KillMode=process
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
```