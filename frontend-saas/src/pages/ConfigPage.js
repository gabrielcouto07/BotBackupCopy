/**
 * Config Page Component - Bot configuration settings
 */
import React, { useState, useEffect } from 'react';
import { 
  Settings, Save, RotateCcw, Eye, EyeOff, 
  AlertCircle, CheckCircle2, Loader2 
} from 'lucide-react';
import { useBotConfig } from '../hooks/useBot';

export default function ConfigPage() {
  const { config, loading, saving, error, updateConfig, resetConfig, refresh } = useBotConfig();
  
  const [formData, setFormData] = useState({
    platform_email: '',
    platform_password: '',
    check_interval_minutes: 15,
    max_retries: 3,
    headless: true,
    webhook_url: '',
    notify_on_error: true,
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  // Update form when config loads
  useEffect(() => {
    if (config) {
      setFormData({
        platform_email: config.platform_email || '',
        platform_password: '',  // Password is masked, don't fill
        check_interval_minutes: config.check_interval_minutes || 15,
        max_retries: config.max_retries || 3,
        headless: config.headless !== false,
        webhook_url: config.webhook_url || '',
        notify_on_error: config.notify_on_error !== false,
      });
    }
  }, [config]);

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);

    // Only send password if changed
    const dataToSend = { ...formData };
    if (!dataToSend.platform_password) {
      delete dataToSend.platform_password;
    }

    const success = await updateConfig(dataToSend);
    
    if (success) {
      setMessage({ type: 'success', text: 'Configurações salvas com sucesso!' });
      setHasChanges(false);
      setFormData(prev => ({ ...prev, platform_password: '' }));
    } else {
      setMessage({ type: 'error', text: error || 'Erro ao salvar configurações' });
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Tem certeza que deseja resetar para as configurações padrão?')) {
      return;
    }

    const success = await resetConfig();
    
    if (success) {
      setMessage({ type: 'success', text: 'Configurações resetadas!' });
      setHasChanges(false);
    } else {
      setMessage({ type: 'error', text: 'Erro ao resetar configurações' });
    }
  };

  if (loading) {
    return (
      <div className="page-loading">
        <Loader2 className="spinner" size={48} />
        <p>Carregando configurações...</p>
      </div>
    );
  }

  return (
    <div className="config-page">
      <div className="page-header">
        <h1><Settings size={28} /> Configurações do Bot</h1>
      </div>

      {message && (
        <div className={`alert alert-${message.type}`}>
          {message.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className="alert-close">×</button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="config-form">
        {/* Credentials Section */}
        <div className="config-section">
          <h3>Credenciais da Plataforma</h3>
          
          <div className="form-group">
            <label htmlFor="platform_email">Email da Plataforma</label>
            <input
              id="platform_email"
              type="email"
              value={formData.platform_email}
              onChange={(e) => handleChange('platform_email', e.target.value)}
              placeholder="email@plataforma.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="platform_password">
              Senha da Plataforma
              <span className="hint">(deixe em branco para manter a atual)</span>
            </label>
            <div className="input-with-action">
              <input
                id="platform_password"
                type={showPassword ? 'text' : 'password'}
                value={formData.platform_password}
                onChange={(e) => handleChange('platform_password', e.target.value)}
                placeholder="••••••••"
              />
              <button
                type="button"
                className="btn btn-icon"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
        </div>

        {/* Bot Settings Section */}
        <div className="config-section">
          <h3>Configurações do Bot</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="check_interval">Intervalo de Verificação (minutos)</label>
              <input
                id="check_interval"
                type="number"
                min="5"
                max="60"
                value={formData.check_interval_minutes}
                onChange={(e) => handleChange('check_interval_minutes', parseInt(e.target.value))}
              />
            </div>

            <div className="form-group">
              <label htmlFor="max_retries">Máximo de Tentativas</label>
              <input
                id="max_retries"
                type="number"
                min="1"
                max="10"
                value={formData.max_retries}
                onChange={(e) => handleChange('max_retries', parseInt(e.target.value))}
              />
            </div>
          </div>

          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.headless}
                onChange={(e) => handleChange('headless', e.target.checked)}
              />
              <span>Modo Headless (sem interface gráfica)</span>
            </label>
          </div>
        </div>

        {/* Notifications Section */}
        <div className="config-section">
          <h3>Notificações</h3>
          
          <div className="form-group">
            <label htmlFor="webhook_url">URL do Webhook (opcional)</label>
            <input
              id="webhook_url"
              type="url"
              value={formData.webhook_url}
              onChange={(e) => handleChange('webhook_url', e.target.value)}
              placeholder="https://..."
            />
          </div>

          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.notify_on_error}
                onChange={(e) => handleChange('notify_on_error', e.target.checked)}
              />
              <span>Notificar em caso de erro</span>
            </label>
          </div>
        </div>

        {/* Actions */}
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleReset}
            disabled={saving}
          >
            <RotateCcw size={18} />
            Resetar Padrões
          </button>
          
          <button
            type="submit"
            className="btn btn-primary"
            disabled={saving || !hasChanges}
          >
            {saving ? (
              <>
                <Loader2 className="spinner" size={18} />
                Salvando...
              </>
            ) : (
              <>
                <Save size={18} />
                Salvar Configurações
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
