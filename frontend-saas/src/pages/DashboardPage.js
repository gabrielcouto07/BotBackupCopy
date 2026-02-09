/**
 * Dashboard Page Component - Main bot control panel
 */
import React, { useState } from 'react';
import { 
  Play, Square, RefreshCw, Settings, History, 
  Activity, CheckCircle2, XCircle, Clock, Loader2,
  Zap, AlertTriangle
} from 'lucide-react';
import { useBotStatus, useBotRuns } from '../hooks/useBot';
import api from '../services/api';

export default function DashboardPage() {
  const { status, loading: statusLoading, refresh: refreshStatus } = useBotStatus(5000);
  const { runs, loading: runsLoading, refresh: refreshRuns } = useBotRuns(1, 5);
  const [actionLoading, setActionLoading] = useState(null);
  const [message, setMessage] = useState(null);

  const handleStart = async () => {
    setActionLoading('start');
    try {
      await api.startBot();
      setMessage({ type: 'success', text: 'Bot iniciado com sucesso!' });
      refreshStatus();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(null);
    }
  };

  const handleStop = async () => {
    setActionLoading('stop');
    try {
      await api.stopBot();
      setMessage({ type: 'success', text: 'Comando de parada enviado!' });
      refreshStatus();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(null);
    }
  };

  const handleTestRun = async () => {
    setActionLoading('test');
    try {
      const result = await api.testRun(true, 120);
      setMessage({ 
        type: result.errors.length ? 'warning' : 'success', 
        text: `Teste concluído: ${result.orders_found} itens encontrados, ${result.actions_taken} ações` 
      });
      refreshRuns();
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (statusValue) => {
    switch (statusValue) {
      case 'running': return 'status-running';
      case 'idle': return 'status-idle';
      case 'stopped': return 'status-stopped';
      case 'error': return 'status-error';
      default: return '';
    }
  };

  const getStatusIcon = (statusValue) => {
    switch (statusValue) {
      case 'running': return <Activity className="status-icon pulse" />;
      case 'idle': return <Clock className="status-icon" />;
      case 'stopped': return <Square className="status-icon" />;
      case 'error': return <XCircle className="status-icon" />;
      default: return <Clock className="status-icon" />;
    }
  };

  const getRunStatusBadge = (runStatus) => {
    switch (runStatus) {
      case 'running':
        return <span className="badge badge-running"><Activity size={14} /> Executando</span>;
      case 'completed':
        return <span className="badge badge-success"><CheckCircle2 size={14} /> Concluído</span>;
      case 'failed':
        return <span className="badge badge-error"><XCircle size={14} /> Falhou</span>;
      case 'stopped':
        return <span className="badge badge-warning"><Square size={14} /> Parado</span>;
      default:
        return <span className="badge">{runStatus}</span>;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('pt-BR');
  };

  return (
    <div className="dashboard">
      {message && (
        <div className={`alert alert-${message.type}`}>
          {message.type === 'success' && <CheckCircle2 size={20} />}
          {message.type === 'error' && <XCircle size={20} />}
          {message.type === 'warning' && <AlertTriangle size={20} />}
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className="alert-close">×</button>
        </div>
      )}

      {/* Status Card */}
      <div className="card status-card">
        <div className="card-header">
          <h2><Activity size={24} /> Status do Bot</h2>
          <button 
            className="btn btn-icon" 
            onClick={refreshStatus}
            disabled={statusLoading}
          >
            <RefreshCw size={18} className={statusLoading ? 'spinner' : ''} />
          </button>
        </div>
        
        <div className="card-content">
          {statusLoading && !status ? (
            <div className="loading-state">
              <Loader2 className="spinner" size={32} />
              <span>Carregando...</span>
            </div>
          ) : status ? (
            <div className="status-display">
              <div className={`status-indicator ${getStatusColor(status.status)}`}>
                {getStatusIcon(status.status)}
                <span className="status-text">{status.status}</span>
              </div>
              
              <div className="status-details">
                <div className="detail">
                  <span className="label">Última execução:</span>
                  <span className="value">{formatDate(status.last_run)}</span>
                </div>
                {status.next_run && (
                  <div className="detail">
                    <span className="label">Próxima execução:</span>
                    <span className="value">{formatDate(status.next_run)}</span>
                  </div>
                )}
                {status.current_cycle && (
                  <div className="detail">
                    <span className="label">Ciclo atual:</span>
                    <span className="value">{status.current_cycle}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p>Não foi possível carregar o status</p>
          )}
        </div>
      </div>

      {/* Control Buttons */}
      <div className="card controls-card">
        <div className="card-header">
          <h2><Zap size={24} /> Controles</h2>
        </div>
        
        <div className="card-content">
          <div className="control-buttons">
            <button
              className="btn btn-success btn-lg"
              onClick={handleStart}
              disabled={actionLoading || status?.status === 'running'}
            >
              {actionLoading === 'start' ? (
                <Loader2 className="spinner" size={20} />
              ) : (
                <Play size={20} />
              )}
              Iniciar Bot
            </button>

            <button
              className="btn btn-danger btn-lg"
              onClick={handleStop}
              disabled={actionLoading || status?.status !== 'running'}
            >
              {actionLoading === 'stop' ? (
                <Loader2 className="spinner" size={20} />
              ) : (
                <Square size={20} />
              )}
              Parar Bot
            </button>

            <button
              className="btn btn-secondary btn-lg"
              onClick={handleTestRun}
              disabled={actionLoading}
            >
              {actionLoading === 'test' ? (
                <Loader2 className="spinner" size={20} />
              ) : (
                <RefreshCw size={20} />
              )}
              Executar Teste
            </button>
          </div>
        </div>
      </div>

      {/* Recent Runs */}
      <div className="card runs-card">
        <div className="card-header">
          <h2><History size={24} /> Execuções Recentes</h2>
          <button 
            className="btn btn-icon" 
            onClick={refreshRuns}
            disabled={runsLoading}
          >
            <RefreshCw size={18} className={runsLoading ? 'spinner' : ''} />
          </button>
        </div>
        
        <div className="card-content">
          {runsLoading && runs.length === 0 ? (
            <div className="loading-state">
              <Loader2 className="spinner" size={32} />
            </div>
          ) : runs.length > 0 ? (
            <div className="runs-list">
              {runs.map((run) => (
                <div key={run.id} className="run-item">
                  <div className="run-info">
                    {getRunStatusBadge(run.status)}
                    <span className="run-trigger">{run.triggered_by}</span>
                  </div>
                  <div className="run-dates">
                    <span>Início: {formatDate(run.started_at)}</span>
                    {run.completed_at && (
                      <span>Fim: {formatDate(run.completed_at)}</span>
                    )}
                  </div>
                  {run.error_message && (
                    <div className="run-error">
                      <AlertTriangle size={14} />
                      {run.error_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state">Nenhuma execução encontrada</p>
          )}
        </div>
      </div>
    </div>
  );
}
