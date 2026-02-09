# 🤖 PROMPT TÉCNICO - Bot de Afiliados WhatsApp + Facebook

Use este prompt para contextualizar qualquer IA sobre este projeto e pedir orientações.

---

## 📋 DESCRIÇÃO DO PROJETO

Este é um **bot automatizado de marketing de afiliados** que:

1. **Monitora grupos fonte do WhatsApp** (grupos de promoções de terceiros)
2. **Extrai mensagens com imagens e links** de produtos (Mercado Livre ou Amazon)
3. **Converte links para links afiliados** usando as tags do usuário
4. **Reposta automaticamente** em um grupo destino do WhatsApp com a mensagem modificada
5. **Posta também no Facebook** (opcional) em uma página, rotacionando entre os grupos fonte

---

## 🏗️ ARQUITETURA DO SISTEMA

```
Bot-main - Facebook/
├── backend/                    # Core do bot + API
│   ├── main.py                 # Loop principal de monitoramento
│   ├── watcher.py              # Extração de mensagens do WhatsApp
│   ├── sender_whatsapp.py      # Envio de mensagens no WhatsApp
│   ├── sender_facebook.py      # Postagem no Facebook
│   ├── affiliate.py            # Geração de links afiliados (ML + Amazon)
│   ├── extractor.py            # Processamento de texto e URLs
│   ├── dedup.py                # Sistema de deduplicação (evita reposts)
│   ├── storage.py              # Persistência do último ID de mensagem
│   ├── config.py               # Carrega configurações do settings.json
│   ├── settings.json           # Arquivo de configurações editável
│   ├── api.py                  # API Flask para o painel de configuração
│   └── dedup_cache.json        # Cache de produtos já enviados
│
├── frontend/                   # Painel de configuração React
│   ├── src/App.js              # Interface React com abas
│   ├── src/App.css             # Estilo dark mode moderno
│   └── package.json            # Dependências npm
│
└── start_config_panel.bat      # Script para iniciar API + Frontend
```

---

## 🔧 TECNOLOGIAS UTILIZADAS

| Componente | Tecnologia |
|------------|------------|
| **Automação Web** | Playwright (Python) - controla Chrome real |
| **Backend API** | Flask + flask-cors |
| **Frontend** | React 18.2 + Axios |
| **Navegador** | Chrome com perfil persistente (mantém login) |
| **Linguagem** | Python 3.10+ |

---

## 📦 MÓDULOS E SUAS FUNÇÕES

### 1. `main.py` - Orquestrador Principal
```python
# Responsabilidades:
- Inicializa navegador Chrome com Playwright
- Abre 3 abas: WhatsApp Web, Mercado Livre/Amazon, Facebook
- Executa loop infinito de monitoramento
- Gerencia ciclos (a cada X minutos verifica todos os grupos)
- Reinício preventivo a cada N ciclos
- Modo noturno (pausa entre 01:00-08:00)
- Rotação de logs automática
- Tratamento de exceções com reinício automático

# Fluxo do loop:
1. Para cada par (source → target):
   - Abre o chat source
   - Extrai última mensagem (texto + URLs + imagem)
   - Compara ID da mensagem com o último salvo
   - Se novo: processa e envia para target
   - Salva novo ID
2. A cada X minutos: posta no Facebook (se ativado)
3. Aguarda POLL_SECONDS antes do próximo ciclo
```

### 2. `watcher.py` - Extração de Mensagens
```python
# Funções principais:
- open_chat(page, chat_name)         # Abre um chat pelo nome
- get_last_message_bubble(page)      # Retorna última bolha de mensagem
- extract_last_message_text_and_urls(page)  # Extrai texto + links
- get_last_message_id(page)          # Extrai ID único da mensagem (data-id do DOM)
- compute_msg_id(text, urls)         # Fallback: gera hash do conteúdo
- has_image(bubble)                  # Verifica se tem imagem
- download_last_image(page, dir, group)  # Baixa imagem para disco

# Detalhes técnicos:
- Extrai texto preservando formatação WhatsApp (*negrito*, _itálico_)
- Remove metadados (horário, "Encaminhada")
- Corta texto após o link (remove lixo)
- Usa seletores CSS específicos do WhatsApp Web
```

### 3. `affiliate.py` - Geração de Links Afiliados
```python
# Mercado Livre:
- Navega para URL /sec/ do produto
- Clica em "Ir para produto" se necessário (minutoreview)
- Captura token CSRF da página de afiliados
- Chama API interna do ML para gerar link afiliado
- Retorna link no formato mercadolivre.com.br/MLB-xxx?matt_tool=xxx

# Amazon:
- Extrai ASIN do produto da URL
- Expande links curtos (amzn.to)
- Gera link limpo com tag de afiliado
- Formato: amazon.com.br/dp/ASIN?tag=xxx

# Regex utilizados:
- ASIN: /dp/([A-Z0-9]{10})
- ML SEC: mercadolivre.com(.br)?/sec/[A-Za-z0-9]+
- ML Product: /p/(ML[A-Z][0-9]+)
```

