# Teste da Plataforma SaaS

## 🧪 Testes Manuais

### 1. Verificar Infraestrutura

```bash
# Verificar containers
docker compose ps

# Todos devem estar "Up":
# - postgres
# - redis  
# - api
# - worker
# - beat
# - frontend
```

### 2. Testar API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Resposta esperada:
# {"status": "healthy", "version": "1.0.0", ...}
```

### 3. Registrar Usuário

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@exemplo.com",
    "password": "senha123",
    "full_name": "Usuário Teste",
    "tenant_name": "Empresa Teste"
  }'
```

### 4. Fazer Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=teste@exemplo.com&password=senha123"

# Salvar o access_token retornado
```

### 5. Verificar Configurações

```bash
curl http://localhost:8000/api/v1/config \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 6. Atualizar Configurações

```bash
curl -X PUT http://localhost:8000/api/v1/config \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "source_urls": ["https://facebook.com/groups/exemplo"],
    "interval_seconds": 120
  }'
```

### 7. Iniciar Bot

```bash
curl -X POST http://localhost:8000/api/v1/bot/start \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 8. Verificar Status

```bash
curl http://localhost:8000/api/v1/bot/status \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 9. Ver Logs

```bash
curl "http://localhost:8000/api/v1/logs?limit=10" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## ✅ Checklist de Validação

- [ ] Containers iniciando corretamente
- [ ] Health check retorna healthy
- [ ] Registro de usuário funciona
- [ ] Login retorna JWT token
- [ ] Token permite acesso a rotas protegidas
- [ ] Configurações são salvas no banco
- [ ] Bot inicia via API
- [ ] Worker processa tasks
- [ ] Logs são registrados
- [ ] Frontend carrega e conecta à API

## 🐛 Debug

### Ver logs do worker
```bash
docker compose logs -f worker
```

### Ver logs da API
```bash
docker compose logs -f api
```

### Acessar banco de dados
```bash
docker compose exec postgres psql -U postgres -d bot_saas
```

### Verificar Redis
```bash
docker compose exec redis redis-cli
> KEYS *
> GET celery-task-meta-*
```

## 📊 Métricas

### Flower Dashboard
Acesse: http://localhost:5555

Verifique:
- Workers ativos
- Tasks em queue
- Taxa de sucesso/falha
