# Bot SaaS Multi-Tenant

Plataforma SaaS multi-tenant para gerenciamento de bots com isolamento por cliente.

## Arquitetura

```
┌─────────────┐
│   Frontend  │ (React/Next.js)
│   :3000     │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐
│   API       │ (FastAPI)
│   :8000     │ ← JWT + X-Tenant-ID
└──────┬──────┘
       │
       ├─────────┬─────────┬─────────┐
       ▼         ▼         ▼         ▼
   ┌──────┐ ┌──────┐  ┌──────┐  ┌──────┐
   │ PG   │ │Redis │  │Worker│  │Worker│ (Celery + Playwright)
   │ DB   │ │Queue │  │  1   │  │  2   │
   └──────┘ └──────┘  └──────┘  └──────┘
```

## Quick Start (Desenvolvimento)

### 1. Pré-requisitos

- Docker e Docker Compose
- Python 3.11+
- Node.js 18+

### 2. Configuração

```bash
# Clonar e entrar no diretório
cd bot-saas

# Copiar arquivo de ambiente
cp .env.example .env

# Gerar chaves de segurança
python -c "import secrets; print(secrets.token_hex(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Editar .env com as chaves geradas
```

### 3. Iniciar com Docker Compose

```bash
# Subir todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar status
docker-compose ps
```

### 4. Acessar

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Flower** (Celery): http://localhost:5555
- **Frontend**: http://localhost:3000

## Estrutura do Projeto

```
├── app/
│   ├── api/           # Endpoints FastAPI
│   │   ├── auth.py    # Autenticação (register, login)
│   │   ├── bot.py     # Controle do bot (start, stop, status)
│   │   ├── config.py  # Configurações do bot
│   │   ├── logs.py    # Logs e histórico
│   │   └── health.py  # Health check e métricas
│   ├── core/          # Núcleo da aplicação
│   │   ├── config.py  # Settings (Pydantic)
│   │   ├── security.py# JWT, hashing
│   │   ├── crypto.py  # Criptografia Fernet
│   │   └── deps.py    # Dependency injection
│   ├── db/            # Database
│   │   ├── schema.sql # Schema PostgreSQL
│   │   └── database.py# Connection pool
│   ├── models/        # Pydantic schemas
│   │   └── schemas.py # Request/Response models
│   ├── worker/        # Celery workers
│   │   ├── tasks.py   # Tasks Celery
│   │   ├── bot_logic.py# Lógica do bot
│   │   ├── browser_config.py # Playwright config
│   │   ├── session_manager.py # Sessões por tenant
│   │   └── config_loader.py  # Carrega configs
│   └── main.py        # FastAPI app
├── frontend-saas/     # Frontend React
├── docker-compose.yml # Orquestração
├── Dockerfile.api     # Imagem da API
├── Dockerfile.worker  # Imagem do Worker
└── requirements.txt   # Dependências Python
```

## API Endpoints

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/auth/register` | Registrar novo usuário e tenant |
| POST | `/api/v1/auth/login` | Login (retorna JWT) |
| GET | `/api/v1/auth/me` | Info do usuário atual |
| GET | `/api/v1/auth/tenants` | Listar tenants do usuário |

### Controle do Bot

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/bot/status` | Status atual do bot |
| POST | `/api/v1/bot/start` | Iniciar bot |
| POST | `/api/v1/bot/stop` | Parar bot |
| POST | `/api/v1/bot/test-run` | Executar teste único |

### Configuração

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/bot/config` | Obter configurações |
| PUT | `/api/v1/bot/config` | Atualizar configurações |
| POST | `/api/v1/bot/config/reset` | Resetar para padrão |

### Logs e Histórico

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/bot/runs` | Listar execuções |
| GET | `/api/v1/bot/logs` | Listar logs |
| GET | `/api/v1/bot/logs/{run_id}` | Logs de uma execução |

## Deploy em Produção

### Railway

1. Criar projeto no Railway
2. Adicionar PostgreSQL e Redis (plugins)
3. Conectar repositório GitHub
4. Configurar variáveis de ambiente

### Render

```yaml
# render.yaml
services:
  - type: web
    name: bot-saas-api
    env: docker
    dockerfilePath: ./Dockerfile.api
    
  - type: worker
    name: bot-saas-worker
    env: docker
    dockerfilePath: ./Dockerfile.worker
```

## Segurança

- JWT com expiração de 24h
- Senhas hash com bcrypt
- Credenciais criptografadas com Fernet
- RBAC (Admin, User, Viewer)
- Rate limiting por IP
- Isolamento de sessões por tenant

## Licença

MIT
