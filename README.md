# Поиск по расписанию экзаменационной сессии РТУ МИРЭА
 [![BOT - LINK](https://img.shields.io/static/v1?label=BOT&message=LINK&color=229ed9&style=for-the-badge)](https://t.me/teacherschedulertu_bot)

Данный бот парсит Json файл со всеми экзаменами и выдаёт преподавателя или группу по запросу

Json был получен при помощи парсера    [rtu-schedule-parser](https://github.com/mirea-ninja/rtu-schedule-parser)

# Запуск бота

### Локальный запуск

1. Установите все необходимые зависимости, используя Poetry:
```bash
poetry install
```
2. Добавьте файл `.env` в корневую директорию проекта и заполните его по примеру `.env.example`
3. Запустите приложение:
```bash
poetry run python bot/main.py
```
### Запуск с использованием Docker
1. Добавьте файл `.env` в корневую директорию проекта и заполните его по примеру `.env.example`
2. Запустите приложение:

```bash
docker-compose up -d
``` 
