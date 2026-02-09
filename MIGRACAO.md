# Guia de Migração: Bot Original → SaaS Multi-Tenant

## 📋 Resumo da Transformação

Este documento descreve a migração do Bot original para a arquitetura SaaS multi-tenant.

## 🔄 O Que Mudou

### Arquitetura Anterior (Monolítica)
```
backend/
├── main.py           # Script único
├── settings.json     # Config local
├── sender_*.py       # Envio direto
└── watcher.py        # Loop infinito
```

### Nova Arquitetura (SaaS)
```
app/
├── api/              # REST API
├── worker/           # Celery distribuído
├── db/               # PostgreSQL multi-tenant
└── core/             # Auth, crypto, config
```

## 🔁 Mapeamento de Funcionalidades

| Original | SaaS | Descrição |
|----------|------|-----------|
| `settings.json` | `bot_configs` table | Configurações no banco |
| `main.py` loop | Celery tasks | Execução distribuída |
| Arquivo local | PostgreSQL | Persistência robusta |
| Sem auth | JWT + tenants | Multi-tenant seguro |
| `state_*.txt` | Redis + DB | Estado distribuído |

## 📁 Mapeamento de Arquivos

### Backend Original → SaaS

| Arquivo Original | Novo Local | Função |
|-----------------|------------|--------|
| `backend/main.py` | `app/worker/bot_logic.py` | Lógica do bot |
| `backend/watcher.py` | `app/worker/tasks.py` | Task Celery |
| `backend/extractor.py` | `app/worker/bot_logic.py` | Integrado na lógica |
| `backend/sender_facebook.py` | `app/worker/bot_logic.py` | Envio via Playwright |
| `backend/sender_whatsapp.py` | `app/worker/bot_logic.py` | Envio via Playwright |
| `backend/config.py` | `app/core/config.py` | Settings Pydantic |
| `backend/storage.py` | `app/db/database.py` | PostgreSQL |
| `backend/dedup.py` | Redis cache | Deduplicação |
| `backend/affiliate.py` | `app/worker/bot_logic.py` | Links afiliados |
| `backend/settings.json` | Tabela `bot_configs` | Config no banco |

### Frontend Original → SaaS

| Original | Novo Local | Função |
|----------|------------|--------|
| `frontend/` | `frontend-saas/` | Dashboard completo |
| Painel simples | Multi-page app | Login, config, logs |

## 🔧 Configurações

### Antes (settings.json)
```json
{
  "source_urls": ["url1", "url2"],
  "interval": 60,
  "groups": ["grupo1"]
}
```

### Depois (API + Banco)
```sql
SELECT * FROM bot_configs WHERE tenant_id = ?;
```

```python
config = await get_config(tenant_id)
```

## 🔐 Autenticação

### Antes
- Sem autenticação
- Qualquer um acessa

### Depois
- JWT obrigatório
- Tenant isolation
- Roles (admin, member)

## 📊 Logs e Monitoramento

### Antes
- Arquivos de texto
- Sem estrutura
- Difícil debug

### Depois
- Tabela `bot_logs`
- Estruturado (JSON)
- Dashboard visual
- Filtros por run/tenant

## 🚀 Deploy

### Antes
```bash
python main.py
# Roda em uma máquina
```

### Depois
```bash
docker compose up -d
# Múltiplos containers
# Escalável horizontalmente
```

## 📝 Checklist de Migração

- [x] Criar estrutura de diretórios
- [x] Criar schema do banco
- [x] Implementar API FastAPI
- [x] Implementar Worker Celery
- [x] Configurar Playwright no worker
- [x] Criar frontend React
- [x] Configurar Docker
- [x] Documentação

## 🔄 Próximos Passos

1. **Testar localmente**
   - Rodar `docker compose up`
   - Criar usuário teste
   - Configurar bot
   - Verificar execução

2. **Ajustar lógica do bot**
   - Migrar código específico de `main.py`
   - Adaptar extractors
   - Configurar credenciais

3. **Deploy produção**
   - Configurar servidor
   - Domínio e SSL
   - Backup automático

## ⚠️ Notas Importantes

1. **Credenciais**: Agora são criptografadas no banco
2. **Sessões**: Playwright salva estado por tenant
3. **Concorrência**: Locks evitam execução duplicada
4. **Logs**: Tudo é rastreável por tenant/run
