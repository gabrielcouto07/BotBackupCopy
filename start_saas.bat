@echo off
REM ==================================================
REM Bot SaaS - Script de Inicialização (Windows)
REM ==================================================

echo.
echo 🚀 Iniciando Bot SaaS Platform...
echo.

REM Verifica se Docker está rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker não está rodando. Por favor, inicie o Docker Desktop primeiro.
    pause
    exit /b 1
)

REM Verifica se .env existe
if not exist .env (
    echo 📋 Arquivo .env não encontrado. Criando a partir do exemplo...
    copy .env.example .env
    echo ✅ .env criado. Por favor, revise as configurações em .env
    echo.
)

echo.
echo 📦 Construindo imagens Docker...
docker compose build

echo.
echo 🗄️  Iniciando banco de dados e Redis...
docker compose up -d postgres redis
timeout /t 5 /nobreak >nul

echo.
echo 📊 Aplicando schema do banco de dados...
docker compose exec -T postgres psql -U postgres -d bot_saas -f /dev/stdin < app\db\schema.sql 2>nul

echo.
echo 🚀 Iniciando todos os serviços...
docker compose up -d

echo.
echo ⏳ Aguardando serviços iniciarem...
timeout /t 10 /nobreak >nul

echo.
echo ✅ Bot SaaS iniciado com sucesso!
echo.
echo 📍 URLs disponíveis:
echo    Frontend:     http://localhost:3000
echo    API:          http://localhost:8000
echo    API Docs:     http://localhost:8000/docs
echo    Flower:       http://localhost:5555
echo.
echo 📝 Para ver os logs: docker compose logs -f
echo 🛑 Para parar: docker compose down
echo.
pause
