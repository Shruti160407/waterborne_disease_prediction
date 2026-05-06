import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';

/**
 * ResourceAllocation Component
 * Shows resource distribution across villages,
 * allocation status, and recommendations for government officials.
 */
const ResourceAllocation = () => {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVillage, setSelectedVillage] = useState(null);
  const [allocating, setAllocating] = useState(false);

  useEffect(() => {
    fetchResources();
  }, []);

  const fetchResources = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/resources');
      const data = await response.json();
      setResources(data.allocations || []);
    } catch (err) {
      // Use demo data
      setResources(generateDemoResources());
    }
    setLoading(false);
  };

  const handleAllocate = async (village, resourceType, quantity) => {
    setAllocating(true);
    try {
      await fetch('http://localhost:5000/api/resources/allocate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ village, resource_type: resourceType, quantity }),
      });
      fetchResources();
    } catch (err) {
      // Simulate locally
      setResources(prev => prev.map(v => {
        if (v.village === village) {
          return {
            ...v,
            resources: v.resources.map(r =>
              r.type === resourceType
                ? { ...r, allocated: r.allocated + quantity, available: r.available - quantity }
                : r
            ),
          };
        }
        return v;
      }));
    }
    setAllocating(false);
  };

  const generateDemoResources = () => [
    {
      village: 'Majuli', district: 'Majuli', recent_cases: 22,
      resources: [
        { type: 'medical_team', quantity: 3, allocated: 2, available: 1, status: 'available' },
        { type: 'ors_packets', quantity: 500, allocated: 380, available: 120, status: 'available' },
        { type: 'water_purifier', quantity: 20, allocated: 15, available: 5, status: 'available' },
        { type: 'chlorine_tablets', quantity: 200, allocated: 150, available: 50, status: 'available' },
        { type: 'testing_kit', quantity: 30, allocated: 25, available: 5, status: 'available' },
      ],
    },
    {
      village: 'Tezpur', district: 'Sonitpur', recent_cases: 18,
      resources: [
        { type: 'medical_team', quantity: 2, allocated: 2, available: 0, status: 'available' },
        { type: 'ors_packets', quantity: 300, allocated: 290, available: 10, status: 'available' },
        { type: 'water_purifier', quantity: 15, allocated: 12, available: 3, status: 'available' },
        { type: 'ambulance', quantity: 2, allocated: 1, available: 1, status: 'available' },
        { type: 'iv_fluids', quantity: 100, allocated: 85, available: 15, status: 'available' },
      ],
    },
    {
      village: 'Barpeta', district: 'Barpeta', recent_cases: 15,
      resources: [
        { type: 'medical_team', quantity: 2, allocated: 1, available: 1, status: 'available' },
        { type: 'ors_packets', quantity: 400, allocated: 200, available: 200, status: 'available' },
        { type: 'chlorine_tablets', quantity: 300, allocated: 100, available: 200, status: 'available' },
        { type: 'testing_kit', quantity: 20, allocated: 8, available: 12, status: 'available' },
      ],
    },
    {
      village: 'Dhubri', district: 'Dhubri', recent_cases: 12,
      resources: [
        { type: 'medical_team', quantity: 1, allocated: 1, available: 0, status: 'available' },
        { type: 'ors_packets', quantity: 200, allocated: 180, available: 20, status: 'available' },
        { type: 'water_purifier', quantity: 10, allocated: 8, available: 2, status: 'available' },
        { type: 'ambulance', quantity: 1, allocated: 1, available: 0, status: 'available' },
      ],
    },
    {
      village: 'Nagaon', district: 'Nagaon', recent_cases: 9,
      resources: [
        { type: 'medical_team', quantity: 2, allocated: 0, available: 2, status: 'available' },
        { type: 'ors_packets', quantity: 350, allocated: 120, available: 230, status: 'available' },
        { type: 'chlorine_tablets', quantity: 250, allocated: 80, available: 170, status: 'available' },
        { type: 'testing_kit', quantity: 25, allocated: 10, available: 15, status: 'available' },
      ],
    },
    {
      village: 'Jorhat', district: 'Jorhat', recent_cases: 6,
      resources: [
        { type: 'medical_team', quantity: 2, allocated: 0, available: 2, status: 'available' },
        { type: 'ors_packets', quantity: 300, allocated: 50, available: 250, status: 'available' },
        { type: 'water_purifier', quantity: 12, allocated: 3, available: 9, status: 'available' },
      ],
    },
  ];

  const resourceIcons = {
    medical_team: '👨‍⚕️',
    ors_packets: '💊',
    water_purifier: '🚰',
    chlorine_tablets: '🧪',
    iv_fluids: '💉',
    ambulance: '🚑',
    testing_kit: '🔬',
  };

  const resourceLabels = {
    medical_team: 'Medical Teams',
    ors_packets: 'ORS Packets',
    water_purifier: 'Water Purifiers',
    chlorine_tablets: 'Chlorine Tablets',
    iv_fluids: 'IV Fluids',
    ambulance: 'Ambulances',
    testing_kit: 'Testing Kits',
  };

  // Aggregate stats
  const totalCases = resources.reduce((s, v) => s + (v.recent_cases || 0), 0);
  const criticalVillages = resources.filter(v => (v.recent_cases || 0) > 10).length;

  // Chart data
  const caseChartData = resources
    .sort((a, b) => (b.recent_cases || 0) - (a.recent_cases || 0))
    .slice(0, 8)
    .map(v => ({ name: v.village, cases: v.recent_cases || 0 }));

  const resourcePieData = (() => {
    const counts = {};
    resources.forEach(v => v.resources?.forEach(r => {
      counts[r.type] = (counts[r.type] || 0) + r.quantity;
    }));
    return Object.entries(counts).map(([type, count]) => ({
      name: resourceLabels[type] || type,
      value: count,
    }));
  })();

  const pieColors = ['#448aff', '#7c4dff', '#00e676', '#ffab40', '#ff5252', '#00e5ff', '#ffd740'];

  return (
    <div>
      <h2 className="section-title">
        <span className="section-title__icon">📦</span>
        Resource Allocation & Management
      </h2>

      {/* Stats */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card">
          <span className="stat-card__label">Villages Monitored</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-blue)' }}>{resources.length}</span>
        </div>
        <div className="stat-card">
          <span className="stat-card__label">Total Cases (7d)</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-red)' }}>{totalCases}</span>
        </div>
        <div className="stat-card">
          <span className="stat-card__label">Critical Villages</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-orange)' }}>{criticalVillages}</span>
          <span className="stat-card__change" style={{ color: 'var(--accent-orange)' }}>
            {criticalVillages > 0 ? '⚠ Needs attention' : '✅ All stable'}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-card__label">Resource Types</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-cyan)' }}>{resourcePieData.length}</span>
        </div>
      </div>

      {/* Charts */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="chart-container">
          <div className="card__title">📊 Cases by Village (Last 7 Days)</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={caseChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis type="number" stroke="#9CA3AF" fontSize={12} />
              <YAxis type="category" dataKey="name" stroke="#9CA3AF" fontSize={11} width={80} />
              <Tooltip contentStyle={{
                background: '#ffffff', border: '1px solid #E5E7EB',
                borderRadius: '8px', color: '#1F2937', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
              }} />
              <Bar dataKey="cases" fill="#ff5252" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <div className="card__title">🎯 Resource Distribution</div>
          <div style={{ display: 'flex', alignItems: 'center', height: 280 }}>
            <ResponsiveContainer width="50%" height={250}>
              <PieChart>
                <Pie data={resourcePieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                  paddingAngle={3} dataKey="value">
                  {resourcePieData.map((_, idx) => (
                    <Cell key={idx} fill={pieColors[idx % pieColors.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{
                  background: '#ffffff', border: '1px solid #E5E7EB',
                  borderRadius: '8px', color: '#1F2937', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
                }} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1 }}>
              {resourcePieData.map((item, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <div style={{
                    width: 10, height: 10, borderRadius: '50%',
                    background: pieColors[idx % pieColors.length],
                  }} />
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    {item.name}: <b style={{ color: 'var(--text-primary)' }}>{item.value}</b>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Village Resource Cards */}
      <div className="card__title" style={{ marginBottom: '1rem' }}>🏘️ Village-wise Resource Allocation</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '1rem' }}>
        {loading ? (
          <div className="spinner" style={{ gridColumn: '1 / -1' }} />
        ) : resources.map((village, idx) => {
          const urgency = (village.recent_cases || 0) > 15 ? 'high' : (village.recent_cases || 0) > 8 ? 'medium' : 'low';
          const urgencyColors = { high: 'var(--accent-red)', medium: 'var(--accent-orange)', low: 'var(--accent-green)' };

          return (
            <div key={idx} className="card" style={{
              borderColor: urgency === 'high' ? 'rgba(255, 82, 82, 0.4)' : 'var(--border-color)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>🏘️ {village.village}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{village.district} District</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.3rem', fontWeight: 800, color: urgencyColors[urgency] }}>
                    {village.recent_cases || 0}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>cases/7d</div>
                </div>
              </div>

              {/* Resource bars */}
              {village.resources?.map((r, ridx) => {
                const pct = r.quantity > 0 ? (r.allocated / r.quantity) * 100 : 0;
                const isLow = pct > 80;
                return (
                  <div key={ridx} style={{ marginBottom: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {resourceIcons[r.type]} {resourceLabels[r.type] || r.type}
                      </span>
                      <span style={{
                        fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
                        color: isLow ? 'var(--accent-red)' : 'var(--accent-cyan)',
                      }}>
                        {r.available}/{r.quantity}
                        {isLow && ' ⚠'}
                      </span>
                    </div>
                    <div className="progress">
                      <div
                        className={`progress__bar progress__bar--${pct > 80 ? 'red' : pct > 50 ? 'orange' : 'blue'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}

              {/* Quick allocate button */}
              {urgency === 'high' && (
                <button
                  className="btn btn--danger"
                  style={{ width: '100%', marginTop: 8, padding: '8px', fontSize: '0.8rem' }}
                  onClick={() => {
                    const lowRes = village.resources?.find(r => r.available < r.quantity * 0.2);
                    if (lowRes) handleAllocate(village.village, lowRes.type, 10);
                  }}
                  disabled={allocating}
                >
                  🚨 Emergency Resupply
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Recommendations */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card__title">💡 AI Recommendations</div>
        <div style={{ display: 'grid', gap: 8 }}>
          {resources
            .filter(v => (v.recent_cases || 0) > 10)
            .map((v, idx) => {
              const lowResources = v.resources?.filter(r => r.available < r.quantity * 0.2) || [];
              return (
                <div key={idx} className="action-item" style={{ borderLeftColor: 'var(--accent-red)' }}>
                  🚨 <b>{v.village}</b>: {v.recent_cases} cases in 7 days.
                  {lowResources.length > 0
                    ? ` Running low on ${lowResources.map(r => resourceLabels[r.type]).join(', ')}.`
                    : ' Monitor closely.'}
                  {' '}Deploy additional medical team recommended.
                </div>
              );
            })}
          {resources.filter(v => (v.recent_cases || 0) <= 10).length > 0 && (
            <div className="action-item" style={{ borderLeftColor: 'var(--accent-green)' }}>
              ✅ {resources.filter(v => (v.recent_cases || 0) <= 10).length} villages have stable case counts.
              Continue routine monitoring and maintain resource levels.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResourceAllocation;
