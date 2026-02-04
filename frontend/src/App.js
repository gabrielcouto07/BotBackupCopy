import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [botRunning, setBotRunning] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadConfig();
    checkBotStatus();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      console.log('🔄 Carregando configurações do config.py...');
      const response = await axios.get(`${API_URL}/config`);
      if (response.data.success) {
        setConfig(response.data.config);
        console.log('✅ Configurações carregadas:', response.data.config);
        setMessage({ type: 'success', text: '✅ Configurações carregadas do config.py!' });
        setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      }
    } catch (error) {
      console.error('❌ Erro ao carregar:', error);
      setMessage({ type: 'error', text: 'Erro ao carregar configurações: ' + error.message });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage({ type: '', text: '' });
      const response = await axios.post(`${API_URL}/config`, config);
      if (response.data.success) {
        setMessage({ type: 'success', text: '✅ Configurações salvas com sucesso!' });
        setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      }
    } catch (error) {
      setMessage({ type: 'error', text: '❌ Erro ao salvar: ' + error.message });
    } finally {
      setSaving(false);
    }
  };

  const handleStartBot = async () => {
    try {
      setStarting(true);
      setMessage({ type: '', text: '' });
      const response = await axios.post(`${API_URL}/start-bot`);
      if (response.data.success) {
        setMessage({ type: 'success', text: '▶️ Bot iniciado com sucesso!' });
        setBotRunning(true);
        setTimeout(() => setMessage({ type: '', text: '' }), 5000);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.message;
      setMessage({ type: 'error', text: '❌ Erro ao iniciar bot: ' + errorMsg });
    } finally {
      setStarting(false);
    }
  };

  const handleStopBot = async () => {
    try {
      setStopping(true);
      setMessage({ type: '', text: '' });
      const response = await axios.post(`${API_URL}/stop-bot`);
      if (response.data.success) {
        setMessage({ type: 'success', text: '⏹️ Bot parado com sucesso!' });
        setBotRunning(false);
        setTimeout(() => setMessage({ type: '', text: '' }), 5000);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.message;
      setMessage({ type: 'error', text: '❌ Erro ao parar bot: ' + errorMsg });
    } finally {
      setStopping(false);
    }
  };

  const checkBotStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/bot-status`);
      setBotRunning(response.data.running);
    } catch (error) {
      console.error('Erro ao verificar status do bot:', error);
    }
  };

  const updateField = (field, value) => {
    setConfig({ ...config, [field]: value });
  };

  const updateGatilho = (index, value) => {
    const newGatilhos = [...(config.GATILHOS || [])];
    newGatilhos[index] = value;
    updateField('GATILHOS', newGatilhos);
  };

  const addGatilho = () => {
    updateField('GATILHOS', [...(config.GATILHOS || []), '']);
  };

  const removeGatilho = (index) => {
    const newGatilhos = config.GATILHOS.filter((_, i) => i !== index);
    updateField('GATILHOS', newGatilhos);
  };

  const updateChannelPair = (index, field, value) => {
    const newPairs = [...(config.CHANNEL_PAIRS || [])];
    newPairs[index] = { ...newPairs[index], [field]: value };
    updateField('CHANNEL_PAIRS', newPairs);
  };

  const addChannelPair = () => {
    updateField('CHANNEL_PAIRS', [
      ...(config.CHANNEL_PAIRS || []),
      { source: '', target: '', description: '' }
    ]);
  };

  const removeChannelPair = (index) => {
    const newPairs = config.CHANNEL_PAIRS.filter((_, i) => i !== index);
    updateField('CHANNEL_PAIRS', newPairs);
  };

  const updateGroupLink = (groupName, link) => {
    const newLinks = { ...(config.GROUP_LINKS || {}) };
    if (link === null) {
      delete newLinks[groupName];
    } else {
      newLinks[groupName] = link;
    }
    updateField('GROUP_LINKS', newLinks);
  };

  const addGroupLink = () => {
    const newLinks = { ...(config.GROUP_LINKS || {}), '': '' };
    updateField('GROUP_LINKS', newLinks);
  };

  const updateGroupLinkKey = (oldKey, newKey) => {
    const newLinks = {};
    Object.entries(config.GROUP_LINKS || {}).forEach(([key, value]) => {
      if (key === oldKey) {
        newLinks[newKey] = value;
      } else {
        newLinks[key] = value;
      }
    });
    updateField('GROUP_LINKS', newLinks);
  };

  if (loading) {
    return <div className="loading">⏳ Carregando configurações...</div>;
  }

  if (!config) {
    return <div className="loading">❌ Erro ao carregar configurações</div>;
  }

  return (
    <div className="App">
      <div className="header">
        <h1>🤖 Bot de Afiliados - Painel de Configuração</h1>
        <p>Configure todas as opções do seu bot de forma fácil e dinâmica</p>
      </div>

      {message.text && (
        <div className={`alert alert-${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="container">
        {/* Chrome & Browser */}
        <div className="section">
          <h2>🌐 Configurações do Chrome</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Diretório de Dados do Chrome:</label>
              <input
                type="text"
                value={config.CHROME_USER_DATA_DIR || ''}
                onChange={(e) => updateField('CHROME_USER_DATA_DIR', e.target.value)}
                placeholder="C:\BotChromeProfile"
              />
              <span className="small-text">Caminho completo do perfil do Chrome</span>
            </div>
            <div className="form-group">
              <label>Nome do Perfil:</label>
              <input
                type="text"
                value={config.CHROME_PROFILE_DIR_NAME || ''}
                onChange={(e) => updateField('CHROME_PROFILE_DIR_NAME', e.target.value)}
                placeholder="Default"
              />
            </div>
            <div className="form-group">
              <div className="checkbox-wrapper">
                <input
                  type="checkbox"
                  checked={config.HEADLESS || false}
                  onChange={(e) => updateField('HEADLESS', e.target.checked)}
                />
                <label>Modo Headless (sem interface)</label>
              </div>
            </div>
          </div>
        </div>

        {/* Configurações Gerais */}
        <div className="section">
          <h2>⚙️ Configurações Gerais</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Diretório de Downloads:</label>
              <input
                type="text"
                value={config.DOWNLOAD_DIR || ''}
                onChange={(e) => updateField('DOWNLOAD_DIR', e.target.value)}
                placeholder="./tmp"
              />
            </div>
            <div className="form-group">
              <label>Tag de Afiliado Mercado Livre:</label>
              <input
                type="text"
                value={config.MELI_AFFILIATE_TAG || ''}
                onChange={(e) => updateField('MELI_AFFILIATE_TAG', e.target.value)}
                placeholder="sua_tag_aqui"
              />
            </div>
            <div className="form-group">
              <label>Emoji Superhero:</label>
              <input
                type="text"
                value={config.SUPERHERO_EMOJI || ''}
                onChange={(e) => updateField('SUPERHERO_EMOJI', e.target.value)}
                placeholder="🦸"
              />
            </div>
          </div>
        </div>

        {/* Timing & Performance */}
        <div className="section">
          <h2>⏱️ Timing & Performance</h2>
          <div className="form-grid">
            <div className="form-group">
              <label>Intervalo de Polling (segundos):</label>
              <input
                type="number"
                value={config.POLL_SECONDS || 180}
                onChange={(e) => updateField('POLL_SECONDS', parseInt(e.target.value))}
              />
              <span className="small-text">Tempo entre verificações de mensagens</span>
            </div>
            <div className="form-group">
              <label>Delay de Refresh de Bolha:</label>
              <input
                type="number"
                value={config.BUBBLE_REFRESH_DELAY || 2}
                onChange={(e) => updateField('BUBBLE_REFRESH_DELAY', parseInt(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>Reiniciar a Cada X Ciclos:</label>
              <input
                type="number"
                value={config.RESTART_EVERY_CYCLES || 40}
                onChange={(e) => updateField('RESTART_EVERY_CYCLES', parseInt(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>Timeout de Ciclo (segundos):</label>
              <input
                type="number"
                value={config.CYCLE_TIMEOUT_SECONDS || 240}
                onChange={(e) => updateField('CYCLE_TIMEOUT_SECONDS', parseInt(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>Granularidade de Sleep (segundos):</label>
              <input
                type="number"
                value={config.SLEEP_GRANULARITY_SECONDS || 5}
                onChange={(e) => updateField('SLEEP_GRANULARITY_SECONDS', parseInt(e.target.value))}
              />
            </div>
          </div>
        </div>

        {/* Modo Noturno */}
        <div className="section">
          <h2>🌙 Modo Noturno</h2>
          <div className="form-grid">
            <div className="form-group">
              <div className="checkbox-wrapper">
                <input
                  type="checkbox"
                  checked={config.NIGHT_MODE_ENABLED || false}
                  onChange={(e) => updateField('NIGHT_MODE_ENABLED', e.target.checked)}
                />
                <label>Ativar Modo Noturno</label>
              </div>
            </div>
            <div className="form-group">
              <label>Hora de Início (0-23):</label>
              <input
                type="number"
                min="0"
                max="23"
                value={config.NIGHT_START_HOUR || 1}
                onChange={(e) => updateField('NIGHT_START_HOUR', parseInt(e.target.value))}
              />
            </div>
            <div className="form-group">
              <label>Hora de Término (0-23):</label>
              <input
                type="number"
                min="0"
                max="23"
                value={config.NIGHT_END_HOUR || 8}
                onChange={(e) => updateField('NIGHT_END_HOUR', parseInt(e.target.value))}
              />
            </div>
          </div>
        </div>

        {/* Gatilhos */}
        <div className="section">
          <h2>🔥 Gatilhos de Marketing</h2>
          <div className="form-group">
            <label>Chance de Adicionar Gatilho (0.0 - 1.0):</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={config.GATILHO_CHANCE || 0.20}
              onChange={(e) => updateField('GATILHO_CHANCE', parseFloat(e.target.value))}
            />
            <span className="small-text">0.20 = 20% de chance</span>
          </div>
          <div className="list-section">
            <h3>Lista de Gatilhos:</h3>
            {(config.GATILHOS || []).map((gatilho, index) => (
              <div key={index} className="list-item">
                <input
                  type="text"
                  value={gatilho}
                  onChange={(e) => updateGatilho(index, e.target.value)}
                  placeholder="Digite um gatilho..."
                />
                <button className="btn-remove" onClick={() => removeGatilho(index)}>
                  🗑️ Remover
                </button>
              </div>
            ))}
            <button className="btn-add" onClick={addGatilho}>
              ➕ Adicionar Gatilho
            </button>
          </div>
        </div>

        {/* Pares de Canais */}
        <div className="section">
          <h2>📢 Pares de Canais (Source → Target)</h2>
          <div className="list-section">
            {(config.CHANNEL_PAIRS || []).map((pair, index) => (
              <div key={index} className="channel-pair-item">
                <div className="form-grid">
                  <div className="form-group">
                    <label>Canal de Origem:</label>
                    <input
                      type="text"
                      value={pair.source || ''}
                      onChange={(e) => updateChannelPair(index, 'source', e.target.value)}
                      placeholder="Nome do canal source"
                    />
                  </div>
                  <div className="form-group">
                    <label>Canal de Destino:</label>
                    <input
                      type="text"
                      value={pair.target || ''}
                      onChange={(e) => updateChannelPair(index, 'target', e.target.value)}
                      placeholder="Nome do canal target"
                    />
                  </div>
                  <div className="form-group">
                    <label>Descrição:</label>
                    <input
                      type="text"
                      value={pair.description || ''}
                      onChange={(e) => updateChannelPair(index, 'description', e.target.value)}
                      placeholder="Descrição"
                    />
                  </div>
                </div>
                <button className="btn-remove" onClick={() => removeChannelPair(index)}>
                  🗑️ Remover Par
                </button>
              </div>
            ))}
            <button className="btn-add" onClick={addChannelPair}>
              ➕ Adicionar Par de Canais
            </button>
          </div>
        </div>

        {/* Links de Grupos */}
        <div className="section">
          <h2>🔗 Links dos Grupos</h2>
          <div className="list-section">
            {Object.entries(config.GROUP_LINKS || {}).map(([groupName, link]) => (
              <div key={groupName} className="group-links-item">
                <input
                  type="text"
                  value={groupName}
                  onChange={(e) => updateGroupLinkKey(groupName, e.target.value)}
                  placeholder="Nome do grupo"
                />
                <input
                  type="text"
                  value={link}
                  onChange={(e) => updateGroupLink(groupName, e.target.value)}
                  placeholder="https://chat.whatsapp.com/..."
                />
                <button className="btn-remove" onClick={() => updateGroupLink(groupName, null)}>
                  🗑️
                </button>
              </div>
            ))}
            <button className="btn-add" onClick={addGroupLink}>
              ➕ Adicionar Link de Grupo
            </button>
          </div>
        </div>

        {/* Ações */}
        <div className="actions">
          <button 
            className="btn-start" 
            onClick={handleStartBot} 
            disabled={starting || saving || stopping || botRunning}
          >
            {starting ? '⏳ Iniciando...' : '▶️ Iniciar Bot'}
          </button>
          <button 
            className="btn-stop" 
            onClick={handleStopBot} 
            disabled={stopping || saving || starting || !botRunning}
          >
            {stopping ? '⏳ Parando...' : '⏹️ Parar Bot'}
          </button>
          <button 
            className="btn-save" 
            onClick={handleSave} 
            disabled={saving || starting || stopping}
          >
            {saving ? '💾 Salvando...' : '💾 Salvar Configurações'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
