# 🤖 Bot de Afiliados para WhatsApp

Bot inteligente para automação de marketing de afiliados no WhatsApp, com painel de controle web moderno e intuitivo.

## 📖 Visão Geral

Este bot monitora canais/grupos do WhatsApp em busca de ofertas e promoções, processa links de produtos (especialmente do Mercado Livre), adiciona sua tag de afiliado e redistribui automaticamente para seus grupos de destino. Tudo isso com um painel web para configuração em tempo real.

### ✨ Principais Funcionalidades

- 🔍 **Monitoramento Automático**: Verifica mensagens em canais/grupos configurados
- 🔗 **Conversão de Links**: Transforma links normais em links de afiliado
- 🎯 **Gatilhos de Marketing**: Adiciona frases de impacto nas mensagens
- 📱 **Multimídia**: Suporta imagens, vídeos e documentos
- 🌙 **Modo Noturno**: Pausa automática durante horários definidos
- 🎨 **Painel Web**: Interface moderna para configuração em tempo real
- ⚡ **Inicialização Rápida**: Inicie o bot diretamente do painel web
- 💾 **Auto-carregamento**: Configurações carregadas automaticamente ao abrir

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.8 ou superior
- Node.js 14 ou superior
- Google Chrome/Chromium
- Conta WhatsApp Web logada em um perfil do Chrome

### Instalação Rápida

```bash
# Clone o repositório
git clone <seu-repositorio>
cd BotBackupCopy

# Execute o script de inicialização (Windows)
start_config_panel.bat
```

O script irá:
1. ✅ Instalar dependências do Python
2. ✅ Instalar dependências do Node.js
3. ✅ Iniciar a API Flask (backend)
4. ✅ Iniciar o servidor React (frontend)
5. ✅ Abrir o painel no navegador

### Instalação Manual

#### Backend (API)

```bash
cd backend
pip install -r requirements_api.txt
python api_config.py
```

#### Frontend (Painel Web)

```bash
cd frontend
npm install
npm start
```

## 🎯 Como Usar

### 1. Configure o Perfil do Chrome

1. Abra o Chrome e faça login no WhatsApp Web
2. Anote o caminho do perfil (geralmente em `C:\Users\<usuario>\AppData\Local\Google\Chrome\User Data`)
3. Configure este caminho no painel web

### 2. Acesse o Painel de Controle

Abra `http://localhost:3000` no navegador. Você verá todas as configurações já preenchidas com os valores atuais do `config.py`.

### 3. Configure suas Preferências

#### 🌐 Chrome e Navegador
- **Diretório de dados**: Caminho do perfil do Chrome
- **Nome do perfil**: Geralmente "Default"
- **Modo headless**: Desative para desenvolvimento, ative para produção

#### ⚙️ Configurações Gerais
- **Tag de afiliado ML**: Sua tag do programa de afiliados do Mercado Livre
- **Diretório de downloads**: Onde salvar mídias temporárias
- **Emoji superhero**: Personalize suas mensagens

#### ⏱️ Timing e Performance
- **Intervalo de polling**: Frequência de verificação (padrão: 180s)
- **Reiniciar a cada X ciclos**: Previne vazamento de memória (padrão: 40)
- **Timeout de ciclo**: Tempo máximo por verificação

#### 🌙 Modo Noturno
- Ative para pausar o bot durante a madrugada
- Configure horário de início e término
- Economiza recursos e evita spam

#### 🔥 Gatilhos de Marketing
- Adicione frases de impacto: "⚡ CORRE!", "🔥 OFERTA IMPERDÍVEL!"
- Configure a probabilidade de uso (0.0 a 1.0)
- Aumenta engajamento das mensagens

#### 📢 Pares de Canais
- **Source**: Canal de origem (onde o bot monitora)
- **Target**: Canal de destino (onde o bot envia)
- **Descrição**: Identifique cada par facilmente

Exemplo:
```
Source: "Herói da Promo #731"
Target: "Super Promos"
Descrição: "Herói da Promo"
```

