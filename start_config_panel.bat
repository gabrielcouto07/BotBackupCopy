@echo off
echo ====================================
echo   Bot de Afiliados - Painel Config
echo ====================================
echo.

echo [1/2] Iniciando API Backend...
start "API Backend" cmd /k "cd backend && python api_config.py"
timeout /t 3 /nobreak > nul

echo [2/2] Iniciando Frontend React...
start "Frontend React" cmd /k "cd frontend && npm start"

echo.
echo ====================================
echo   Tudo pronto!
echo ====================================
echo.
echo API Backend: http://localhost:5000
echo Frontend:    http://localhost:3000
echo.
echo Pressione qualquer tecla para fechar este terminal...
pause > nul
