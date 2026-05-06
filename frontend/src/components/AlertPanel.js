import React, { useState, useEffect } from 'react';
import { getAlertHistory, getAlertStats, sendAlert } from '../services/api';

/**
 * AlertPanel Component
 * Displays alert history, statistics, and manual alert trigger.
 */
const AlertPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [manualMessage, setManualMessage] = useState('');
  const [manualRisk, setManualRisk] = useState('HIGH');
  const [sendingAlert, setSendingAlert] = useState(false);
  const [sendResult, setSendResult] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [historyRes, statsRes] = await Promise.all([
        getAlertHistory(20).catch(() => ({ alerts: [] })),
        getAlertStats().catch(() => null),
      ]);
      setAlerts(historyRes.alerts || []);
      setStats(statsRes);
    } catch (err) {
      // API might not be running
    } finally {
      setLoading(false);
    }
  };

  const handleSendAlert = async () => {
    if (!manualMessage.trim()) return;
    setSendingAlert(true);
    setSendResult(null);
    try {
      const result = await sendAlert(manualRisk, manualMessage);
      setSendResult(result);
      setManualMessage('');
      fetchData(); // Refresh the list
    } catch (err) {
      setSendResult({ error: err.message });
    } finally {
      setSendingAlert(false);
    }
  };

  const riskColors = {
    LOW: 'var(--accent-green)',
    MEDIUM: 'var(--accent-orange)',
    HIGH: 'var(--accent-red)',
  };

  const riskBg = {
    LOW: 'rgba(0, 230, 118, 0.08)',
    MEDIUM: 'rgba(255, 171, 64, 0.08)',
    HIGH: 'rgba(255, 82, 82, 0.08)',
  };

  const typeIcons = {
    manual: '👤',
    auto_prediction: '🧠',
    detection: '🔬',
    risk: '⚠️',
  };

  return (
    <div>
      <h2 className="section-title">
        <span className="section-title__icon">🚨</span>
        Alert Management
      </h2>

      <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
        {/* Stats Cards */}
        <div className="stat-card">
          <span className="stat-card__label">Total Alerts</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-blue)' }}>
            {stats?.total_alerts ?? 0}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-card__label">High Risk Alerts</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-red)' }}>
            {stats?.high_risk_alerts ?? 0}
          </span>
        </div>
        <div className="stat-card">
          <span className="stat-card__label">SMS Sent</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-cyan)' }}>
            {stats?.sms_sent ?? 0}
          </span>
          <span className="stat-card__change" style={{ color: stats?.twilio_configured ? 'var(--accent-green)' : 'var(--text-muted)' }}>
            {stats?.twilio_configured ? '✅ Twilio Active' : '⚙️ SMS Not Configured'}
          </span>
        </div>
      </div>

      <div className="grid-2">
        {/* Left: Manual Alert */}
        <div>
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card__title">📤 Send Manual Alert</div>

            <div className="input-group" style={{ marginBottom: '1rem' }}>
              <label className="input-group__label">Risk Level</label>
              <div style={{ display: 'flex', gap: 8 }}>
                {['LOW', 'MEDIUM', 'HIGH'].map(level => (
                  <button
                    key={level}
                    className={`btn ${manualRisk === level ? (level === 'HIGH' ? 'btn--danger' : level === 'MEDIUM' ? 'btn--outline' : 'btn--success') : 'btn--outline'}`}
                    onClick={() => setManualRisk(level)}
                    style={{
                      flex: 1,
                      borderColor: manualRisk === level ? riskColors[level] : 'var(--border-color)',
                      color: manualRisk === level ? (level === 'LOW' ? '#0a0e27' : 'white') : 'var(--text-muted)',
                    }}
                    id={`risk-btn-${level.toLowerCase()}`}
                  >
                    {level === 'LOW' ? '✅' : level === 'MEDIUM' ? '⚠️' : '🚨'} {level}
                  </button>
                ))}
              </div>
            </div>

            <div className="input-group" style={{ marginBottom: '1rem' }}>
              <label className="input-group__label">Alert Message</label>
              <textarea
                className="input-group__input"
                value={manualMessage}
                onChange={(e) => setManualMessage(e.target.value)}
                placeholder="Enter alert message..."
                rows={3}
                style={{ resize: 'vertical', fontFamily: 'var(--font-primary)' }}
                id="alert-message"
              />
            </div>

            <button
              className={`btn ${manualRisk === 'HIGH' ? 'btn--danger' : 'btn--primary'} btn--lg`}
              style={{ width: '100%' }}
              onClick={handleSendAlert}
              disabled={sendingAlert || !manualMessage.trim()}
              id="send-alert-btn"
            >
              {sendingAlert ? '⏳ Sending...' : `🚨 Send ${manualRisk} Alert`}
            </button>

            {sendResult && (
              <div className={`alert-banner ${sendResult.error ? 'alert-banner--danger' : 'alert-banner--success'}`} style={{ marginTop: '1rem' }}>
                <span>{sendResult.error ? '❌' : '✅'}</span>
                <span>
                  {sendResult.error
                    ? `Failed: ${sendResult.error}`
                    : `Alert sent! ID: ${sendResult.alert_id} | SMS: ${sendResult.sms_sent ? 'Sent' : 'Not configured'}`
                  }
                </span>
              </div>
            )}
          </div>


        </div>

        {/* Right: Alert History */}
        <div className="card">
          <div className="card__title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>📜 Alert History</span>
            <button className="btn btn--outline" onClick={fetchData} style={{ padding: '6px 12px', fontSize: '0.8rem' }} id="refresh-alerts">
              🔄 Refresh
            </button>
          </div>

          {loading ? (
            <div className="spinner" />
          ) : alerts.length > 0 ? (
            <div style={{ maxHeight: 500, overflowY: 'auto', paddingRight: 8 }}>
              {alerts.map((alert, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px 14px',
                    background: riskBg[alert.risk_level] || 'transparent',
                    borderRadius: 'var(--radius-sm)',
                    marginBottom: 8,
                    borderLeft: `3px solid ${riskColors[alert.risk_level] || 'var(--accent-blue)'}`,
                    transition: 'var(--transition-fast)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span>{typeIcons[alert.alert_type] || '📢'}</span>
                      <span className={`risk-badge risk-badge--${alert.risk_level?.toLowerCase()}`} style={{ padding: '3px 10px', fontSize: '0.7rem' }}>
                        {alert.risk_level}
                      </span>
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {alert.id}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: 4 }}>
                    {alert.message}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {new Date(alert.timestamp).toLocaleString()}
                    </span>
                    {alert.sms_sent && (
                      <span style={{ fontSize: '0.7rem', color: 'var(--accent-green)' }}>📱 SMS Sent</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem', opacity: 0.3 }}>🔔</div>
              <div>No alerts yet.</div>
              <div style={{ fontSize: '0.8rem', marginTop: 4 }}>Alerts are triggered automatically when HIGH risk is detected.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AlertPanel;
