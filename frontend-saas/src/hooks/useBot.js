/**
 * Custom hooks for bot operations
 */
import { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

// Hook for bot status with polling
export function useBotStatus(pollInterval = 5000) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await api.getBotStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, pollInterval);
    return () => clearInterval(interval);
  }, [fetchStatus, pollInterval]);

  return { status, loading, error, refresh: fetchStatus };
}

// Hook for bot config
export function useBotConfig() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const fetchConfig = useCallback(async () => {
    try {
      const data = await api.getConfig();
      setConfig(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConfig = async (newConfig) => {
    setSaving(true);
    try {
      const data = await api.updateConfig(newConfig);
      setConfig(data);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setSaving(false);
    }
  };

  const resetConfig = async () => {
    setSaving(true);
    try {
      await api.resetConfig();
      await fetchConfig();
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  return { config, loading, error, saving, updateConfig, resetConfig, refresh: fetchConfig };
}

// Hook for bot runs history
export function useBotRuns(page = 1, pageSize = 20) {
  const [runs, setRuns] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRuns = useCallback(async () => {
    try {
      const data = await api.listRuns(page, pageSize);
      setRuns(data.runs);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  return { runs, total, loading, error, refresh: fetchRuns };
}

// Hook for bot logs
export function useBotLogs(limit = 100, level = null, runId = null) {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLogs = useCallback(async () => {
    try {
      const data = await api.listLogs(limit, level, runId);
      setLogs(data.logs);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [limit, level, runId]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return { logs, total, loading, error, refresh: fetchLogs };
}