#### 🔗 Links de Grupos
- Adicione links de convite dos seus grupos
- Bot pode enviar estes links automaticamente
- Formato: `https://chat.whatsapp.com/XXXXX`

### 4. Salve e Inicie

1. Clique em **"💾 Salvar Configurações"**
2. Aguarde confirmação de sucesso
3. Clique em **"▶️ Iniciar Bot"**
4. O bot começará a monitorar e processar mensagens

## 📁 Estrutura do Projeto

```
BotBackupCopy/
├── README.md                    # Este arquivo
├── README_CONFIG_PANEL.md       # Documentação detalhada do painel
├── start_config_panel.bat       # Script de inicialização rápida
│
├── backend/                     # Backend Python
│   ├── config.py               # Configurações do bot
│   ├── api_config.py           # API Flask para o painel
│   ├── main.py                 # Lógica principal do bot
│   ├── run_bot.pyw             # Executor do bot (sem console)
│   ├── watcher.py              # Monitor de mensagens
│   ├── extractor.py            # Extrator de links
│   ├── affiliate.py            # Processador de afiliados
│   ├── sender_whatsapp.py      # Envio de mensagens
│   ├── storage.py              # Persistência de dados
│   ├── requirements_api.txt    # Dependências da API
│   └── ...
│
└── frontend/                    # Frontend React
    ├── package.json
    ├── public/
    │   └── index.html
    └── src/
        ├── App.js              # Componente principal
        ├── App.css             # Estilos do painel
        ├── index.js
        └── index.css
```

## 🔧 Tecnologias Utilizadas

### Backend
- **Python 3.8+**: Linguagem principal
- **Selenium**: Automação do WhatsApp Web
- **Flask**: API REST para o painel
- **Flask-CORS**: Comunicação frontend-backend

### Frontend
- **React 18**: Framework UI
- **Axios**: Requisições HTTP
- **CSS3**: Estilização moderna com gradientes

## 🛡️ Segurança e Boas Práticas

- ✅ Nunca compartilhe seu `config.py` com tags de afiliado
- ✅ Faça backup regular das configurações
- ✅ Use modo headless em produção
- ✅ Configure limites de mensagens para evitar banimento
- ✅ Respeite os termos de uso do WhatsApp
- ✅ Não faça spam

## 📊 Monitoramento

O bot salva o estado em:
- `state_last_seen.txt`: Última mensagem processada
- `ml_affiliate_network_dump.json`: Cache de redes de afiliados

## 🐛 Solução de Problemas

### Bot não inicia
```bash
# Verifique se o Chrome profile está correto
# Verifique se o WhatsApp Web está logado
# Veja os logs no console
```

### Painel não carrega configurações
```bash
# Verifique se a API está rodando
curl http://localhost:5000/api/health

# Deve retornar: {"status":"ok"}
```

### Configurações não salvam
- Feche o arquivo `config.py` se estiver aberto
- Verifique permissões de escrita
- Veja logs do Flask no terminal

## 📝 Logs e Debug

- **API Flask**: Logs aparecem no terminal onde você executou `api_config.py`
- **Frontend React**: Erros no Console do navegador (F12)
- **Bot**: Logs no terminal onde foi iniciado (ou verificar arquivos de log se configurado)

## 🔄 Atualizações

Para atualizar o bot:
```bash
git pull
cd backend && pip install -r requirements_api.txt
cd ../frontend && npm install
```

## 📄 Licença

Este projeto é privado e proprietário. Todos os direitos reservados.

## 🤝 Contribuindo

Este é um projeto privado. Para contribuir, entre em contato com o desenvolvedor.

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a seção de **Solução de Problemas**
2. Consulte o [README_CONFIG_PANEL.md](README_CONFIG_PANEL.md) para detalhes do painel
3. Entre em contato com o desenvolvedor

---

**Desenvolvido com ❤️ para automatizar e otimizar seu marketing de afiliados**

**⚠️ Aviso Legal**: Use este bot de forma responsável e em conformidade com os termos de serviço do WhatsApp e das plataformas de afiliados.
