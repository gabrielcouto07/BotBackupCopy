# 🤖 Bot de Afiliados - Painel de Configuração

Interface web moderna e intuitiva para gerenciar todas as configurações do bot de afiliados de forma dinâmica e em tempo real.

## ✨ Características Principais

- ✅ **Auto-carregamento**: Configurações carregadas automaticamente do `config.py` ao iniciar
- 🎯 **Interface Intuitiva**: Campos pré-preenchidos com valores atuais
- 🚀 **Iniciar Bot**: Botão de play para executar o bot diretamente do painel
- 💾 **Salvamento Dinâmico**: Alterações salvas instantaneamente no `config.py`
- 🎨 **Design Moderno**: Interface responsiva com gradientes e animações
- 📱 **Responsivo**: Funciona perfeitamente em desktop, tablet e mobile

## 📋 Requisitos

- Python 3.8+
- Node.js 14+ 
- npm ou yarn
- Chrome/Chromium instalado
- Perfil do Chrome configurado (para WhatsApp Web)

## 🚀 Início Rápido

### Opção Fácil: Use o Script Automático

```bash
# Windows
start_config_panel.bat
```

Este script irá:
1. Instalar dependências do backend
2. Instalar dependências do frontend
3. Iniciar a API Flask
4. Iniciar o servidor React
5. Abrir automaticamente o navegador

### Opção Manual: Passo a Passo

### 1️⃣ Backend (API Flask)

```bash
# Entre na pasta backend
cd backend

# Instale as dependências da API
pip install -r requirements_api.txt

# Execute a API
python api_config.py
```

A API estará rodando em: `http://localhost:5000`

### 2️⃣ Frontend (React)

```bash
# Entre na pasta frontend
cd frontend

# Instale as dependências
npm install

# Execute o frontend
npm start
```

O frontend abrirá automaticamente em: `http://localhost:3000`

## 🎯 Funcionalidades Detalhadas

### 🌐 Configurações do Chrome
- **Diretório de dados do Chrome**: Caminho para o perfil onde o WhatsApp Web está logado
- **Nome do perfil**: Nome do perfil do Chrome (geralmente "Default")
- **Modo headless**: Executar sem interface gráfica (para produção)

### ⚙️ Configurações Gerais
- **Diretório de downloads**: Pasta para salvar mídias baixadas
- **Tag de afiliado do Mercado Livre**: Sua tag de afiliado para gerar links
- **Emoji superhero**: Emoji personalizado para mensagens

### ⏱️ Timing & Performance
- **Intervalo de polling**: Tempo entre verificações de novas mensagens (padrão: 180s)
- **Delay de refresh de bolha**: Tempo para atualizar interface do WhatsApp
- **Reiniciar a cada X ciclos**: Reinicia o navegador para evitar vazamentos de memória
- **Timeout de ciclo**: Tempo máximo para um ciclo de verificação
- **Granularidade de sleep**: Precisão dos intervalos de espera

### 🌙 Modo Noturno
- **Ativar/desativar**: Liga ou desliga o modo noturno
- **Horários**: Define quando o bot deve pausar (ex: 01:00 às 08:00)
- **Economia de recursos**: Bot em standby durante a madrugada

### 🔥 Gatilhos de Marketing
- **Lista editável**: Adicione ou remova frases de impacto
- **Probabilidade de uso**: Define chance de adicionar gatilho (0.0 a 1.0)
- **Exemplos**: "⚡ CORRE!", "🔥 OFERTA IMPERDÍVEL!", "💰 PREÇO NUNCA VISTO!"

### 📢 Pares de Canais
- **Source → Target**: Define de qual canal pegar mensagens e para onde enviar
- **Descrições**: Identifique cada par facilmente
- **Múltiplos pares**: Configure vários canais simultaneamente

### 🔗 Links de Grupos WhatsApp
- **Gerenciamento fácil**: Adicione ou remova links de convite
- **Integração automática**: Bot usa esses links para convidar usuários
- **Organização**: Associe cada grupo ao seu link específico

### ▶️ Controle do Bot
- **Iniciar Bot**: Botão de play para executar o bot instantaneamente
- **Salvar Configurações**: Persiste todas as alterações no `config.py`
- **Feedback visual**: Mensagens de sucesso/erro em tempo real

## 💾 Como Funciona

