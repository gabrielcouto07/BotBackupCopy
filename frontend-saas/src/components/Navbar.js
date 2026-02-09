/**
 * Navbar Component
 */
import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  Bot, LayoutDashboard, Settings, FileText, LogOut, 
  User, ChevronDown, Building2 
} from 'lucide-react';

export default function Navbar() {
  const { user, tenant, logout } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/config', label: 'Configurações', icon: Settings },
    { path: '/logs', label: 'Logs', icon: FileText },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/dashboard">
          <Bot size={32} />
          <span>Bot SaaS</span>
        </Link>
      </div>

      <div className="navbar-menu">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="navbar-end">
        {tenant && (
          <div className="tenant-badge">
            <Building2 size={16} />
            <span>{tenant.name}</span>
          </div>
        )}

        <div className="user-menu">
          <button 
            className="user-menu-trigger"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
          >
            <User size={20} />
            <span>{user?.full_name || user?.email}</span>
            <ChevronDown size={16} />
          </button>

          {userMenuOpen && (
            <div className="user-menu-dropdown">
              <div className="user-menu-header">
                <p className="user-email">{user?.email}</p>
                <p className="user-role">{tenant?.subscription_tier}</p>
              </div>
              <hr />
              <button onClick={handleLogout} className="menu-item danger">
                <LogOut size={18} />
                <span>Sair</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
