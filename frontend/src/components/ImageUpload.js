import React, { useState, useRef, useCallback } from 'react';
import api from '../services/api';

const RISK_COLORS = {
  CRITICAL: '#ff2d2d',
  HIGH: '#ff8c00',
  MEDIUM: '#ffd700',
  LOW: '#00e676',
};

const CLASS_COLORS = {
  contaminated_water: '#ff2d2d',
  clean_water: '#00e676',
  industrial_waste: '#ff6600',
  sewage: '#ff9900',
  chemical_runoff: '#ff00ff',
  floating_debris: '#00e5ff',
  oil_spill: '#cc3333',
  oil_film: '#cc3333',
  algae_bloom: '#33cc33',
  foam_scum: '#00cccc',
  turbid_water: '#cc9966',
  flood_water: '#0088ff',
  stagnant_water: '#669999',
};

const MODEL_STATUS = [
  { name: 'Fish Disease', key: 'fish_disease' },
  { name: 'Malaria', key: 'malaria' },
  { name: 'Algal Bloom', key: 'algal_bloom' },
  { name: 'Micropathogens', key: 'micro_pathogens' },
  { name: 'Contamination', key: 'water_contamination' },
];

const MODULE_CARDS = [
  { name: 'Harmful Algal Bloom Detection', icon: '🧫', key: 'algal_bloom' },
  { name: 'Water Contamination Detection', icon: '🏭', key: 'water_contamination' },
  { name: 'Fish Disease Detection', icon: '🐟', key: 'fish_disease' },
  { name: 'Malaria Parasite Detection', icon: '🦟', key: 'malaria' },
  { name: 'Microalgae & Pathogen Detection', icon: '🔬', key: 'micro_pathogens' },
];

