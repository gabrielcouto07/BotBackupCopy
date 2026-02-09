import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [activeTab, setActiveTab] = useState('affiliate');
  const [botStatus, setBotStatus] = useState({ running: false, pid: null });
  const [botLoading, setBotLoading] = useState(false);

  useEffect(() => {
    loadSettings();
    checkBotStatus();
    // Verifica status do bot a cada 5 segundos
    const interval = setInterval(checkBotStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkBotStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/bot/status`);
      setBotStatus(response.data);
    } catch (error) {
      console.error('Erro ao verificar status do bot:', error);
    }
  };

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/settings`);
      setSettings(response.data);
      showMessage('success', '✅ Configurações carregadas!');
    } catch (error) {
      console.error('Erro ao carregar:', error);
      showMessage('error', '❌ Erro ao carregar. Verifique se a API está rodando.');
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: '', text: '' }), 4000);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await axios.post(`${API_URL}/settings`, settings);
      showMessage('success', '✅ Configurações salvas com sucesso!');
    } catch (error) {
      showMessage('error', '❌ Erro ao salvar: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleStartBot = async () => {
    try {
      setBotLoading(true);
      const response = await axios.post(`${API_URL}/bot/start`);
      if (response.data.success) {
        showMessage('success', '🚀 Bot iniciado com sucesso!');
        checkBotStatus();
      } else {
        showMessage('error', response.data.message);
      }
    } catch (error) {
      showMessage('error', '❌ Erro ao iniciar bot: ' + (error.response?.data?.message || error.message));
    } finally {
      setBotLoading(false);
    }
  };

  const handleStopBot = async () => {
    try {
      setBotLoading(true);
      const response = await axios.post(`${API_URL}/bot/stop`);
      if (response.data.success) {
        showMessage('success', '⏹️ Bot parado!');
        checkBotStatus();
      } else {
        showMessage('error', response.data.message);
      }
    } catch (error) {
      showMessage('error', '❌ Erro ao parar bot: ' + (error.response?.data?.message || error.message));
    } finally {
      setBotLoading(false);
    }
  };

  const handleSaveAndStart = async () => {
    try {
      setSaving(true);
      await axios.post(`${API_URL}/settings`, settings);
      showMessage('success', '✅ Configurações salvas!');
      
      // Se bot não está rodando, inicia
      if (!botStatus.running) {
        setBotLoading(true);
        const response = await axios.post(`${API_URL}/bot/start`);
        if (response.data.success) {
          showMessage('success', '🚀 Configurações salvas e Bot iniciado!');
          checkBotStatus();
        }
      } else {
        // Se já está rodando, reinicia para aplicar novas configs
        const response = await axios.post(`${API_URL}/bot/restart`);
        if (response.data.success) {
          showMessage('success', '🔄 Configurações salvas e Bot reiniciado!');
          checkBotStatus();
        }
      }
    } catch (error) {
      showMessage('error', '❌ Erro: ' + error.message);
    } finally {
      setSaving(false);
      setBotLoading(false);
    }
  };

  const updateAffiliate = (field, value) => {
    setSettings({
      ...settings,
      affiliate: { ...settings.affiliate, [field]: value }
    });
  };

  const updateFacebook = (field, value) => {
    setSettings({
      ...settings,
      facebook: { ...settings.facebook, [field]: value }
    });
  };

  const updateWhatsapp = (field, value) => {
    setSettings({
      ...settings,
      whatsapp: { ...settings.whatsapp, [field]: value }
    });
  };

  const updateTiming = (field, value) => {
    setSettings({
      ...settings,
      timing: { ...settings.timing, [field]: value }
    });
  };

  const updateTriggers = (field, value) => {
    setSettings({
      ...settings,
      triggers: { ...settings.triggers, [field]: value }
    });
  };

  const updateChannelPair = (index, field, value) => {
    const newPairs = [...settings.channel_pairs];
    newPairs[index] = { ...newPairs[index], [field]: value };
    setSettings({ ...settings, channel_pairs: newPairs });
  };

  const addChannelPair = () => {
    setSettings({
      ...settings,
      channel_pairs: [
        ...settings.channel_pairs,
        { source: '', target: '', description: '', enabled: true }
      ]
    });
  };

  const removeChannelPair = (index) => {
    const newPairs = settings.channel_pairs.filter((_, i) => i !== index);
    setSettings({ ...settings, channel_pairs: newPairs });
  };

  const updateTriggerItem = (index, value) => {
    const newList = [...settings.triggers.list];
    newList[index] = value;
    updateTriggers('list', newList);
  };

  const addTrigger = () => {
    updateTriggers('list', [...settings.triggers.list, '']);
  };

  const removeTrigger = (index) => {
    const newList = settings.triggers.list.filter((_, i) => i !== index);
    updateTriggers('list', newList);
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>⏳ Carregando configurações...</p>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="loading-screen error">
        <p>❌ Erro ao carregar configurações</p>
        <button onClick={loadSettings}>🔄 Tentar novamente</button>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 Bot Afiliados - Configurações</h1>
        <p>Gerencie suas configurações de forma fácil</p>
      </header>

      {message.text && (
        <div className={`alert alert-${message.type}`}>
          {message.text}
        </div>
      )}

      <nav className="tabs">
        <button className={activeTab === 'affiliate' ? 'active' : ''} onClick={() => setActiveTab('affiliate')}>
          💰 Afiliados
        </button>
        <button className={activeTab === 'channels' ? 'active' : ''} onClick={() => setActiveTab('channels')}>
          📢 Canais
        </button>
        <button className={activeTab === 'platforms' ? 'active' : ''} onClick={() => setActiveTab('platforms')}>
          📱 Plataformas
        </button>
        <button className={activeTab === 'timing' ? 'active' : ''} onClick={() => setActiveTab('timing')}>
          ⏱️ Timing
        </button>
        <button className={activeTab === 'triggers' ? 'active' : ''} onClick={() => setActiveTab('triggers')}>
          🔥 Gatilhos
        </button>
      </nav>

      <main className="content">
        {activeTab === 'affiliate' && (
          <section className="section">
            <h2>💰 Configurações de Afiliados</h2>
            <div className="card">
              <h3>🛒 Mercado Livre</h3>
              <div className="form-group">
                <label>Tag de Afiliado ML:</label>
                <input type="text" value={settings.affiliate.meli_tag} onChange={(e) => updateAffiliate('meli_tag', e.target.value)} placeholder="sua-tag-ml" />
                <span className="hint">Ex: seunome20230101120000</span>
              </div>
            </div>
            <div className="card">
              <h3>📦 Amazon</h3>
              <div className="form-group">
                <label>Tag de Afiliado Amazon:</label>
                <input type="text" value={settings.affiliate.amazon_tag} onChange={(e) => updateAffiliate('amazon_tag', e.target.value)} placeholder="sua-tag-20" />
                <span className="hint">Ex: seusite-20</span>
              </div>
              <div className="form-group toggle-group">
                <label>Ativar Amazon:</label>
                <label className="toggle">
                  <input type="checkbox" checked={settings.affiliate.amazon_enabled} onChange={(e) => updateAffiliate('amazon_enabled', e.target.checked)} />
                  <span className="slider"></span>
                </label>
                <span className={`status ${settings.affiliate.amazon_enabled ? 'on' : 'off'}`}>
                  {settings.affiliate.amazon_enabled ? '✅ Ativo' : '❌ Desativado'}
                </span>
              </div>
            </div>
          </section>
        )}

        {activeTab === 'channels' && (
          <section className="section">
            <h2>📢 Pares de Canais (Origem → Destino)</h2>
            <p className="description">Configure quais grupos do WhatsApp serão monitorados e para onde as mensagens serão enviadas.</p>
            {settings.channel_pairs.map((pair, index) => (
              <div key={index} className={`card channel-card ${!pair.enabled ? 'disabled' : ''}`}>
                <div className="card-header">
                  <h3>Canal #{index + 1}</h3>
                  <div className="card-actions">
                    <label className="toggle small">
                      <input type="checkbox" checked={pair.enabled} onChange={(e) => updateChannelPair(index, 'enabled', e.target.checked)} />
                      <span className="slider"></span>
                    </label>
                    <button className="btn-icon danger" onClick={() => removeChannelPair(index)} title="Remover">🗑️</button>
                  </div>
                </div>
                <div className="form-grid">
                  <div className="form-group">
                    <label>📥 Grupo Origem:</label>
                    <input type="text" value={pair.source} onChange={(e) => updateChannelPair(index, 'source', e.target.value)} placeholder="Nome exato do grupo origem" />
                  </div>
                  <div className="form-group">
                    <label>📤 Grupo Destino:</label>
                    <input type="text" value={pair.target} onChange={(e) => updateChannelPair(index, 'target', e.target.value)} placeholder="Nome exato do grupo destino" />
                  </div>
                  <div className="form-group">
                    <label>📝 Descrição:</label>
                    <input type="text" value={pair.description} onChange={(e) => updateChannelPair(index, 'description', e.target.value)} placeholder="Descrição para identificar" />
                  </div>
                </div>
              </div>
            ))}
            <button className="btn-add" onClick={addChannelPair}>➕ Adicionar Canal</button>
          </section>
        )}

        {activeTab === 'platforms' && (
          <section className="section">
            <h2>📱 Plataformas</h2>
            <div className="card">
              <h3>💬 WhatsApp</h3>
              <div className="form-group">
                <label>Link do Grupo (adicionado nas mensagens):</label>
                <input type="text" value={settings.whatsapp.group_link} onChange={(e) => updateWhatsapp('group_link', e.target.value)} placeholder="https://chat.whatsapp.com/..." />
                <span className="hint">Será adicionado no final de cada mensagem</span>
              </div>
            </div>
            <div className="card">
              <h3>📘 Facebook</h3>
              <div className="form-group toggle-group">
                <label>Ativar Facebook:</label>
                <label className="toggle">
                  <input type="checkbox" checked={settings.facebook.enabled} onChange={(e) => updateFacebook('enabled', e.target.checked)} />
                  <span className="slider"></span>
                </label>
                <span className={`status ${settings.facebook.enabled ? 'on' : 'off'}`}>
                  {settings.facebook.enabled ? '✅ Ativo' : '❌ Desativado'}
                </span>
              </div>
              {settings.facebook.enabled && (
                <>
                  <div className="form-group">
                    <label>URL da Página:</label>
                    <input type="text" value={settings.facebook.page_url} onChange={(e) => updateFacebook('page_url', e.target.value)} placeholder="https://www.facebook.com/..." />
                  </div>
                  <div className="form-group">
                    <label>Intervalo de Postagem (minutos):</label>
                    <input type="number" min="5" value={settings.facebook.post_interval_minutes} onChange={(e) => updateFacebook('post_interval_minutes', parseInt(e.target.value))} />
                    <span className="hint">Tempo mínimo entre postagens</span>
                  </div>
                </>
              )}
            </div>
          </section>
        )}

        {activeTab === 'timing' && (
          <section className="section">
            <h2>⏱️ Configurações de Tempo</h2>
            <div className="card">
              <h3>🔄 Ciclo de Monitoramento</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label>Intervalo entre Ciclos (segundos):</label>
                  <input type="number" min="60" value={settings.timing.poll_seconds} onChange={(e) => updateTiming('poll_seconds', parseInt(e.target.value))} />
                  <span className="hint">{Math.floor(settings.timing.poll_seconds / 60)} minutos</span>
                </div>
                <div className="form-group">
                  <label>Janela de Deduplicação (horas):</label>
                  <input type="number" min="1" value={settings.timing.dedup_window_hours} onChange={(e) => updateTiming('dedup_window_hours', parseInt(e.target.value))} />
                  <span className="hint">Evita reenviar o mesmo produto</span>
                </div>
              </div>
            </div>
            <div className="card">
              <h3>🌙 Modo Noturno</h3>
              <div className="form-group toggle-group">
                <label>Ativar Modo Noturno:</label>
                <label className="toggle">
                  <input type="checkbox" checked={settings.timing.night_mode_enabled} onChange={(e) => updateTiming('night_mode_enabled', e.target.checked)} />
                  <span className="slider"></span>
                </label>
                <span className={`status ${settings.timing.night_mode_enabled ? 'on' : 'off'}`}>
                  {settings.timing.night_mode_enabled ? '✅ Ativo' : '❌ Desativado'}
                </span>
              </div>
              {settings.timing.night_mode_enabled && (
                <div className="form-grid">
                  <div className="form-group">
                    <label>Hora de Início (pausa):</label>
                    <input type="number" min="0" max="23" value={settings.timing.night_start_hour} onChange={(e) => updateTiming('night_start_hour', parseInt(e.target.value))} />
                    <span className="hint">{settings.timing.night_start_hour}:00</span>
                  </div>
                  <div className="form-group">
                    <label>Hora de Término (retoma):</label>
                    <input type="number" min="0" max="23" value={settings.timing.night_end_hour} onChange={(e) => updateTiming('night_end_hour', parseInt(e.target.value))} />
                    <span className="hint">{settings.timing.night_end_hour}:00</span>
                  </div>
                </div>
              )}
            </div>
          </section>
        )}

        {activeTab === 'triggers' && (
          <section className="section">
            <h2>🔥 Gatilhos de Marketing</h2>
            <p className="description">Frases que podem ser adicionadas aleatoriamente às mensagens.</p>
            <div className="card">
              <div className="form-group toggle-group">
                <label>Ativar Gatilhos:</label>
                <label className="toggle">
                  <input type="checkbox" checked={settings.triggers.enabled} onChange={(e) => updateTriggers('enabled', e.target.checked)} />
                  <span className="slider"></span>
                </label>
              </div>
              {settings.triggers.enabled && (
                <>
                  <div className="form-group">
                    <label>Chance de Adicionar (0 a 1):</label>
                    <input type="number" step="0.05" min="0" max="1" value={settings.triggers.chance} onChange={(e) => updateTriggers('chance', parseFloat(e.target.value))} />
                    <span className="hint">{Math.round(settings.triggers.chance * 100)}% de chance</span>
                  </div>
                  <h4>Lista de Gatilhos:</h4>
                  <div className="trigger-list">
                    {settings.triggers.list.map((trigger, index) => (
                      <div key={index} className="trigger-item">
                        <input type="text" value={trigger} onChange={(e) => updateTriggerItem(index, e.target.value)} placeholder="Digite um gatilho..." />
                        <button className="btn-icon danger" onClick={() => removeTrigger(index)}>🗑️</button>
                      </div>
                    ))}
                  </div>
                  <button className="btn-add small" onClick={addTrigger}>➕ Adicionar Gatilho</button>
                </>
              )}
            </div>
          </section>
        )}
      </main>

      {/* Bot Status Bar */}
      <div className={`bot-status-bar ${botStatus.running ? 'running' : 'stopped'}`}>
        <div className="status-indicator">
          <span className={`dot ${botStatus.running ? 'pulse' : ''}`}></span>
          <span>{botStatus.running ? `🤖 Bot Rodando (PID: ${botStatus.pid})` : '⏹️ Bot Parado'}</span>
        </div>
      </div>

      <footer className="footer">
        <div className="footer-left">
          {botStatus.running ? (
            <button className="btn-stop" onClick={handleStopBot} disabled={botLoading}>
              {botLoading ? '⏳...' : '⏹️ Parar Bot'}
            </button>
          ) : (
            <button className="btn-start" onClick={handleStartBot} disabled={botLoading}>
              {botLoading ? '⏳...' : '▶️ Iniciar Bot'}
            </button>
          )}
        </div>
        <div className="footer-right">
          <button className="btn-reload" onClick={loadSettings} disabled={loading}>
            🔄
          </button>
          <button className="btn-save" onClick={handleSave} disabled={saving || botLoading}>
            {saving ? '⏳...' : '💾 Salvar'}
          </button>
          <button className="btn-save-start" onClick={handleSaveAndStart} disabled={saving || botLoading}>
            {saving || botLoading ? '⏳...' : '🚀 Salvar e Iniciar'}
          </button>
        </div>
      </footer>
    </div>
  );
}

export default App;
