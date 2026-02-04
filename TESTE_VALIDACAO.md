# ✅ Checklist de Validação do Sistema

Este documento ajuda a confirmar que todas as partes do sistema estão funcionando corretamente.

## 🔍 Pré-requisitos

- [ ] Python 3.8+ instalado (`python --version`)
- [ ] Node.js 14+ instalado (`node --version`)
- [ ] npm instalado (`npm --version`)
- [ ] Chrome/Chromium instalado
- [ ] WhatsApp Web logado em um perfil do Chrome

## 📋 Checklist de Instalação

### Backend
- [ ] Dependências instaladas (`pip install -r backend/requirements_api.txt`)
- [ ] Arquivo `config.py` existe em `backend/`
- [ ] API Flask inicia sem erros (`python backend/api_config.py`)
- [ ] Endpoint `/api/health` responde OK

### Frontend
- [ ] Dependências instaladas (`npm install` em `frontend/`)
- [ ] Servidor React inicia sem erros (`npm start` em `frontend/`)
- [ ] Navegador abre automaticamente em `http://localhost:3000`

## ✨ Checklist de Funcionalidades

### 1. Auto-carregamento de Configurações

**Teste:**
1. Abra o painel em `http://localhost:3000`
2. Verifique se os campos estão preenchidos com valores do `config.py`

**Resultado Esperado:**
- ✅ Campos de Chrome profile preenchidos
- ✅ Tag de afiliado aparece (se configurada)
- ✅ Lista de gatilhos carregada
- ✅ Pares de canais aparecem
- ✅ Links de grupos visíveis

**Status:** [ ] Passou / [ ] Falhou

---

### 2. Salvar Configurações

**Teste:**
1. Altere qualquer campo (ex: adicione um novo gatilho)
2. Clique em "💾 Salvar Configurações"
3. Verifique mensagem de sucesso
4. Abra `backend/config.py` em um editor de texto
5. Confirme que as alterações foram salvas

**Resultado Esperado:**
- ✅ Mensagem "✅ Configurações salvas com sucesso!" aparece
- ✅ Arquivo `config.py` foi atualizado
- ✅ Valores persistidos corretamente

**Status:** [ ] Passou / [ ] Falhou

---

### 3. Botão de Play (Iniciar Bot)

**Teste:**
1. Clique em "▶️ Iniciar Bot"
2. Verifique mensagem de confirmação
3. Abra o Gerenciador de Tarefas (Ctrl+Shift+Esc)
4. Procure por processo Python relacionado ao bot

**Resultado Esperado:**
- ✅ Mensagem "▶️ Bot iniciado com sucesso!" aparece
- ✅ Processo Python aparece no Gerenciador de Tarefas
- ✅ Chrome/navegador pode abrir (se não estiver em headless)

**Status:** [ ] Passou / [ ] Falhou

---

### 4. Validação de Campos

**Teste:**
1. Tente diferentes valores nos campos
2. Verifique se números aceitam apenas números
3. Verifique se checkboxes funcionam
4. Teste adicionar/remover itens de listas

**Resultado Esperado:**
- ✅ Campos numéricos aceitam apenas números
- ✅ Checkboxes alternam True/False
- ✅ Botões "Adicionar" funcionam
- ✅ Botões "Remover" funcionam
- ✅ Mudanças refletidas ao salvar

**Status:** [ ] Passou / [ ] Falhou

---

### 5. Interface Responsiva

**Teste:**
1. Redimensione a janela do navegador
2. Teste em diferentes tamanhos
3. Verifique scroll se necessário

**Resultado Esperado:**
- ✅ Layout se adapta a diferentes tamanhos
- ✅ Todos os elementos permanecem acessíveis
- ✅ Botões clicáveis em qualquer tamanho

**Status:** [ ] Passou / [ ] Falhou

---

### 6. Gestão de Gatilhos

**Teste:**
1. Clique em "➕ Adicionar Gatilho"
2. Digite um novo gatilho
3. Clique em "🗑️ Remover" em um gatilho existente
4. Salve as configurações
5. Recarregue a página

**Resultado Esperado:**
- ✅ Novo gatilho adicionado à lista
- ✅ Gatilho removido desaparece
- ✅ Alterações persistem após recarregar
- ✅ `config.py` reflete as mudanças

**Status:** [ ] Passou / [ ] Falhou

---

### 7. Gestão de Pares de Canais

