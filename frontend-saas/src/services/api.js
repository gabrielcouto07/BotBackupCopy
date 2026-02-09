/**
 * API Service - Handles all API calls to the backend
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

class ApiService {
  constructor() {
    this.baseUrl = `${API_BASE_URL}${API_VERSION}`;
    this.token = localStorage.getItem('access_token');
    this.tenantId = localStorage.getItem('tenant_id');
  }

  // Set authentication token
  setToken(token) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  // Set tenant ID
  setTenantId(tenantId) {
    this.tenantId = tenantId;
    localStorage.setItem('tenant_id', tenantId);
  }

  // Clear authentication
  clearAuth() {
    this.token = null;
    this.tenantId = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('tenant_id');
  }

  // Build headers
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (this.tenantId) {
      headers['X-Tenant-ID'] = this.tenantId;
    }

    return headers;
  }

  // Generic request method
  async request(method, endpoint, data = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const options = {
      method,
      headers: this.getHeaders(),
    };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      
      if (response.status === 401) {
        this.clearAuth();
        window.location.href = '/login';
        throw new Error('Sessão expirada. Faça login novamente.');
      }

      const json = await response.json();

      if (!response.ok) {
        throw new Error(json.detail || 'Erro na requisição');
      }

      return json;
    } catch (error) {
      console.error(`API Error [${method} ${endpoint}]:`, error);
      throw error;
    }
  }

  // Auth endpoints
  async register(email, password, fullName, tenantName) {
    const response = await this.request('POST', '/auth/register', {
      email,
      password,
      full_name: fullName,
      tenant_name: tenantName,
    });
    
    this.setToken(response.token.access_token);
    this.setTenantId(response.token.tenant_id);
    
    return response;
  }

  async login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erro no login');
    }

    const data = await response.json();
    this.setToken(data.access_token);
    this.setTenantId(data.tenant_id);
    
    return data;
  }

  async getCurrentUser() {
    return this.request('GET', '/auth/me');
  }

  async listTenants() {
    return this.request('GET', '/auth/tenants');
  }

  async switchTenant(tenantId) {
    const response = await this.request('POST', `/auth/switch-tenant/${tenantId}`);
    this.setToken(response.access_token);
    this.setTenantId(response.tenant_id);
    return response;
  }

  // Bot control endpoints
  async getBotStatus() {
    return this.request('GET', '/bot/status');
  }

  async startBot() {
    return this.request('POST', '/bot/start');
  }

  async stopBot() {
    return this.request('POST', '/bot/stop');
  }

  async testRun(dryRun = true, timeout = 300) {
    return this.request('POST', '/bot/test-run', {
      dry_run: dryRun,
      timeout_seconds: timeout,
    });
  }

  async reloadConfig() {
    return this.request('POST', '/bot/reload-config');
  }

  // Config endpoints
  async getConfig() {
    return this.request('GET', '/bot/config');
  }

  async updateConfig(config) {
    return this.request('PUT', '/bot/config', config);
  }

  async resetConfig() {
    return this.request('POST', '/bot/config/reset');
  }

  // Logs endpoints
  async listRuns(page = 1, pageSize = 20, statusFilter = null) {
    let endpoint = `/bot/runs?page=${page}&page_size=${pageSize}`;
    if (statusFilter) endpoint += `&status_filter=${statusFilter}`;
    return this.request('GET', endpoint);
  }

  async getRunLogs(runId) {
    return this.request('GET', `/bot/logs/${runId}`);
  }

  async listLogs(limit = 100, level = null, runId = null) {
    let endpoint = `/bot/logs?limit=${limit}`;
    if (level) endpoint += `&level=${level}`;
    if (runId) endpoint += `&run_id=${runId}`;
    return this.request('GET', endpoint);
  }

  // Health check
  async healthCheck() {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  }
}

export const api = new ApiService();
export default api;
