import React, { useState, useCallback } from 'react';
import { useI18n } from './i18n';

/**
 * DataEntry Component
 * ASHA Worker / Clinic symptom reporting form.
 * Supports offline data collection with local storage fallback.
 * Multilingual labels using i18n context.
 */
const DataEntry = () => {
  const { t, lang } = useI18n();
  const [formData, setFormData] = useState({
    patient_name: '',
    patient_age: '',
    patient_gender: 'M',
    village: '',
    district: '',
    reporter_type: 'asha_worker',
    reporter_id: '',
    symptoms: '',
    severity: 'moderate',
    onset_date: '',
    fever: false,
    diarrhea: false,
    vomiting: false,
    abdominal_pain: false,
    dehydration: false,
    blood_in_stool: false,
    skin_rash: false,
    jaundice: false,
    suspected_disease: '',
    water_source: '',
    notes: '',
  });

  const [submitState, setSubmitState] = useState({ loading: false, success: false, error: null });
  const [offlineQueue, setOfflineQueue] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('aquaguard_offline_queue') || '[]');
    } catch { return []; }
  });
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // Track online/offline status
  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleChange = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleCheckbox = useCallback((field) => {
    setFormData(prev => ({ ...prev, [field]: !prev[field] }));
  }, []);

  const handleSubmit = async () => {
    if (!formData.patient_name || !formData.symptoms) {
      setSubmitState({ loading: false, success: false, error: 'Patient name and symptoms are required.' });
      return;
    }

    setSubmitState({ loading: true, success: false, error: null });

    // Build symptom text from checkboxes + text
    const symptomList = [];
    if (formData.fever) symptomList.push('fever');
    if (formData.diarrhea) symptomList.push('diarrhea');
    if (formData.vomiting) symptomList.push('vomiting');
    if (formData.abdominal_pain) symptomList.push('abdominal_pain');
    if (formData.dehydration) symptomList.push('dehydration');
    if (formData.blood_in_stool) symptomList.push('blood_in_stool');
    if (formData.skin_rash) symptomList.push('skin_rash');
    if (formData.jaundice) symptomList.push('jaundice');

    const payload = {
      ...formData,
      symptoms: [...symptomList, formData.symptoms].filter(Boolean).join(', '),
    };

    if (!isOnline) {
      // Save offline
      const queue = [...offlineQueue, { ...payload, saved_at: new Date().toISOString() }];
      localStorage.setItem('aquaguard_offline_queue', JSON.stringify(queue));
      setOfflineQueue(queue);
      setSubmitState({ loading: false, success: true, error: null });
      resetForm();
      return;
    }

    try {
      // First register patient, then submit symptom report
      let patientId = null;
      if (formData.patient_name) {
        try {
          const patRes = await fetch('http://localhost:5000/api/patients', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: formData.patient_name,
              age: formData.patient_age ? parseInt(formData.patient_age) : null,
              gender: formData.patient_gender,
              village: formData.village,
              district: formData.district,
              asha_worker_id: formData.reporter_id,
            }),
          });
          const patData = await patRes.json();
          patientId = patData.patient_id;
        } catch (e) { /* Continue without patient registration */ }
      }

      const response = await fetch('http://localhost:5000/api/symptoms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, patient_id: patientId }),
      });

      if (!response.ok) throw new Error('Server error');
      const result = await response.json();

      setSubmitState({ loading: false, success: true, error: null });
      resetForm();
    } catch (err) {
      // Fallback to offline
      const queue = [...offlineQueue, { ...payload, saved_at: new Date().toISOString() }];
      localStorage.setItem('aquaguard_offline_queue', JSON.stringify(queue));
      setOfflineQueue(queue);
      setSubmitState({ loading: false, success: true, error: 'Saved offline — will sync when connected.' });
    }
  };

  const syncOfflineData = async () => {
    if (offlineQueue.length === 0) return;

    try {
      const response = await fetch('http://localhost:5000/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_id: 'web_dashboard',
          records: offlineQueue.map(r => ({
            type: 'symptom_report',
            data: r,
          })),
        }),
      });

      if (response.ok) {
        localStorage.removeItem('aquaguard_offline_queue');
        setOfflineQueue([]);
        setSubmitState({ loading: false, success: true, error: null });
      }
    } catch (err) {
      setSubmitState({ loading: false, success: false, error: 'Sync failed. Will retry later.' });
    }
  };

  const resetForm = () => {
    setFormData({
      patient_name: '', patient_age: '', patient_gender: 'M',
      village: '', district: '', reporter_type: 'asha_worker',
      reporter_id: '', symptoms: '', severity: 'moderate',
      onset_date: '', fever: false, diarrhea: false, vomiting: false,
      abdominal_pain: false, dehydration: false, blood_in_stool: false,
      skin_rash: false, jaundice: false, suspected_disease: '', water_source: '', notes: '',
    });
  };

  const villages = ['Majuli', 'Dhubri', 'Silchar', 'Tezpur', 'Jorhat', 'Dibrugarh', 'Nagaon', 'Barpeta', 'Goalpara', 'Kokrajhar', 'Morigaon', 'Hailakandi'];
  const diseases = [
    { value: 'cholera', label: `🦠 ${t('cholera')}` },
    { value: 'typhoid', label: `🤒 ${t('typhoid')}` },
    { value: 'diarrheal', label: `💧 ${t('diarrheal')}` },
    { value: 'hepatitis_a', label: `🟡 ${t('hepatitis_a')}` },
    { value: 'leptospirosis', label: `🐀 ${t('leptospirosis', 'Leptospirosis')}` },
    { value: 'dysentery', label: `🩸 ${t('dysentery')}` },
    { value: 'giardiasis', label: `🔬 ${t('giardiasis', 'Giardiasis')}` },
  ];
  const waterSources = ['river', 'well', 'borewell', 'pond', 'tap', 'handpump', 'other'];

  return (
    <div>
      <h2 className="section-title">
        <span className="section-title__icon">📝</span>
        {t('data_collection')}
      </h2>

      {offlineQueue.length > 0 && (
        <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            className="btn btn--primary"
            style={{ padding: '6px 14px', fontSize: '0.8rem' }}
            onClick={syncOfflineData}
          >
            🔄 Sync {offlineQueue.length} pending reports
          </button>
        </div>
      )}

      <div className="grid-2">
        {/* Left: Form */}
        <div>
          {/* Reporter Info */}
          <div className="card" style={{ marginBottom: '1rem' }}>
            <div className="card__title">👤 {t('reporter_info')}</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="input-group">
                <label className="input-group__label">{t('reporter_type')}</label>
                <select
                  className="input-group__input"
                  value={formData.reporter_type}
                  onChange={(e) => handleChange('reporter_type', e.target.value)}
                  id="input-reporter-type"
                >
                  <option value="asha_worker">{t('asha_worker')}</option>
                  <option value="clinic">{t('clinic')}</option>
                  <option value="volunteer">{t('volunteer')}</option>
                  <option value="self">{t('self_report')}</option>
                </select>
              </div>
              <div className="input-group">
                <label className="input-group__label">Reporter ID</label>
                <input className="input-group__input" type="text" placeholder="e.g. ASHA-123"
                  value={formData.reporter_id} onChange={(e) => handleChange('reporter_id', e.target.value)}
                  id="input-reporter-id"
                />
              </div>
            </div>
          </div>

          {/* Patient Info */}
          <div className="card" style={{ marginBottom: '1rem' }}>
            <div className="card__title">🏥 {t('patient_details')}</div>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 12 }}>
              <div className="input-group">
                <label className="input-group__label">{t('patient_name')} *</label>
                <input className="input-group__input" type="text" placeholder="Patient name"
                  value={formData.patient_name} onChange={(e) => handleChange('patient_name', e.target.value)}
                  id="input-patient-name" required
                />
              </div>
              <div className="input-group">
                <label className="input-group__label">{t('patient_age')}</label>
                <input className="input-group__input" type="number" min="0" max="120"
                  value={formData.patient_age} onChange={(e) => handleChange('patient_age', e.target.value)}
                  id="input-patient-age"
                />
              </div>
              <div className="input-group">
                <label className="input-group__label">{t('patient_gender')}</label>
                <select className="input-group__input"
                  value={formData.patient_gender} onChange={(e) => handleChange('patient_gender', e.target.value)}
                  id="input-patient-gender"
                >
                  <option value="M">{t('male')}</option>
                  <option value="F">{t('female')}</option>
                  <option value="O">{t('other')}</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12 }}>
              <div className="input-group">
                <label className="input-group__label">{t('village')}</label>
                <select className="input-group__input"
                  value={formData.village} onChange={(e) => handleChange('village', e.target.value)}
                  id="input-village"
                >
                  <option value="">{lang === 'hi' ? 'गाँव चुनें...' : 'Select village...'}</option>
                  {villages.map(v => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>
              <div className="input-group">
                <label className="input-group__label">{t('district')}</label>
                <input className="input-group__input" type="text" placeholder="District name"
                  value={formData.district} onChange={(e) => handleChange('district', e.target.value)}
                  id="input-district"
                />
              </div>
            </div>
          </div>

          {/* Symptoms */}
          <div className="card" style={{ marginBottom: '1rem' }}>
            <div className="card__title">🩺 {t('symptoms')} *</div>

            {/* Symptom Checkboxes */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 12 }}>
              {[
                { key: 'fever', label: `🌡️ ${t('fever')}` },
                { key: 'diarrhea', label: `💧 ${t('diarrhea')}` },
                { key: 'vomiting', label: `🤮 ${t('vomiting')}` },
                { key: 'abdominal_pain', label: `🤢 ${t('abdominal_pain')}` },
                { key: 'dehydration', label: `😰 ${t('dehydration')}` },
                { key: 'blood_in_stool', label: `🩸 ${t('blood_in_stool')}` },
                { key: 'skin_rash', label: `🔴 ${t('skin_rash')}` },
                { key: 'jaundice', label: `🟡 ${t('jaundice')}` },
              ].map(({ key, label }) => (
                <label
                  key={key}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px',
                    background: formData[key] ? 'rgba(68, 138, 255, 0.15)' : 'var(--bg-input)',
                    border: `1px solid ${formData[key] ? 'var(--accent-blue)' : 'var(--border-color)'}`,
                    borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                    fontSize: '0.78rem', transition: 'var(--transition-fast)',
                  }}
                >
                  <input type="checkbox" checked={formData[key]} onChange={() => handleCheckbox(key)}
                    style={{ accentColor: 'var(--accent-blue)' }}
                  />
                  {label}
                </label>
              ))}
            </div>

            <div className="input-group">
              <label className="input-group__label">{t('additional_symptoms')} *</label>
              <textarea className="input-group__input" rows={2}
                placeholder={lang === 'hi' ? "विस्तार से लक्षण बताएं..." : "Describe symptoms in detail..."}
                value={formData.symptoms} onChange={(e) => handleChange('symptoms', e.target.value)}
                style={{ resize: 'vertical', fontFamily: 'var(--font-primary)' }}
                id="input-symptoms"
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginTop: 12 }}>
              <div className="input-group">
                <label className="input-group__label">{t('severity')}</label>
                <div style={{ display: 'flex', gap: 6 }}>
                  {[
                    { value: 'mild', label: `✅ ${t('mild')}`, color: 'var(--accent-green)' },
                    { value: 'moderate', label: `⚠️ ${t('moderate')}`, color: 'var(--accent-orange)' },
                    { value: 'severe', label: `🔴 ${t('severe')}`, color: 'var(--accent-red)' },
                    { value: 'critical', label: `🚨 ${t('critical')}`, color: '#ff1744' },
                  ].map(sev => (
                    <button key={sev.value}
                      className={`btn ${formData.severity === sev.value ? 'btn--primary' : 'btn--outline'}`}
                      onClick={() => handleChange('severity', sev.value)}
                      style={{
                        flex: 1, padding: '6px 4px', fontSize: '0.7rem',
                        borderColor: formData.severity === sev.value ? 'transparent' : sev.color,
                        color: formData.severity === sev.value ? 'white' : sev.color,
                      }}
                    >
                      {sev.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="input-group">
                <label className="input-group__label">{t('onset_date')}</label>
                <input className="input-group__input" type="date"
                  value={formData.onset_date} onChange={(e) => handleChange('onset_date', e.target.value)}
                  id="input-onset-date"
                />
              </div>
              <div className="input-group">
                <label className="input-group__label">{t('suspected_disease')}</label>
                <select className="input-group__input"
                  value={formData.suspected_disease} onChange={(e) => handleChange('suspected_disease', e.target.value)}
                  id="input-disease"
                >
                  <option value="">{lang === 'hi' ? 'बीमारी चुनें...' : 'Select disease...'}</option>
                  {diseases.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12 }}>
              <div className="input-group">
                <label className="input-group__label">{t('water_source')}</label>
                <select className="input-group__input"
                  value={formData.water_source} onChange={(e) => handleChange('water_source', e.target.value)}
                  id="input-water-source"
                >
                  <option value="">{lang === 'hi' ? 'स्रोत चुनें...' : 'Select source...'}</option>
                  {waterSources.map(ws => (
                    <option key={ws} value={ws}>{ws.charAt(0).toUpperCase() + ws.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div className="input-group">
                <label className="input-group__label">{t('notes')}</label>
                <input className="input-group__input" type="text" placeholder={lang === 'hi' ? "अतिरिक्त नोट्स..." : "Additional notes..."}
                  value={formData.notes} onChange={(e) => handleChange('notes', e.target.value)}
                  id="input-notes"
                />
              </div>
            </div>
          </div>

          {/* Submit */}
          <button
            className={`btn ${formData.severity === 'critical' || formData.severity === 'severe' ? 'btn--danger' : 'btn--primary'} btn--lg`}
            style={{ width: '100%' }}
            onClick={handleSubmit}
            disabled={submitState.loading}
            id="submit-report-btn"
          >
            {submitState.loading ? `⏳ ${t('submitting')}` : isOnline ? `📤 ${t('submit')}` : `💾 ${t('save_offline')}`}
          </button>

          {submitState.success && (
            <div className="alert-banner alert-banner--success" style={{ marginTop: '1rem' }}>
              <span>✅</span>
              <span>{submitState.error || t('success')}</span>
            </div>
          )}
          {submitState.error && !submitState.success && (
            <div className="alert-banner alert-banner--danger" style={{ marginTop: '1rem' }}>
              <span>❌</span><span>{submitState.error}</span>
            </div>
          )}
        </div>

        {/* Right: Summary + Offline Queue */}
        <div>
          {/* Quick Summary Preview */}
          <div className="card" style={{ marginBottom: '1rem' }}>
            <div className="card__title">📋 Report Preview</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 2 }}>
              <div><b>Patient:</b> {formData.patient_name || '—'} ({formData.patient_gender}, {formData.patient_age || '—'} yrs)</div>
              <div><b>Location:</b> {formData.village || '—'}, {formData.district || '—'}</div>
              <div><b>Reporter:</b> {formData.reporter_type} {formData.reporter_id ? `(${formData.reporter_id})` : ''}</div>
              <div>
                <b>Symptoms:</b>{' '}
                {[
                  formData.fever && '🌡️ Fever',
                  formData.diarrhea && '💧 Diarrhea',
                  formData.vomiting && '🤮 Vomiting',
                  formData.abdominal_pain && '🤢 Abdominal Pain',
                  formData.dehydration && '😰 Dehydration',
                  formData.blood_in_stool && '🩸 Blood in Stool',
                  formData.skin_rash && '🔴 Skin Rash',
                  formData.jaundice && '🟡 Jaundice',
                ].filter(Boolean).join(', ') || '—'}
              </div>
              <div><b>Severity:</b>{' '}
                <span className={`risk-badge risk-badge--${formData.severity === 'critical' || formData.severity === 'severe' ? 'high' : formData.severity === 'moderate' ? 'medium' : 'low'}`}
                  style={{ padding: '2px 10px', fontSize: '0.7rem' }}>
                  {formData.severity.toUpperCase()}
                </span>
              </div>
              <div><b>Disease:</b> {formData.suspected_disease || '—'}</div>
              <div><b>Water Source:</b> {formData.water_source || '—'}</div>
            </div>
          </div>

          {/* Offline Queue */}
          <div className="card" style={{ marginBottom: '1rem' }}>
            <div className="card__title">
              📦 Offline Queue ({offlineQueue.length} pending)
            </div>
            {offlineQueue.length > 0 ? (
              <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                {offlineQueue.map((item, idx) => (
                  <div key={idx} style={{
                    padding: '8px 12px', background: 'rgba(255, 171, 64, 0.08)',
                    borderRadius: 'var(--radius-sm)', marginBottom: 6,
                    borderLeft: '3px solid var(--accent-orange)',
                    fontSize: '0.8rem',
                  }}>
                    <div style={{ fontWeight: 600 }}>{item.patient_name} — {item.suspected_disease || 'Unknown'}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                      Saved: {new Date(item.saved_at).toLocaleString()}
                    </div>
                  </div>
                ))}
                <button className="btn btn--primary" style={{ width: '100%', marginTop: 8 }}
                  onClick={syncOfflineData}>
                  🔄 Sync All to Server
                </button>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: '2rem', opacity: 0.3, marginBottom: 8 }}>📭</div>
                <div>No pending offline reports</div>
              </div>
            )}
          </div>

          {/* SMS Fallback Info */}
          <div className="card">
            <div className="card__title">📱 {t('sms_fallback')}</div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
              <p>For areas with no internet, send an SMS:</p>
              <div style={{
                padding: '12px', background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)',
                fontFamily: 'var(--font-mono)', fontSize: '0.78rem', marginTop: 8,
                border: '1px solid var(--border-color)',
              }}>
                REPORT &lt;village&gt; &lt;disease&gt; &lt;severity&gt; &lt;count&gt;
              </div>
              <div style={{ marginTop: 8, fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>
                Example: REPORT Majuli cholera severe 5
              </div>
              <p style={{ marginTop: 8, color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                Send to the designated health surveillance number. Reports are automatically processed and added to the system.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataEntry;