### 4. `sender_whatsapp.py` - Envio no WhatsApp
```python
# Funções:
- send_image_with_caption(page, chat, img_path, caption)
  1. Abre chat destino
  2. Clica em "Anexar"
  3. Seleciona "Fotos e vídeos"
  4. Faz upload via file chooser
  5. Digita legenda com quebras de linha (Shift+Enter)
  6. Adiciona link do grupo no final
  7. Envia

# Retry automático em caso de falha (3 tentativas)
```

### 5. `sender_facebook.py` - Postagem no Facebook
```python
# Funções:
- send_facebook_post(page, page_url, text, image_path)
  1. Navega para a página do Facebook
  2. Clica em "No que você está pensando?"
  3. Abre modal de post
  4. Digita texto primeiro
  5. Anexa imagem depois
  6. Clica em "Publicar"

# Particularidades:
- Remove formatação WhatsApp do texto
- Adiciona convite para grupo WhatsApp no final
- Rotaciona entre os grupos fonte a cada post
```

### 6. `dedup.py` - Sistema de Deduplicação
```python
# Objetivo: Evitar repostar o mesmo produto em menos de X horas

# Como funciona:
1. Extrai ID único do produto da URL:
   - Amazon: ASIN (10 caracteres)
   - ML: ID do /sec/ ou MLB-xxx
2. Também extrai IDs do texto (fallback)
3. Chave: "GRUPO:PRODUTO_ID"
4. Salva timestamp no cache
5. Bloqueia se diferença < DEDUP_WINDOW_HOURS

# Cache persistido em dedup_cache.json
# Limitado a 500 entradas (remove mais antigos)
```

### 7. `storage.py` - Persistência de Estado
```python
# Arquivo: state_last_seen.txt
# Formato: grupo|msg_id|preview

# Funções:
- get_last_seen(group_name)  # Carrega último ID
- save_last_seen(msg_id, group_name, preview)  # Salva novo ID

# Permite retomar de onde parou após reinício
```

### 8. `config.py` - Configurações
```python
# Carrega settings.json e exporta variáveis globais

# Configurações editáveis via frontend:
- MELI_AFFILIATE_TAG      # Tag do Mercado Livre
- AMAZON_AFFILIATE_TAG    # Tag da Amazon
- AMAZON_ENABLED          # Ativar/desativar Amazon
- FACEBOOK_ENABLED        # Ativar/desativar Facebook
- FACEBOOK_PAGE_URL       # URL da página do Facebook
- FACEBOOK_POST_INTERVAL  # Intervalo entre posts (minutos)
- GROUP_LINK              # Link do grupo WhatsApp
- CHANNEL_PAIRS           # Lista de (source, target, description)
- POLL_SECONDS            # Intervalo entre ciclos
- DEDUP_WINDOW_HOURS      # Janela de bloqueio de duplicatas
- NIGHT_MODE_*            # Configurações do modo noturno
- GATILHOS                # Frases de urgência ("CORRE!", etc)
- GATILHO_CHANCE          # Probabilidade de adicionar gatilho

# Configurações fixas:
- CHROME_USER_DATA_DIR    # Pasta do perfil Chrome
- HEADLESS = True         # Executa sem interface
- RESTART_EVERY_CYCLES    # Reinício preventivo
```

### 9. `api.py` - API REST
```python
# Endpoints:
GET  /api/settings           # Retorna todas configurações
POST /api/settings           # Salva todas configurações
GET  /api/settings/<section> # Retorna seção específica
PUT  /api/settings/<section> # Atualiza seção

GET  /api/channel-pairs      # Lista pares de canais
POST /api/channel-pairs      # Adiciona par
PUT  /api/channel-pairs/<i>  # Atualiza par
DEL  /api/channel-pairs/<i>  # Remove par

GET  /api/bot/status         # Status do bot (running, pid)
POST /api/bot/start          # Inicia o bot
POST /api/bot/stop           # Para o bot
POST /api/bot/restart        # Reinicia o bot

GET  /api/health             # Health check

# Porta: 5000
```

### 10. `frontend/src/App.js` - Painel de Configuração
```javascript
// Interface React com 5 abas:

1. AFILIADOS
   - Tag do Mercado Livre
   - Tag da Amazon
   - Toggle Amazon ativado

2. CANAIS
   - Lista de pares (source → target)
   - Adicionar/remover/ativar/desativar

3. PLATAFORMAS
   - Facebook ativado
   - URL da página
   - Intervalo de posts
   - Link do grupo WhatsApp

4. TIMING
   - Intervalo entre ciclos
   - Janela de deduplicação
   - Modo noturno

5. GATILHOS
   - Lista de frases de urgência
   - Probabilidade de uso

// Footer com:
- Status do bot (rodando/parado)
- Botões: Iniciar, Parar, Salvar, Salvar e Iniciar
```

---

## ⚙️ CONFIGURAÇÕES ATUAIS (settings.json)