### 🔄 Fluxo de Inicialização

1. **Ao abrir o painel**: 
   - Frontend React inicia e se conecta à API Flask
   - API lê automaticamente o arquivo `config.py`
   - Todas as configurações são extraídas e parseadas
   - Interface é preenchida com os valores atuais do `config.py`

2. **Durante a edição**:
   - Você modifica os campos na interface web
   - Alterações são mantidas em memória (React state)
   - Nenhuma mudança é salva até clicar em "Salvar"

3. **Ao salvar configurações**:
   - Frontend envia todas as configurações via POST para a API
   - API valida e reescreve o arquivo `config.py`
   - Mensagem de sucesso é exibida
   - Configurações estão prontas para serem usadas

4. **Ao iniciar o bot**:
   - Botão "▶️ Iniciar Bot" executa o `run_bot.pyw`
   - Bot carrega as configurações do `config.py` atualizado
   - Processo roda em background (modo pythonw)
   - Painel continua disponível para monitoramento

### 🎯 Arquitetura

```
┌─────────────────┐      HTTP/REST      ┌─────────────────┐
│                 │ ←─────────────────→  │                 │
│  React Frontend │                      │   Flask API     │
│  (Port 3000)    │                      │   (Port 5000)   │
│                 │                      │                 │
└─────────────────┘                      └────────┬────────┘
                                                  │
                                                  │ Read/Write
                                                  ↓
                                         ┌─────────────────┐
                                         │   config.py     │
                                         │  (Configurações)│
                                         └─────────────────┘
                                                  ↑
                                                  │ Import
                                                  │
                                         ┌─────────────────┐
                                         │   run_bot.pyw   │
                                         │  (Bot Principal)│
                                         └─────────────────┘
```

## 🎨 Interface

- Design moderno com gradientes
- Formulários organizados por seções
- Validação em tempo real
- Feedback visual ao salvar
- Responsivo (funciona em mobile)

## 🔧 Estrutura do Projeto

```
BotBackupCopy/
├── backend/
│   ├── config.py              # Configurações do bot
│   ├── api_config.py          # API Flask
│   └── requirements_api.txt   # Dependências da API
└── frontend/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── App.js             # Componente principal
    │   ├── App.css            # Estilos
    │   ├── index.js
    │   └── index.css
    └── package.json
```

## 📝 Observações Importantes

- ⚠️ **Backup**: Faça backup do `config.py` antes de usar pela primeira vez
- 🔄 **Auto-carregamento**: Configurações são carregadas automaticamente ao abrir o painel
- 💾 **Persistência**: Alterações são salvas diretamente no `config.py`
- ⚡ **Inicialização**: Use o botão "▶️ Iniciar Bot" para executar o bot
- 🔌 **Servidores**: API (port 5000) e Frontend (port 3000) devem estar rodando
- 🌐 **Navegador**: Abra `http://localhost:3000` para acessar o painel

## 🐛 Solução de Problemas

### Frontend não carrega configurações
```bash
# Verifique se a API está rodando
curl http://localhost:5000/api/health

# Deve retornar: {"status":"ok"}
```

### Erro ao salvar configurações
- Verifique se o arquivo `config.py` não está aberto em outro programa
- Confirme que você tem permissões de escrita na pasta `backend/`
- Verifique os logs da API Flask no terminal

### Bot não inicia
- Verifique se o arquivo `run_bot.pyw` existe em `backend/`
- Confirme que o Python está instalado e no PATH
- Verifique se as dependências do bot estão instaladas

### Porta já em uso
```bash
# Se a porta 5000 já estiver em uso, mude no arquivo api_config.py:
app.run(debug=True, port=5001)  # Mude para 5001

# E no frontend/src/App.js:
const API_URL = 'http://localhost:5001/api';  # Atualize aqui também
```

### Configurações não aparecem preenchidas
- Verifique se o `config.py` tem valores válidos
- Abra o console do navegador (F12) e veja se há erros
- Confirme que a API consegue ler o arquivo `config.py`

## 🛠️ Tecnologias

**Backend:**
- Flask (API REST)
- Flask-CORS (permitir requisições do React)

**Frontend:**
- React 18
- Axios (requisições HTTP)
- CSS moderno com gradientes

---

Feito com ❤️ para facilitar a gestão do seu bot de afiliados!
