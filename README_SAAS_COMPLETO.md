# Bot SaaS - Plataforma Multi-Tenant

## 🚀 Visão Geral

Bot SaaS é uma plataforma multi-tenant que transforma o bot existente em um serviço escalável, permitindo múltiplos clientes (tenants) utilizarem o sistema de forma isolada e segura.

## 📁 Estrutura do Projeto

```
├── app/                          # Backend principal
│   ├── api/                      # Endpoints da API REST
│   │   ├── auth.py              # Autenticação e registro
│   │   ├── bot.py               # Controle do bot (start/stop/status)
│   │   ├── config.py            # Configurações do tenant
│   │   ├── logs.py              # Logs e histórico de execuções
│   │   └── health.py            # Health check e métricas
│   ├── core/                     # Módulos centrais
│   │   ├── config.py            # Configurações (Pydantic Settings)
│   │   ├── security.py          # JWT e autenticação
│   │   ├── crypto.py            # Criptografia de credenciais
│   │   └── deps.py              # Dependências FastAPI
│   ├── db/                       # Banco de dados
│   │   ├── database.py          # Conexão e pool
│   │   └── schema.sql           # Schema PostgreSQL
│   ├── models/                   # Modelos de dados
│   │   └── schemas.py           # Pydantic schemas
│   ├── worker/                   # Worker Celery
│   │   ├── tasks.py             # Tasks assíncronas
│   │   ├── bot_logic.py         # Lógica principal do bot
│   │   ├── session_manager.py   # Gerenciador de sessões
│   │   ├── config_loader.py     # Loader de configurações
│   │   ├── browser_config.py    # Configuração Playwright
│   │   └── celery_config.py     # Configuração Celery
│   └── main.py                   # Aplicação FastAPI
├── frontend-saas/                # Frontend React
│   ├── src/
│   │   ├── components/          # Componentes reutilizáveis
│   │   ├── pages/               # Páginas da aplicação
│   │   ├── hooks/               # React hooks customizados
│   │   ├── services/            # API client
│   │   ├── contexts/            # Context providers
│   │   └── styles/              # CSS
│   └── Dockerfile               # Build do frontend
├── alembic/                      # Migrations do banco
├── docker-compose.yml            # Orquestração de containers
├── Dockerfile.api                # Imagem da API
├── Dockerfile.worker             # Imagem do Worker
├── requirements.txt              # Dependências Python
└── .env.example                  # Variáveis de ambiente exemplo
```

## 🛠️ Tecnologias

| Componente | Tecnologia |
|------------|------------|
| API | FastAPI 0.109 |
| Worker | Celery 5.3 |
| Banco de Dados | PostgreSQL 16 |
| Cache/Broker | Redis 7 |
| Automação | Playwright 1.48 |
| Frontend | React 18 |
| Auth | JWT (PyJWT) |
| Deploy | Docker Compose |

## 📋 Pré-requisitos

- Docker Desktop instalado
- Git
- 4GB RAM mínimo
- 10GB espaço em disco

## 🚀 Instalação Rápida

### 1. Clone o repositório
```bash
git clone <repo-url>
cd Bot-main\ -\ Facebook
```

### 2. Configure as variáveis de ambiente
```bash
copy .env.example .env
# Edite o arquivo .env com suas configurações
```

### 3. Inicie a plataforma
```bash
# Windows
start_saas.bat

# Linux/Mac
chmod +x start_saas.sh
./start_saas.sh
```

### 4. Acesse a plataforma
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery)**: http://localhost:5555

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```env
# Banco de Dados
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/bot_saas

# Redis
REDIS_URL=redis://redis:6379/0

# Segurança
SECRET_KEY=sua-chave-secreta-aqui
ENCRYPTION_KEY=chave-criptografia-32bytes

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Ambiente
ENVIRONMENT=development
DEBUG=true
```

## 📖 API Reference

### Autenticação

#### POST /api/v1/auth/register
Registra novo usuário e tenant.

```json
{
  "email": "user@example.com",
  "password": "senha123",
  "full_name": "Nome Completo",
  "tenant_name": "Minha Empresa"
}
```

#### POST /api/v1/auth/token
Login e obtenção de token JWT.

```json
{
  "username": "user@example.com",
  "password": "senha123"
}
```

### Bot

#### POST /api/v1/bot/start
Inicia o bot para o tenant atual.

#### POST /api/v1/bot/stop
Para o bot.

#### GET /api/v1/bot/status
Retorna status atual do bot.

### Configurações

#### GET /api/v1/config
Retorna configurações do bot.

#### PUT /api/v1/config
Atualiza configurações.

```json
{
  "source_urls": ["https://facebook.com/grupo1"],
  "interval_seconds": 60,
  "destination_config": {
    "groups": ["grupo-destino-1"]
  }
}
```

### Logs

#### GET /api/v1/logs/runs
Lista execuções do bot.

#### GET /api/v1/logs/runs/{run_id}
Detalhes de uma execução.

## 🔐 Segurança

### Isolamento Multi-Tenant
- Cada tenant possui dados completamente isolados
- RLS (Row Level Security) no PostgreSQL
- Sessões Playwright separadas por tenant

### Criptografia
- Senhas: bcrypt com salt
- Credenciais: Fernet (AES-128)
- Tokens: JWT com expiração

### Proteções
- CORS configurado
- Rate limiting
- Validação de input
- Sanitização de dados

## 🐳 Docker Commands

```bash
# Iniciar todos os serviços
docker compose up -d

# Ver logs
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f api
docker compose logs -f worker

# Reiniciar serviços
docker compose restart

# Parar tudo
docker compose down

# Rebuild após mudanças
docker compose up -d --build

# Limpar volumes (CUIDADO: apaga dados)
docker compose down -v
```

## 🔧 Desenvolvimento

### Rodar localmente (sem Docker)

1. **Instale as dependências**
```bash
pip install -r requirements.txt
```

2. **Inicie PostgreSQL e Redis**
```bash
docker compose up -d postgres redis
```

3. **Execute as migrations**
```bash
alembic upgrade head
```

4. **Inicie a API**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Inicie o Worker**
```bash
celery -A app.worker.celery_config worker -l info
```

6. **Inicie o Frontend**
```bash
cd frontend-saas
npm install
npm start
```

## 📊 Monitoramento

### Flower (Celery Dashboard)
Acesse http://localhost:5555 para:
- Ver tasks em execução
- Monitorar workers
- Ver histórico de tasks

### Logs Estruturados
Todos os logs incluem:
- `tenant_id`: Identificador do tenant
- `run_id`: ID da execução
- `timestamp`: Data/hora
- `level`: INFO, WARNING, ERROR

## 🚨 Troubleshooting

### Bot não inicia
1. Verifique logs: `docker compose logs worker`
2. Confirme que Redis está rodando
3. Verifique configurações do tenant

### Erro de conexão com banco
1. Verifique se PostgreSQL está rodando
2. Confirme DATABASE_URL no .env
3. Rode migrations: `alembic upgrade head`

### Frontend não conecta à API
1. Verifique CORS no backend
2. Confirme que API está rodando
3. Verifique URL no arquivo api.js

## 📈 Escalabilidade

### Horizontal Scaling
```yaml
# docker-compose.yml
services:
  worker:
    deploy:
      replicas: 3
```

### Por Tenant
- Cada tenant pode ter configurações específicas
- Rate limits por plano (free, pro, enterprise)
- Filas separadas se necessário

## 📝 Licença

Projeto privado - Todos os direitos reservados.

## 🤝 Suporte

Para suporte, entre em contato com a equipe de desenvolvimento.
