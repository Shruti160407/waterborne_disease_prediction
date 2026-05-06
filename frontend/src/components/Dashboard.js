import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { healthCheck, getAlertStats, getWaterTrends, getRiskDistribution, getDiseaseStats } from '../services/api';

/**
 * Dashboard Component
 * Main overview page with stats, charts, and quick actions.
 */
const Dashboard = ({ onNavigate }) => {
  const [apiStatus, setApiStatus] = useState('checking');
  const [alertStats, setAlertStats] = useState(null);
  
  // Real data state
  const [waterTrendData, setWaterTrendData] = useState([]);
  const [riskDistribution, setRiskDistribution] = useState([]);
  const [diseaseData, setDiseaseData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check API health
    healthCheck()
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'));

    // Fetch all real data in parallel
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [alerts, trends, risk, disease] = await Promise.all([
          getAlertStats().catch(() => null),
          getWaterTrends().catch(() => []),
          getRiskDistribution().catch(() => []),
          getDiseaseStats().catch(() => [])
        ]);
        
        if (alerts) setAlertStats(alerts);
        if (trends && trends.length) setWaterTrendData(trends);
        if (risk && risk.length) setRiskDistribution(risk);
        if (disease && disease.length) setDiseaseData(disease);
        
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);

  return (
    <div>


      {/* Stats Row */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card" onClick={() => onNavigate('detection')} style={{ cursor: 'pointer' }}>
          <span className="stat-card__label">Detections Today</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-blue)' }}>24</span>
          <span className="stat-card__change" style={{ color: 'var(--accent-green)' }}>↑ 12% from yesterday</span>
        </div>
        <div className="stat-card" onClick={() => onNavigate('prediction')} style={{ cursor: 'pointer' }}>
          <span className="stat-card__label">Risk Level</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-orange)' }}>MEDIUM</span>
          <span className="stat-card__change" style={{ color: 'var(--accent-orange)' }}>⚠ Elevated risk detected</span>
        </div>
        <div className="stat-card" onClick={() => onNavigate('alerts')} style={{ cursor: 'pointer' }}>
          <span className="stat-card__label">Active Alerts</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-red)' }}>
            {alertStats?.high_risk_alerts || 3}
          </span>
          <span className="stat-card__change" style={{ color: 'var(--accent-red)' }}>🚨 Requires attention</span>
        </div>
        <div className="stat-card">
          <span className="stat-card__label">Water Quality Score</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-cyan)' }}>72</span>
          <span className="stat-card__change" style={{ color: 'var(--accent-orange)' }}>↓ 5 points this week</span>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Water Quality Trends */}
        <div className="chart-container">
          <div className="card__title">📈 Water Quality Trends (7 Days)</div>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={waterTrendData}>
              <defs>
                <linearGradient id="colorPh" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#448aff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#448aff" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorTurb" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ffab40" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ffab40" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="day" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: '#ffffff',
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  color: '#1F2937',
                  fontSize: '0.85rem',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
                }}
              />
              <Area type="monotone" dataKey="ph" stroke="#448aff" fill="url(#colorPh)" strokeWidth={2} name="pH Level" />
              <Area type="monotone" dataKey="turbidity" stroke="#ffab40" fill="url(#colorTurb)" strokeWidth={2} name="Turbidity" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Distribution */}
        <div className="chart-container">
          <div className="card__title">🎯 Risk Distribution</div>
          <div style={{ display: 'flex', alignItems: 'center', height: 280 }}>
            <ResponsiveContainer width="50%" height={250}>
              <PieChart>
                <Pie
                  data={riskDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskDistribution.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#ffffff',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    color: '#1F2937',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1 }}>
              {riskDistribution.map((item, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                  <div style={{
                    width: 12, height: 12, borderRadius: '50%',
                    background: item.color,
                    boxShadow: `0 0 10px ${item.color}40`,
                  }} />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{item.name}</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: item.color }}>{item.value}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Disease Overview & Bacteria Trends */}
      <div className="grid-2">
        {/* Disease Cases */}
        <div className="card">
          <div className="card__title">🦠 Disease Cases Overview</div>
          {diseaseData.map((disease, idx) => (
            <div key={idx} style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{disease.name}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                  {disease.cases} <span style={{ color: disease.trend.startsWith('+') ? 'var(--accent-red)' : 'var(--accent-green)', fontSize: '0.75rem' }}>{disease.trend}</span>
                </span>
              </div>
              <div className="progress">
                <div
                  className={`progress__bar progress__bar--${idx === 0 ? 'red' : idx === 1 ? 'orange' : 'blue'}`}
                  style={{ width: `${Math.min(100, disease.cases / 2)}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Bacteria Count Chart */}
        <div className="chart-container">
          <div className="card__title">🔬 Bacteria Count Trend</div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={waterTrendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="day" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: '#ffffff',
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  color: '#1F2937',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
                }}
              />
              <Bar dataKey="bacteria" fill="#7c4dff" radius={[4, 4, 0, 0]} name="Bacteria (CFU/mL)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Actions */}
      <div style={{ marginTop: '1.5rem', display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <button className="btn btn--primary btn--lg" onClick={() => onNavigate('detection')} id="quick-detect">
          🔬 Analyze Water Sample
        </button>
        <button className="btn btn--primary btn--lg" onClick={() => onNavigate('prediction')} id="quick-predict">
          🧠 Predict Outbreak Risk
        </button>
        <button className="btn btn--danger btn--lg" onClick={() => onNavigate('alerts')} id="quick-alerts">
          🚨 View Alerts
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
