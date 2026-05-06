import React, { useState } from 'react';
import './App.css';
import Dashboard from './components/Dashboard';
import ImageUpload from './components/ImageUpload';
import RiskPrediction from './components/RiskPrediction';
import AlertPanel from './components/AlertPanel';
import DiseaseHeatmap from './components/DiseaseHeatmap';
import DataEntry from './components/DataEntry';
import ResourceAllocation from './components/ResourceAllocation';
import { LanguageSelector } from './components/i18n';
import AuthPage from './components/AuthPage';

/**
 * ============================================
 * AquaGuard AI - Smart Health Surveillance
 * & Early Warning System
 * ============================================
 * Waterborne Disease Monitoring Dashboard
 * 
 * Tabs:
 * 1. Dashboard - Overview with stats and charts
 * 2. Heatmap - Disease surveillance map
 * 3. Data Entry - ASHA worker symptom reporting
 * 4. Image Detection - Upload images for YOLO analysis
 * 5. Risk Prediction - ML-based outbreak prediction
 * 6. Resources - Resource allocation management
 * 7. Alerts - Alert history and management
 */
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  // Auth state
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('aquaguard_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const handleLogout = () => {
    localStorage.removeItem('aquaguard_token');
    localStorage.removeItem('aquaguard_user');
    setUser(null);
  };

  const allTabs = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'heatmap', label: '🗺️ Heatmap', icon: '🗺️' },
    { id: 'data_entry', label: '📝 Data Entry', icon: '📝' },
    { id: 'detection', label: '🔬 Detection', icon: '🔬' },
    { id: 'prediction', label: '🧠 Prediction', icon: '🧠' },
    { id: 'resources', label: '📦 Resources', icon: '📦' },
  ];

  // Role-based access control: Filter tabs based on role
  const tabs = allTabs.filter(tab => {
    if (!user) return false;
    if (user.role !== 'Admin' && (tab.id === 'alerts' || tab.id === 'resources')) {
      return false; // Hide Alerts and Resources from regular users
    }
    return true;
  });

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard onNavigate={setActiveTab} />;
      case 'heatmap':
        return <DiseaseHeatmap />;
      case 'data_entry':
        return <DataEntry />;
      case 'detection':
        return <ImageUpload />;
      case 'prediction':
        return <RiskPrediction />;
      case 'resources':
        return <ResourceAllocation />;
      case 'alerts':
        return <AlertPanel />;
      default:
        return <Dashboard onNavigate={setActiveTab} />;
    }
  };

  if (!user) {
    return <AuthPage onAuthSuccess={(userData) => setUser(userData)} />;
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header__logo">

          <div>
            <div className="header__title">AquaCare</div>
            <div className="header__subtitle">Smart Health Surveillance & Early Warning System</div>
          </div>
        </div>
        <nav className="header__nav">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`header__nav-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              id={`nav-${tab.id}`}
            >
              {tab.label}
            </button>
          ))}
          <LanguageSelector />
          <div style={{ marginLeft: '1rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              👤 {user.name} ({user.role})
            </span>
            <button
              onClick={handleLogout}
              style={{
                background: 'transparent', border: '1px solid var(--border-color)',
                color: 'var(--text-primary)', padding: '4px 10px', borderRadius: '4px',
                cursor: 'pointer', fontSize: '0.8rem'
              }}
            >
              Logout
            </button>
          </div>
        </nav>
      </header>

      {/* Mobile Nav */}
      <div className="mobile-nav">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`mobile-nav__btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="mobile-nav__icon">{tab.icon}</span>
            <span className="mobile-nav__label">{tab.id.replace('_', ' ')}</span>
          </button>
        ))}
      </div>

      {/* Main Content */}
      <main className="main">
        <div className="fade-in" key={activeTab}>
          {renderContent()}
        </div>
      </main>

      {/* Footer */}
      <footer style={{
        textAlign: 'center',
        padding: '1.5rem',
        color: 'var(--text-muted)',
        fontSize: '0.8rem',
        borderTop: '1px solid var(--border-color)',
      }}>
        AquaCare — Smart Health Surveillance & Early Warning System for Waterborne Disease Prevention
      </footer>
    </div>
  );
}

export default App;