export default function ImageUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [model, setModel] = useState('water_contamination');
  const [confidence, setConfidence] = useState(0.25);
  const fileInputRef = useRef(null);

  const handleFileSelect = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
      setError(null);
    }
  }, []);

  const handleDemoImage = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Create a synthetic demo contaminated water image
      const canvas = document.createElement('canvas');
      canvas.width = 640;
      canvas.height = 480;
      const ctx = canvas.getContext('2d');
      
      // Draw murky water background
      const grad = ctx.createLinearGradient(0, 0, 0, 480);
      grad.addColorStop(0, '#4a6741');
      grad.addColorStop(0.3, '#5d7a52');
      grad.addColorStop(0.6, '#3d5a35');
      grad.addColorStop(1, '#2d4a28');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 640, 480);

      // Add murky patches
      for (let i = 0; i < 20; i++) {
        ctx.fillStyle = `rgba(${80+Math.random()*60}, ${70+Math.random()*50}, ${30+Math.random()*30}, 0.4)`;
        ctx.beginPath();
        ctx.ellipse(Math.random()*640, Math.random()*480, 30+Math.random()*80, 20+Math.random()*40, 0, 0, Math.PI*2);
        ctx.fill();
      }
      
      // Add bright debris
      for (let i = 0; i < 15; i++) {
        const colors = ['#ffffff', '#eeeeee', '#ddccbb', '#ff4444', '#4488ff', '#44ff44'];
        ctx.fillStyle = colors[Math.floor(Math.random()*colors.length)];
        ctx.fillRect(Math.random()*600, Math.random()*440, 10+Math.random()*30, 5+Math.random()*20);
      }
      
      // Add foam patches
      for (let i = 0; i < 8; i++) {
        ctx.fillStyle = `rgba(220, 220, 210, ${0.3+Math.random()*0.4})`;
        ctx.beginPath();
        ctx.arc(Math.random()*640, Math.random()*480, 15+Math.random()*30, 0, Math.PI*2);
        ctx.fill();
      }

      canvas.toBlob(async (blob) => {
        const file = new File([blob], 'demo_contaminated.jpg', { type: 'image/jpeg' });
        setSelectedFile(file);
        setPreview(URL.createObjectURL(blob));

        // Auto-analyze
        const formData = new FormData();
        formData.append('image', file);
        formData.append('model', model);
        formData.append('confidence', confidence);
        const response = await api.post('/predict-image', formData);
        setResult(response.data);
        setLoading(false);
      }, 'image/jpeg', 0.9);
    } catch (err) {
      setError('Demo failed: ' + err.message);
      setLoading(false);
    }
  }, [model, confidence]);

  const handleAnalyze = useCallback(async () => {
    if (!selectedFile) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('image', selectedFile);
      formData.append('model', model);
      formData.append('confidence', confidence);
      const response = await api.post('/predict-image', formData);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Detection failed. Make sure Flask backend is running.');
    }
    setLoading(false);
  }, [selectedFile, model, confidence]);

  const handleClear = useCallback(() => {
    setSelectedFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  const riskLevel = result?.risk_level || 'LOW';
  const riskScore = result?.risk_score || 0;
  const classDist = result?.class_distribution || {};
  const detections = result?.detections || [];
  const totalObjects = result?.total_objects || detections.length;

  return (
    <div className="hydra-layout">
      {/* Sidebar */}
      <aside className="hydra-sidebar">
        <div className="sidebar-section">
          <h3 className="sidebar-title">DETECTION MODULES</h3>
          {MODEL_STATUS.map(m => (
            <div
              key={m.key}
              className={`sidebar-item ${model === m.key ? 'active' : ''}`}
              onClick={() => setModel(m.key)}
            >
              <span className="sidebar-icon">
                {m.key === 'fish_disease' ? '🐟' : m.key === 'malaria' ? '🦟' : m.key === 'algal_bloom' ? '🧫' : m.key === 'micro_pathogens' ? '🔬' : '💧'}
              </span>
              <span className="sidebar-name">{m.name}</span>
              {result && model === m.key && (
                <span className={`sidebar-badge badge-${riskLevel.toLowerCase()}`}>{riskLevel.substring(0, 3)}</span>
              )}
            </div>
          ))}
        </div>

        <div className="sidebar-section">
          <h3 className="sidebar-title">MODEL STATUS</h3>
          {MODEL_STATUS.map(m => (
            <div key={m.key} className="model-status-item">
              <span>{m.name}</span>
              <span className="status-dot active"></span>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Content */}
      <main className="hydra-main">
        {/* Module Cards */}
        <div className="module-cards-row">
          {MODULE_CARDS.map(mc => (
            <div
              key={mc.key}
              className={`module-card ${model === mc.key ? 'active' : ''}`}
              onClick={() => setModel(mc.key)}
            >
              <span className="module-icon">{mc.icon}</span>
              <span className="module-name">{mc.name}</span>
              <span className="module-status">● ONLINE</span>
            </div>
          ))}
        </div>

        {/* YOLO Detection Engine */}
        <div className="detection-engine-card">
          <h2 className="engine-title">YOLO DETECTION ENGINE</h2>
          <p className="engine-subtitle">Upload an image to run AI-powered waterborne disease detection across all 5 modules</p>

          <div className="engine-content">
            {/* Upload Zone + Preview */}
            <div
              className="upload-zone-hydra"
              onDrop={handleDrop}
              onDragOver={e => e.preventDefault()}
              onClick={() => fileInputRef.current?.click()}
            >
              {preview ? (
                <img src={preview} alt="Upload" className="upload-preview-img" />
              ) : (
                <div className="upload-placeholder">
                  <span className="upload-folder-icon">📁</span>
                  <p>Drop image here or click to browse</p>
                  <p className="upload-formats">PNG · JPG · BMP · TIFF · WEBP · max 16MB</p>
                </div>
              )}
              <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileSelect} hidden />
            </div>

            {/* Original image preview (right side before analysis) */}
            {preview && !result && (
              <div className="preview-panel">
                <img src={preview} alt="Preview" className="preview-original" />
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="detection-controls">
            <div className="control-group">
              <label>DETECTION MODULE</label>
              <select value={model} onChange={e => setModel(e.target.value)} className="model-select-hydra">
                {MODULE_CARDS.map(mc => (
                  <option key={mc.key} value={mc.key}>{mc.icon} {mc.name}</option>
                ))}
              </select>
            </div>
            <button className="btn-run" onClick={handleAnalyze} disabled={!selectedFile || loading}>
              {loading ? '⏳ Analyzing...' : '▶ Run Detection'}
            </button>
            <button className="btn-demo" onClick={handleDemoImage} disabled={loading}>
              💧 Try Demo Image
            </button>
            <button className="btn-clear" onClick={handleClear}>✕ Clear</button>
          </div>

          {error && <div className="error-banner">{error}</div>}
        </div>

        {/* ============ RESULTS ============ */}
        {result && (
          <>
            {/* Stats Bar */}
            <div className="stats-bar">
              <div className="stat-box">
                <span className="stat-value">{totalObjects}</span>
                <span className="stat-label">OBJECTS FOUND</span>
              </div>
              <div className="stat-box">
                <span className="stat-value" style={{ color: RISK_COLORS[riskLevel] }}>{riskScore}%</span>
                <span className="stat-label">RISK SCORE</span>
              </div>
              <div className="stat-box">
                <span className="stat-value">
                  {detections.length > 0 ? Math.round(detections.reduce((s, d) => s + d.confidence, 0) / detections.length * 100) : 0}%
                </span>
                <span className="stat-label">AVG CONFIDENCE</span>
              </div>
              <div className="stat-box">
                <span className="stat-value">{result.analysis_method?.includes('yolo') ? (result.analysis_method === 'yolo+cv' ? 'YOLO+CV' : 'YOLO') : 'CV'}</span>
                <span className="stat-label">ENGINE</span>
              </div>
            </div>

            {/* Annotated Output + Risk Panel */}
            <div className="results-grid">
              {/* Left: Annotated Image */}
              <div className="annotated-panel">
                <div className="panel-header">
                  <span>ANNOTATED OUTPUT</span>
                  <span className="detection-badge">
                    {result.model_name ? `🔬 ${result.model_name.toUpperCase()}` : 'DETECTION'}
                  </span>
                </div>
                {result.annotated_image ? (
                  <img
                    src={`data:image/jpeg;base64,${result.annotated_image}`}
                    alt="Annotated"
                    className="annotated-image"
                  />
                ) : (
                  <img src={preview} alt="Original" className="annotated-image" />
                )}
                {result.is_dangerous && (
                  <div className="action-banner">
                    ⚠ IMMEDIATE ACTION: Critical finding. Isolate affected area and notify authorities.
                  </div>
                )}
              </div>

              {/* Right: Risk Assessment */}
              <div className="risk-panel">
                <h3 className="panel-title">RISK ASSESSMENT</h3>
                <div className="risk-badge-row">
                  <span className="risk-badge-large" style={{ background: RISK_COLORS[riskLevel] }}>
                    {riskLevel}
                  </span>
                </div>
                <div className="risk-score-bar">
                  <span className="risk-bar-label">Risk Score</span>
                  <div className="risk-bar-track">
                    <div
                      className="risk-bar-fill"
                      style={{
                        width: `${riskScore}%`,
                        background: `linear-gradient(90deg, #00e676, #ffd700 50%, #ff2d2d)`
                      }}
                    />
                  </div>
                  <span className="risk-bar-value" style={{ color: RISK_COLORS[riskLevel] }}>{riskScore}</span>
                </div>

                {/* Class Distribution */}
                <h4 className="section-title">CLASS DISTRIBUTION</h4>
                <div className="class-dist">
                  {Object.entries(classDist).map(([cls, count]) => (
                    <div key={cls} className="dist-row">
                      <span className="dist-class">{cls}</span>
                      <div className="dist-bar-container">
                        <div
                          className="dist-bar"
                          style={{
                            width: `${Math.min(100, (count / Math.max(1, totalObjects)) * 100)}%`,
                            background: CLASS_COLORS[cls] || '#00e5ff'
                          }}
                        />
                      </div>
                      <span className="dist-count">{count}</span>
                    </div>
                  ))}
                </div>

                {/* Detections Table */}
                <h4 className="section-title">DETECTIONS <span className="obj-count">{totalObjects} OBJECTS</span></h4>
                <div className="detections-table">
                  <div className="det-header">
                    <span>CLASS</span>
                    <span>CONFIDENCE</span>
                    <span>RISK</span>
                    <span>BBOX</span>
                  </div>
                  {detections.map((det, i) => (
                    <div key={i} className="det-row">
                      <span className="det-class" style={{ background: CLASS_COLORS[det.class] || '#555' }}>
                        {det.class}
                      </span>
                      <span className="det-conf">{Math.round(det.confidence * 100)}%</span>
                      <span className={`det-risk risk-${(det.risk || 'MEDIUM').toLowerCase()}`}>
                        {det.risk || 'MEDIUM'}
                      </span>
                      <span className="det-bbox">
                        [{det.bbox?.map(b => Math.round(b)).join(',')}]
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
