/**
 * Authentication Context - Manages user authentication state
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is authenticated on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const tenantId = localStorage.getItem('tenant_id');

    if (token && tenantId) {
      api.setToken(token);
      api.setTenantId(tenantId);
      loadUser();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async () => {
    try {
      const userData = await api.getCurrentUser();
      setUser(userData);
      
      // Load tenant info
      const tenants = await api.listTenants();
      const currentTenant = tenants.find(t => t.id === localStorage.getItem('tenant_id'));
      setTenant(currentTenant);
      
    } catch (err) {
      console.error('Failed to load user:', err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    setError(null);
    try {
      await api.login(email, password);
      await loadUser();
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  const register = async (email, password, fullName, tenantName) => {
    setError(null);
    try {
      const response = await api.register(email, password, fullName, tenantName);
      setUser(response.user);
      setTenant(response.tenant);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  const logout = useCallback(() => {
    api.clearAuth();
    setUser(null);
    setTenant(null);
  }, []);

  const switchTenant = async (tenantId) => {
    try {
      await api.switchTenant(tenantId);
      const tenants = await api.listTenants();
      const newTenant = tenants.find(t => t.id === tenantId);
      setTenant(newTenant);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  const value = {
    user,
    tenant,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    switchTenant,
    clearError: () => setError(null),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