**Teste:**
1. Clique em "➕ Adicionar Par de Canais"
2. Preencha source, target e descrição
3. Clique em "🗑️ Remover Par" em um existente
4. Salve as configurações

**Resultado Esperado:**
- ✅ Novo par adicionado com 3 campos
- ✅ Par removido desaparece
- ✅ Valores salvos em `config.py` no formato correto
- ✅ Tuplas Python geradas corretamente

**Status:** [ ] Passou / [ ] Falhou

---

### 8. Gestão de Links de Grupos

**Teste:**
1. Clique em "➕ Adicionar Link de Grupo"
2. Preencha nome do grupo e link
3. Remova um link existente
4. Salve as configurações

**Resultado Esperado:**
- ✅ Novo link adicionado
- ✅ Link removido desaparece
- ✅ Dicionário Python gerado corretamente em `config.py`
- ✅ Links persistem após recarregar

**Status:** [ ] Passou / [ ] Falhou

---

### 9. Modo Noturno

**Teste:**
1. Ative o checkbox "Ativar Modo Noturno"
2. Configure horários (ex: 1 às 8)
3. Salve
4. Verifique no `config.py`

**Resultado Esperado:**
- ✅ `NIGHT_MODE_ENABLED = True` no config
- ✅ `NIGHT_START_HOUR` e `NIGHT_END_HOUR` corretos
- ✅ Valores numéricos válidos (0-23)

**Status:** [ ] Passou / [ ] Falhou

---

### 10. Comunicação Backend-Frontend

**Teste:**
1. Com o painel aberto, pare a API (Ctrl+C no terminal)
2. Tente salvar configurações
3. Reinicie a API
4. Tente novamente

**Resultado Esperado:**
- ✅ Erro exibido quando API está offline
- ✅ Mensagem de erro clara e descritiva
- ✅ Sucesso quando API volta online

**Status:** [ ] Passou / [ ] Falhou

---

## 🎯 Teste de Integração Completa

### Fluxo End-to-End

**Cenário:** Configurar e iniciar o bot do zero

**Passos:**
1. [ ] Execute `start_config_panel.bat`
2. [ ] Aguarde abertura automática do navegador
3. [ ] Verifique se configurações foram carregadas
4. [ ] Modifique pelo menos 3 configurações diferentes:
   - [ ] Tag de afiliado
   - [ ] Adicione um gatilho
   - [ ] Adicione um par de canais
5. [ ] Clique em "💾 Salvar Configurações"
6. [ ] Aguarde confirmação de sucesso
7. [ ] Clique em "▶️ Iniciar Bot"
8. [ ] Aguarde confirmação de inicialização
9. [ ] Verifique processo no Gerenciador de Tarefas
10. [ ] Abra `backend/config.py` e confirme mudanças

**Resultado:** [ ] Sucesso Total / [ ] Sucesso Parcial / [ ] Falhou

**Observações:**
```
[Escreva aqui qualquer problema encontrado]
```

---

## 🐛 Problemas Conhecidos e Soluções

### Problema: "Erro ao carregar configurações"
**Solução:** 
- Verifique se a API está rodando
- Confirme que `config.py` existe e tem sintaxe válida
- Veja logs no terminal da API

### Problema: "Erro ao salvar"
**Solução:**
- Feche `config.py` se estiver aberto em editor
- Verifique permissões de escrita
- Confirme que não há erros de sintaxe nos valores

### Problema: Bot não inicia
**Solução:**
- Verifique se `run_bot.pyw` existe
- Confirme que Python está no PATH
- Veja se todas dependências do bot estão instaladas

---

## ✅ Resumo de Validação

Data do Teste: _______________
Testado por: _______________

**Resultados:**
- Testes Passados: ___ / 10
- Teste de Integração: [ ] Sucesso / [ ] Falhou

**Sistema Pronto para Produção:** [ ] Sim / [ ] Não

**Próximos Passos:**
```
[Liste o que precisa ser feito antes de usar em produção]
```

---

## 📞 Suporte

Se algum teste falhou e você não consegue resolver:
1. Verifique os logs detalhados nos terminais
2. Consulte README.md e README_CONFIG_PANEL.md
3. Abra o console do navegador (F12) para erros JavaScript
4. Entre em contato com o desenvolvedor com:
   - Qual teste falhou
   - Mensagem de erro completa
   - Screenshots se possível
