#!/bin/bash
# ==================================================
# Bot SaaS - Script de Inicialização
# ==================================================

set -e

echo "🚀 Iniciando Bot SaaS Platform..."
echo ""

# Verifica se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Verifica se .env existe
if [ ! -f .env ]; then
    echo "📋 Arquivo .env não encontrado. Criando a partir do exemplo..."
    cp .env.example .env
    echo "✅ .env criado. Por favor, revise as configurações antes de continuar."
    echo ""
fi

# Gera SECRET_KEY se não definida
if grep -q "SECRET_KEY=your-super-secret-key" .env 2>/dev/null; then
    NEW_SECRET=$(openssl rand -hex 32)
    sed -i "s/SECRET_KEY=your-super-secret-key/SECRET_KEY=$NEW_SECRET/" .env
    echo "🔑 SECRET_KEY gerada automaticamente."
fi

# Gera ENCRYPTION_KEY se não definida
if grep -q "ENCRYPTION_KEY=your-32-byte-encryption-key" .env 2>/dev/null; then
    NEW_KEY=$(openssl rand -base64 32)
    sed -i "s|ENCRYPTION_KEY=your-32-byte-encryption-key|ENCRYPTION_KEY=$NEW_KEY|" .env
    echo "🔐 ENCRYPTION_KEY gerada automaticamente."
fi

echo ""
echo "📦 Construindo imagens Docker..."
docker compose build

echo ""
echo "🗄️  Iniciando banco de dados e Redis..."
docker compose up -d postgres redis
sleep 5

echo ""
echo "📊 Aplicando schema do banco de dados..."
docker compose exec -T postgres psql -U postgres -d bot_saas < app/db/schema.sql 2>/dev/null || true

echo ""
echo "🚀 Iniciando todos os serviços..."
docker compose up -d

echo ""
echo "⏳ Aguardando serviços iniciarem..."
sleep 10

echo ""
echo "✅ Bot SaaS iniciado com sucesso!"
echo ""
echo "📍 URLs disponíveis:"
echo "   Frontend:     http://localhost:3000"
echo "   API:          http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Flower:       http://localhost:5555"
echo ""
echo "📝 Para ver os logs: docker compose logs -f"
echo "🛑 Para parar: docker compose down"
echo ""
