@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ========================================
echo  Telegram Moderation Bot - запуск
echo ========================================
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Docker не запущен. Сначала откройте Docker Desktop.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ОШИБКА] Файл .env не найден. Скопируйте .env.example в .env и заполните настройки.
    pause
    exit /b 1
)

echo Запуск контейнера...
docker compose up -d --build
if errorlevel 1 (
    echo [ОШИБКА] Не удалось запустить docker compose.
    pause
    exit /b 1
)

echo.
echo Статус:
docker compose ps
echo.
echo Бот запущен. Логи: logs\bot.log
echo Остановка: stop.bat или docker compose down
echo.
pause
