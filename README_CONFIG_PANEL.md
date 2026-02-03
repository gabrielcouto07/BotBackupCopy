# 🤖 Bot de Afiliados - Painel de Configuração

Interface web moderna para gerenciar todas as configurações do bot de afiliados de forma dinâmica.

## 📋 Requisitos

- Python 3.8+
- Node.js 14+
- npm ou yarn

## 🚀 Como Executar

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

## 🎯 Funcionalidades

✅ **Configurações do Chrome**
- Diretório de dados do Chrome
- Nome do perfil
- Modo headless

✅ **Configurações Gerais**
- Diretório de downloads
- Tag de afiliado do Mercado Livre
- Emoji superhero

✅ **Timing & Performance**
- Intervalo de polling
- Delays e timeouts
- Ciclos de reinicialização

✅ **Modo Noturno**
- Ativar/desativar
- Horários de início e término

✅ **Gatilhos de Marketing**
- Lista editável de gatilhos
- Probabilidade de uso

✅ **Pares de Canais**
- Configurar source → target
- Descrições personalizadas

✅ **Links de Grupos**
- Gerenciar links do WhatsApp
- Adicionar/remover grupos

## 💾 Como Funciona

1. O frontend React se conecta à API Flask
2. A API lê o arquivo `config.py` e extrai as configurações
3. Você edita as configurações na interface web
4. Ao salvar, a API reescreve o `config.py` com as novas configurações
5. Reinicie o bot para aplicar as mudanças

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

## 📝 Observações

- As configurações são salvas diretamente no `config.py`
- Certifique-se de fazer backup antes de usar
- Após salvar, reinicie o bot para aplicar as mudanças
- A API e o frontend devem estar rodando simultaneamente

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
