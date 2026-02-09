/**
 * Logs Page Component - View bot execution logs
 */
import React, { useState } from 'react';
import { 
  FileText, RefreshCw, Filter, ChevronDown, ChevronRight,
  AlertCircle, AlertTriangle, Info, Bug, Loader2
} from 'lucide-react';
import { useBotLogs, useBotRuns } from '../hooks/useBot';

export default function LogsPage() {
  const [selectedRun, setSelectedRun] = useState(null);
  const [levelFilter, setLevelFilter] = useState(null);
  const [limit, setLimit] = useState(100);
  
  const { runs, loading: runsLoading, refresh: refreshRuns } = useBotRuns(1, 20);
  const { logs, loading: logsLoading, refresh: refreshLogs } = useBotLogs(
    limit, 
    levelFilter, 
    selectedRun
  );

  const getLevelIcon = (level) => {
    switch (level?.toUpperCase()) {
      case 'ERROR': return <AlertCircle size={16} className="log-icon error" />;
      case 'WARNING': return <AlertTriangle size={16} className="log-icon warning" />;
      case 'INFO': return <Info size={16} className="log-icon info" />;
      case 'DEBUG': return <Bug size={16} className="log-icon debug" />;
      default: return <Info size={16} className="log-icon" />;
    }
  };

  const getLevelClass = (level) => {
    switch (level?.toUpperCase()) {
      case 'ERROR': return 'log-error';
      case 'WARNING': return 'log-warning';
      case 'INFO': return 'log-info';
      case 'DEBUG': return 'log-debug';
      default: return '';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString('pt-BR');
  };

  return (
    <div className="logs-page">
      <div className="page-header">
        <h1><FileText size={28} /> Logs de Execução</h1>
        <button 
          className="btn btn-secondary"
          onClick={() => { refreshRuns(); refreshLogs(); }}
        >
          <RefreshCw size={18} />
          Atualizar
        </button>
      </div>

      <div className="logs-layout">
        {/* Sidebar - Run selector */}
        <aside className="runs-sidebar">
          <div className="sidebar-header">
            <h3>Execuções</h3>
          </div>
          
          <div className="runs-list">
            <button
              className={`run-item ${!selectedRun ? 'active' : ''}`}
              onClick={() => setSelectedRun(null)}
            >
              <span>Todos os logs</span>
              {!selectedRun && <ChevronRight size={16} />}
            </button>
            
            {runsLoading ? (
              <div className="loading-small">
                <Loader2 className="spinner" size={20} />
              </div>
            ) : (
              runs.map((run) => (
                <button
                  key={run.id}
                  className={`run-item ${selectedRun === run.id ? 'active' : ''}`}
                  onClick={() => setSelectedRun(run.id)}
                >
                  <div className="run-item-content">
                    <span className={`status-dot status-${run.status}`}></span>
                    <span className="run-date">
                      {new Date(run.started_at).toLocaleDateString('pt-BR')}
                    </span>
                    <span className="run-time">
                      {new Date(run.started_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  {selectedRun === run.id && <ChevronRight size={16} />}
                </button>
              ))
            )}
          </div>
        </aside>

        {/* Main content - Logs */}
        <main className="logs-content">
          {/* Filters */}
          <div className="logs-filters">
            <div className="filter-group">
              <Filter size={18} />
              <select
                value={levelFilter || ''}
                onChange={(e) => setLevelFilter(e.target.value || null)}
              >
                <option value="">Todos os níveis</option>
                <option value="ERROR">Erros</option>
                <option value="WARNING">Avisos</option>
                <option value="INFO">Info</option>
                <option value="DEBUG">Debug</option>
              </select>
            </div>

            <div className="filter-group">
              <span>Mostrar:</span>
              <select
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
              >
                <option value="50">50 logs</option>
                <option value="100">100 logs</option>
                <option value="250">250 logs</option>
                <option value="500">500 logs</option>
              </select>
            </div>
          </div>

          {/* Logs list */}
          <div className="logs-list">
            {logsLoading ? (
              <div className="loading-state">
                <Loader2 className="spinner" size={32} />
                <span>Carregando logs...</span>
              </div>
            ) : logs.length > 0 ? (
              logs.map((log) => (
                <div key={log.id} className={`log-entry ${getLevelClass(log.level)}`}>
                  <div className="log-header">
                    {getLevelIcon(log.level)}
                    <span className="log-level">{log.level}</span>
                    <span className="log-timestamp">{formatDate(log.created_at)}</span>
                  </div>
                  <div className="log-message">{log.message}</div>
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <details className="log-metadata">
                      <summary>
                        <ChevronDown size={14} />
                        Metadados
                      </summary>
                      <pre>{JSON.stringify(log.metadata, null, 2)}</pre>
                    </details>
                  )}
                </div>
              ))
            ) : (
              <div className="empty-state">
                <FileText size={48} />
                <p>Nenhum log encontrado</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
