@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo Остановка Telegram Moderation Bot...
docker compose down
if errorlevel 1 (
    echo [ОШИБКА] Не удалось остановить контейнеры.
    pause
    exit /b 1
)

echo Готово. Бот остановлен.
pause
