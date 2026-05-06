import React, { useState } from 'react';
import { predictRisk } from '../services/api';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip
} from 'recharts';

/**
 * RiskPrediction Component
 * ML-based outbreak prediction from water quality sensor inputs.
 * Shows risk gauges, predictions, feature importance, and suggested actions.
 */
const RiskPrediction = () => {
  const [formData, setFormData] = useState({
    contaminant_level_ppm: 25,
    ph_level: 7.0,
    turbidity_ntu: 10,
    dissolved_oxygen_mg_l: 6.5,
    nitrate_levels: 8,
    lead_concentration: 0.01,
    bacteria_count_cfu_ml: 200,
    rainfall: 120,
    temperature: 28,
    sanitation_coverage: 65,
    population_density: 500,
    access_to_clean_water: 70,
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fields = [
    { key: 'contaminant_level_ppm', label: 'Contaminant Level (ppm)', min: 0, max: 100, step: 0.5, icon: '⚗️' },
    { key: 'ph_level', label: 'pH Level', min: 0, max: 14, step: 0.1, icon: '🧪' },
    { key: 'turbidity_ntu', label: 'Turbidity (NTU)', min: 0, max: 100, step: 0.5, icon: '💧' },
    { key: 'dissolved_oxygen_mg_l', label: 'Dissolved Oxygen (mg/L)', min: 0, max: 15, step: 0.1, icon: '🫧' },
    { key: 'nitrate_levels', label: 'Nitrate Levels', min: 0, max: 50, step: 0.5, icon: '🧫' },
    { key: 'lead_concentration', label: 'Lead Concentration', min: 0, max: 0.1, step: 0.001, icon: '⚠️' },
    { key: 'bacteria_count_cfu_ml', label: 'Bacteria Count (CFU/mL)', min: 0, max: 5000, step: 10, icon: '🦠' },
    { key: 'rainfall', label: 'Rainfall (mm)', min: 0, max: 500, step: 5, icon: '🌧️' },
    { key: 'temperature', label: 'Temperature (°C)', min: 10, max: 50, step: 0.5, icon: '🌡️' },
    { key: 'sanitation_coverage', label: 'Sanitation Coverage (%)', min: 0, max: 100, step: 1, icon: '🚿' },
    { key: 'population_density', label: 'Population Density (per km²)', min: 50, max: 5000, step: 10, icon: '👥' },
    { key: 'access_to_clean_water', label: 'Clean Water Access (%)', min: 0, max: 100, step: 1, icon: '🚰' },
  ];

  const handleChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: parseFloat(value) || 0 }));
  };

  const handlePreset = (preset) => {
    const presets = {
      safe: {
        contaminant_level_ppm: 5, ph_level: 7.2, turbidity_ntu: 3,
        dissolved_oxygen_mg_l: 8.5, nitrate_levels: 3, lead_concentration: 0.002,
        bacteria_count_cfu_ml: 50, rainfall: 80, temperature: 25,
        sanitation_coverage: 90, population_density: 300, access_to_clean_water: 95,
      },
      moderate: {
        contaminant_level_ppm: 35, ph_level: 6.5, turbidity_ntu: 18,
        dissolved_oxygen_mg_l: 5.0, nitrate_levels: 12, lead_concentration: 0.012,
        bacteria_count_cfu_ml: 500, rainfall: 150, temperature: 30,
        sanitation_coverage: 55, population_density: 800, access_to_clean_water: 60,
      },
      danger: {
        contaminant_level_ppm: 65, ph_level: 5.5, turbidity_ntu: 35,
        dissolved_oxygen_mg_l: 3.0, nitrate_levels: 25, lead_concentration: 0.035,
        bacteria_count_cfu_ml: 1500, rainfall: 250, temperature: 35,
        sanitation_coverage: 30, population_density: 1500, access_to_clean_water: 35,
      },
    };
    setFormData(presets[preset]);
    setResults(null);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await predictRisk(formData);
      setResults(result);
    } catch (err) {
      const msg = err.response?.data?.error || err.message;
      setError(`Prediction failed: ${msg}. Make sure Flask backend is running.`);
    } finally {
      setLoading(false);
    }
  };

  const riskColorMap = { LOW: '#00e676', MEDIUM: '#ffab40', HIGH: '#ff5252' };

  // Prepare radar chart data from form
  const radarData = [
    { param: 'pH', value: Math.min(100, (formData.ph_level / 14) * 100), fullMark: 100 },
    { param: 'Turbidity', value: Math.min(100, formData.turbidity_ntu), fullMark: 100 },
    { param: 'Bacteria', value: Math.min(100, (formData.bacteria_count_cfu_ml / 2000) * 100), fullMark: 100 },
    { param: 'Contaminant', value: Math.min(100, formData.contaminant_level_ppm), fullMark: 100 },
    { param: 'Lead', value: Math.min(100, (formData.lead_concentration / 0.05) * 100), fullMark: 100 },
    { param: 'Nitrate', value: Math.min(100, (formData.nitrate_levels / 50) * 100), fullMark: 100 },
  ];

  return (
    <div>
      <h2 className="section-title">
        <span className="section-title__icon">🧠</span>
        Outbreak Risk Prediction
      </h2>

      {/* Preset Buttons */}
      <div style={{ display: 'flex', gap: 10, marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', alignSelf: 'center' }}>Quick presets:</span>
        <button className="btn btn--success" onClick={() => handlePreset('safe')} id="preset-safe">✅ Safe Water</button>
        <button className="btn btn--outline" onClick={() => handlePreset('moderate')} style={{ borderColor: 'var(--accent-orange)', color: 'var(--accent-orange)' }} id="preset-moderate">⚠️ Moderate Risk</button>
        <button className="btn btn--danger" onClick={() => handlePreset('danger')} id="preset-danger">🚨 High Risk</button>
      </div>

      <div className="grid-2">
        {/* Left: Input Form */}
        <div className="card">
          <div className="card__title">📊 Water Quality Parameters</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
            {fields.map(field => (
              <div className="input-group" key={field.key}>
                <label className="input-group__label">
                  {field.icon} {field.label}
                </label>
                <input
                  className="input-group__input"
                  type="number"
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  value={formData[field.key]}
                  onChange={(e) => handleChange(field.key, e.target.value)}
                  id={`input-${field.key}`}
                />
              </div>
            ))}
          </div>

          {/* Radar Chart */}
          <div style={{ marginTop: '1.5rem' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 8 }}>Parameter Overview:</div>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="param" stroke="#5c6bc0" fontSize={11} />
                <PolarRadiusAxis angle={30} stroke="rgba(255,255,255,0.1)" fontSize={9} />
                <Radar name="Values" dataKey="value" stroke="#448aff" fill="#448aff" fillOpacity={0.25} strokeWidth={2} />
                <Tooltip contentStyle={{ background: '#161b4a', border: '1px solid rgba(68,138,255,0.3)', borderRadius: '8px', color: '#e8eaf6' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <button
            className="btn btn--primary btn--lg"
            style={{ width: '100%', marginTop: '1rem' }}
            onClick={handleSubmit}
            disabled={loading}
            id="predict-btn"
          >
            {loading ? '⏳ Predicting...' : '🧠 Predict Outbreak Risk'}
          </button>

          {error && (
            <div className="alert-banner alert-banner--danger" style={{ marginTop: '1rem' }}>
              <span>❌</span><span>{error}</span>
            </div>
          )}
        </div>

        {/* Right: Results */}
        <div>
          {results ? (
            <div className="fade-in">
              {/* Risk Gauge */}
              <div className="card" style={{ marginBottom: '1rem' }}>
                <div className="risk-gauge">
                  <div className={`risk-gauge__circle risk-gauge__circle--${results.overall_risk?.toLowerCase()}`}>
                    <div className="risk-gauge__level" style={{ color: riskColorMap[results.overall_risk] }}>
                      {results.overall_risk}
                    </div>
                    <div className="risk-gauge__label">Overall Risk</div>
                  </div>
                  {results.is_demo && (
                    <div className="alert-banner alert-banner--info" style={{ marginTop: '1rem', justifyContent: 'center' }}>
                      <span>ℹ️</span><span style={{ fontSize: '0.8rem' }}>Demo mode — Train ML model for accurate predictions</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Disease Predictions */}
              <div className="card" style={{ marginBottom: '1rem' }}>
                <div className="card__title">🦠 Disease Predictions</div>
                {results.predictions && Object.entries(results.predictions).map(([disease, info]) => (
                  <div key={disease} style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>
                        {disease.replace(/_/g, ' ').replace('per 100000', '/ 100K')}
                      </span>
                      <span className={`risk-badge risk-badge--${info.risk_level?.toLowerCase()}`}>
                        {info.risk_level}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div className="progress" style={{ flex: 1 }}>
                        <div
                          className={`progress__bar progress__bar--${info.risk_level === 'HIGH' ? 'red' : info.risk_level === 'MEDIUM' ? 'orange' : 'green'}`}
                          style={{ width: `${Math.min(100, (info.predicted_cases / (info.thresholds?.high || 100)) * 100)}%` }}
                        />
                      </div>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--accent-cyan)', minWidth: 60 }}>
                        {info.predicted_cases}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Feature Importance */}
              {results.feature_importance && (
                <div className="card" style={{ marginBottom: '1rem' }}>
                  <div className="card__title">🔍 Feature Importance (Explainability)</div>
                  {Object.entries(results.feature_importance).slice(0, 8).map(([feat, imp]) => {
                    const maxImp = Math.max(...Object.values(results.feature_importance));
                    return (
                      <div className="feature-bar" key={feat}>
                        <span className="feature-bar__name">{feat.replace(/_/g, ' ')}</span>
                        <div className="feature-bar__track">
                          <div className="feature-bar__fill" style={{ width: `${(imp / maxImp) * 100}%` }} />
                        </div>
                        <span className="feature-bar__value">{(imp * 100).toFixed(1)}%</span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Suggested Actions */}
              {results.suggested_actions && (
                <div className="card">
                  <div className="card__title">📋 Suggested Actions</div>
                  {results.suggested_actions.map((action, idx) => (
                    <div className="action-item" key={idx}>{action}</div>
                  ))}
                </div>
              )}

              {/* Alert triggered */}
              {results.alert_triggered && (
                <div className="alert-banner alert-banner--danger" style={{ marginTop: '1rem' }}>
                  <span>🚨</span>
                  <span>Alert Sent: {results.alert_triggered.alert_id} | SMS: {results.alert_triggered.sms_sent ? 'Sent ✅' : 'Not configured'}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '6rem 2rem' }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem', opacity: 0.3 }}>🧠</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>
                Enter water quality parameters and click Predict
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                Uses ML model to predict cholera, typhoid, and diarrheal cases
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskPrediction;
