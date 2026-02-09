@echo off
echo ====================================
echo   Bot de Afiliados - Painel Config
echo ====================================
echo.

REM Verifica se as dependências do backend estão instaladas
echo [1/4] Verificando dependências do backend...
cd backend
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Instalando dependências do backend...
    pip install flask flask-cors
) else (
    echo Dependências do backend OK!
)
cd ..

REM Verifica se as dependências do frontend estão instaladas
echo [2/4] Verificando dependências do frontend...
cd frontend
if not exist "node_modules\" (
    echo Instalando dependências do frontend...
    call npm install
) else (
    echo Dependências do frontend OK!
)
cd ..

echo.
echo [3/4] Iniciando API Backend...
start "API Backend" cmd /k "cd backend && python api.py"
timeout /t 3 /nobreak > nul

echo [4/4] Iniciando Frontend React...
start "Frontend React" cmd /k "cd frontend && npm start"

echo.
echo ====================================
echo   Tudo pronto!
echo ====================================
echo.
echo API Backend: http://localhost:5000
echo Frontend:    http://localhost:3000
echo.
echo O painel web abrira automaticamente no seu navegador.
echo.
echo Pressione qualquer tecla para fechar este terminal...
pause > nul