```json
{
  "affiliate": {
    "meli_tag": "silvagabriel20230920180155",
    "amazon_tag": "superprom03bb-20",
    "amazon_enabled": true
  },
  "facebook": {
    "enabled": false,
    "page_url": "https://www.facebook.com/profile.php?id=61587267939249",
    "post_interval_minutes": 30
  },
  "whatsapp": {
    "group_link": "https://chat.whatsapp.com/Hd8UFqVrs1dGxdhq477syJ"
  },
  "channel_pairs": [
    {"source": "Herói da Promo #731", "target": "Super Promos [21]", "enabled": true},
    {"source": "Home Deals [12]", "target": "Super Promos [21]", "enabled": true},
    {"source": "Tech Deals 🎯 [20]", "target": "Super Promos [21]", "enabled": true},
    {"source": "Parfum Deals 👔 [15]", "target": "Super Promos [21]", "enabled": true},
    {"source": "Guerra Deals Fit [125]", "target": "Super Promos [21]", "enabled": true}
  ],
  "timing": {
    "poll_seconds": 180,
    "dedup_window_hours": 3,
    "night_mode_enabled": true,
    "night_start_hour": 1,
    "night_end_hour": 8
  },
  "triggers": {
    "enabled": true,
    "chance": 0.20,
    "list": ["⚡ CORRE!", "🔥 OFERTA IMPERDÍVEL!", "💰 PREÇO NUNCA VISTO!", "⏰ ÚLTIMAS UNIDADES!"]
  }
}
```

---

## 🔄 FLUXO COMPLETO DE EXECUÇÃO

```
1. INICIALIZAÇÃO
   ├── Carrega settings.json
   ├── Inicia Chrome com perfil persistente
   ├── Abre WhatsApp Web (aguarda QR code se necessário)
   ├── Abre Mercado Livre/Amazon (para gerar links)
   └── Abre Facebook (se ativado)

2. LOOP DE MONITORAMENTO (a cada 3 minutos)
   ├── Para cada par (source → target):
   │   ├── Abre grupo source
   │   ├── Extrai última mensagem
   │   ├── Verifica se tem imagem
   │   ├── Verifica se é nova (compara ID)
   │   ├── Verifica dedup (produto já enviado?)
   │   ├── Extrai URLs (ML ou Amazon)
   │   ├── Gera link afiliado
   │   ├── Processa texto (remove emoji, adiciona gatilho)
   │   ├── Baixa imagem
   │   ├── Envia para grupo target
   │   ├── Marca como enviado (dedup)
   │   └── Salva novo ID
   │
   ├── FACEBOOK (se ativado, a cada 30 min):
   │   ├── Usa próximo grupo da rotação
   │   ├── Extrai última mensagem
   │   ├── Gera link afiliado
   │   ├── Remove formatação WhatsApp
   │   ├── Adiciona link do grupo
   │   └── Posta na página
   │
   └── Aguarda próximo ciclo

3. TRATAMENTO DE ERROS
   ├── Timeout → Reinicia navegador
   ├── WhatsApp travado → Recarrega página
   ├── Erro de rede → Retry com backoff
   └── Crash → Reinício automático
```

---

## 🎯 PONTOS FORTES

1. **Perfil persistente**: Não precisa escanear QR code toda vez
2. **Deduplicação inteligente**: Evita spam do mesmo produto
3. **Rotação de fontes**: Facebook alterna entre grupos
4. **Modo noturno**: Não posta de madrugada
5. **Gatilhos de urgência**: Aumenta conversão
6. **Frontend amigável**: Configuração sem editar código
7. **Logs detalhados**: Fácil debug
8. **Reinício automático**: Resiliência a falhas

---

## ⚠️ LIMITAÇÕES ATUAIS

1. **Apenas 1 target**: Todos os sources vão para o mesmo grupo destino
2. **Sem métricas**: Não rastreia cliques ou conversões
3. **Sem agendamento**: Posts do Facebook são baseados em intervalo, não horário fixo
4. **Sem filtro de categorias**: Reposta qualquer produto
5. **Sem edição de mensagem**: Não permite customizar template
6. **Chrome obrigatório**: Não funciona com outros navegadores

---

## 📊 DADOS DE OPERAÇÃO

- **Ciclo padrão**: 3 minutos
- **Dedup window**: 3 horas (mesmo produto bloqueado por 3h)
- **Facebook interval**: 30 minutos
- **Grupos monitorados**: 5
- **Gatilho chance**: 20%
- **Horário noturno**: 01:00 - 08:00

---

## 🚀 COMO USAR ESTE PROMPT

Cole este documento inteiro em uma conversa com uma IA e pergunte:

1. "Como posso adicionar suporte a múltiplos grupos destino?"
2. "Como implementar métricas de cliques nos links?"
3. "Como adicionar filtro por categoria de produto?"
4. "Como melhorar a performance do bot?"
5. "Como adicionar suporte a Telegram além de WhatsApp?"
6. "Como implementar templates customizáveis para as mensagens?"
7. "Quais melhorias de segurança devo implementar?"

---

*Última atualização: Fevereiro 2026*
