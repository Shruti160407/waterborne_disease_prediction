import React, { useState, useEffect, useRef } from 'react';

/**
 * DiseaseHeatmap Component
 * Interactive map showing disease hotspots, water quality markers,
 * and IoT sensor locations across monitored regions.
 * Uses Leaflet via CDN for compatibility.
 */
const DiseaseHeatmap = () => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [days, setDays] = useState(7);
  const [showLayers, setShowLayers] = useState({
    symptoms: true,
    water: true,
    sensors: true,
  });

  // Fetch heatmap data from API
  useEffect(() => {
    fetchHeatmapData();
  }, [days, filter]);

  const fetchHeatmapData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:5000/api/heatmap?type=${filter}&days=${days}`
      );
      const data = await response.json();
      setHeatmapData(data);
    } catch (err) {
      // Use demo data if API is not available
      setHeatmapData(generateDemoData());
    }
    setLoading(false);
  };

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapRef.current) return;

    // Load Leaflet CSS
    if (!document.querySelector('link[href*="leaflet"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      document.head.appendChild(link);
    }

    // Load Leaflet JS
    const loadLeaflet = () => {
      return new Promise((resolve) => {
        if (window.L) return resolve(window.L);
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.onload = () => resolve(window.L);
        document.head.appendChild(script);
      });
    };

    let mounted = true;
    let mapReady = false;

    const initMap = async () => {
      const L = await loadLeaflet();
      
      // Wait for CSS to load and container to have proper dimensions
      await new Promise(resolve => setTimeout(resolve, 500));
      
      if (!mounted || !mapRef.current || mapInstanceRef.current) return;
      
      const container = mapRef.current;
      // Force container dimensions explicitly
      container.style.width = '100%';
      container.style.height = '520px';
      
      // Wait one more frame for layout
      await new Promise(resolve => requestAnimationFrame(resolve));
      await new Promise(resolve => setTimeout(resolve, 100));

      if (!mounted) return;

      try {
        const map = L.map(container, {
          zoomControl: true,
          attributionControl: false,
          center: [26.5, 92.5],
          zoom: 7,
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
          maxZoom: 18,
        }).addTo(map);

        mapInstanceRef.current = map;

        // Wait for map to be fully ready before adding any markers
        map.whenReady(() => {
          mapReady = true;
          map.invalidateSize();
          // Only add markers after map is fully ready
          setTimeout(() => {
            if (mounted && heatmapData) {
              updateMapMarkers(L, map);
            }
          }, 300);
        });

      } catch (err) {
        console.warn('Leaflet init error:', err);
      }
    };

    initMap();

    return () => {
      mounted = false;
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) { /* ignore cleanup errors */ }
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update markers when data changes - but only if map is ready
  useEffect(() => {
    if (!mapInstanceRef.current || !heatmapData || !window.L) return;
    // Add a small delay to ensure map has finished rendering
    const timer = setTimeout(() => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.invalidateSize();
        updateMapMarkers(window.L, mapInstanceRef.current);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [heatmapData, showLayers]);

  const updateMapMarkers = (L, map) => {
    if (!heatmapData) return;
    
    // Ensure map has valid size before adding markers
    try {
      const size = map.getSize();
      if (!size || size.x === 0 || size.y === 0) {
        // Map not ready yet, retry later
        setTimeout(() => updateMapMarkers(L, map), 500);
        return;
      }
    } catch (e) {
      return;
    }

    // Clear existing markers
    map.eachLayer((layer) => {
      if (layer instanceof L.CircleMarker || layer instanceof L.Marker) {
        map.removeLayer(layer);
      }
    });

    const riskColors = { LOW: '#00e676', MEDIUM: '#ffab40', HIGH: '#ff5252', CRITICAL: '#ff1744' };
    const severitySize = { mild: 6, moderate: 10, severe: 15, critical: 20 };

    // Symptom clusters
    if (showLayers.symptoms && heatmapData.symptom_clusters) {
      heatmapData.symptom_clusters.forEach((cluster) => {
        if (!cluster.latitude || !cluster.longitude) return;
        const severity = cluster.severity || 'moderate';
        const radius = (severitySize[severity] || 10) * Math.sqrt(cluster.case_count || 1);
        const color = cluster.case_count > 10 ? '#ff5252' : cluster.case_count > 5 ? '#ffab40' : '#448aff';

        L.circleMarker([cluster.latitude, cluster.longitude], {
          radius: Math.min(radius, 35),
          color: color,
          fillColor: color,
          fillOpacity: 0.4,
          weight: 2,
        })
          .bindPopup(`
            <div style="font-family:Inter,sans-serif;min-width:200px">
              <strong style="color:${color};font-size:14px">🦠 ${cluster.suspected_disease || 'Disease Cluster'}</strong><br/>
              <hr style="border-color:#333;margin:6px 0"/>
              <b>Cases:</b> ${cluster.case_count}<br/>
              <b>Severity:</b> ${cluster.severity || 'N/A'}<br/>
              <b>Date:</b> ${cluster.created_at || 'Recent'}<br/>
              <small style="color:#999">Lat: ${cluster.latitude?.toFixed(3)}, Lon: ${cluster.longitude?.toFixed(3)}</small>
            </div>
          `)
          .addTo(map);
      });
    }

    // Water quality markers
    if (showLayers.water && heatmapData.water_quality) {
      heatmapData.water_quality.forEach((wq) => {
        if (!wq.latitude || !wq.longitude) return;
        const color = riskColors[wq.risk_level] || '#448aff';

        L.circleMarker([wq.latitude, wq.longitude], {
          radius: 7,
          color: color,
          fillColor: color,
          fillOpacity: 0.6,
          weight: 1,
        })
          .bindPopup(`
            <div style="font-family:Inter,sans-serif;min-width:180px">
              <strong style="color:${color}">💧 ${wq.source_name || 'Water Source'}</strong><br/>
              <hr style="border-color:#333;margin:6px 0"/>
              <b>Risk:</b> <span style="color:${color}">${wq.risk_level}</span><br/>
              <b>pH:</b> ${wq.ph_level || 'N/A'}<br/>
              <b>Bacteria:</b> ${wq.bacteria_count_cfu_ml || 'N/A'} CFU/mL<br/>
              <small style="color:#999">${wq.created_at || ''}</small>
            </div>
          `)
          .addTo(map);
      });
    }

    // IoT Sensors
    if (showLayers.sensors && heatmapData.sensors) {
      heatmapData.sensors.forEach((sensor) => {
        if (!sensor.latitude || !sensor.longitude) return;
        const isActive = sensor.status === 'active';
        const color = isActive ? '#00e5ff' : '#ff5252';

        L.circleMarker([sensor.latitude, sensor.longitude], {
          radius: 5,
          color: color,
          fillColor: color,
          fillOpacity: 0.8,
          weight: 2,
        })
          .bindPopup(`
            <div style="font-family:Inter,sans-serif;min-width:160px">
              <strong style="color:${color}">📡 ${sensor.location_name || sensor.sensor_id}</strong><br/>
              <hr style="border-color:#333;margin:6px 0"/>
              <b>Status:</b> <span style="color:${color}">${sensor.status}</span><br/>
              <b>Battery:</b> ${sensor.battery_level}%<br/>
              <b>Last Reading:</b> ${sensor.last_reading_at || 'N/A'}<br/>
            </div>
          `)
          .addTo(map);
      });
    }
  };

  const generateDemoData = () => ({
    symptom_clusters: [
      { latitude: 26.95, longitude: 94.17, suspected_disease: 'cholera', severity: 'severe', case_count: 12, created_at: 'Today' },
      { latitude: 26.02, longitude: 89.98, suspected_disease: 'typhoid', severity: 'moderate', case_count: 8, created_at: 'Today' },
      { latitude: 24.82, longitude: 92.78, suspected_disease: 'diarrheal', severity: 'mild', case_count: 15, created_at: 'Yesterday' },
      { latitude: 26.63, longitude: 92.80, suspected_disease: 'cholera', severity: 'critical', case_count: 22, created_at: 'Today' },
      { latitude: 26.75, longitude: 94.22, suspected_disease: 'dysentery', severity: 'moderate', case_count: 6, created_at: '2 days ago' },
      { latitude: 27.47, longitude: 94.91, suspected_disease: 'hepatitis_a', severity: 'severe', case_count: 4, created_at: 'Today' },
      { latitude: 26.35, longitude: 92.69, suspected_disease: 'typhoid', severity: 'moderate', case_count: 9, created_at: 'Yesterday' },
      { latitude: 26.32, longitude: 91.00, suspected_disease: 'cholera', severity: 'severe', case_count: 18, created_at: 'Today' },
    ],
    water_quality: [
      { latitude: 26.95, longitude: 94.17, risk_level: 'HIGH', source_name: 'Majuli River', ph_level: 5.5, bacteria_count_cfu_ml: 1500 },
      { latitude: 26.02, longitude: 89.98, risk_level: 'MEDIUM', source_name: 'Dhubri Well', ph_level: 6.2, bacteria_count_cfu_ml: 600 },
      { latitude: 26.63, longitude: 92.80, risk_level: 'HIGH', source_name: 'Tezpur Pond', ph_level: 5.8, bacteria_count_cfu_ml: 2200 },
      { latitude: 26.75, longitude: 94.22, risk_level: 'LOW', source_name: 'Jorhat Tap', ph_level: 7.1, bacteria_count_cfu_ml: 80 },
      { latitude: 26.35, longitude: 92.69, risk_level: 'MEDIUM', source_name: 'Nagaon River', ph_level: 6.5, bacteria_count_cfu_ml: 750 },
    ],
    sensors: [
      { sensor_id: 'IOT-MAJ-001', latitude: 26.96, longitude: 94.18, status: 'active', battery_level: 85, location_name: 'Majuli Sensor #1' },
      { sensor_id: 'IOT-DHU-001', latitude: 26.03, longitude: 89.99, status: 'active', battery_level: 62, location_name: 'Dhubri Sensor #1' },
      { sensor_id: 'IOT-TEZ-001', latitude: 26.64, longitude: 92.81, status: 'error', battery_level: 5, location_name: 'Tezpur Sensor #1' },
      { sensor_id: 'IOT-JOR-001', latitude: 26.76, longitude: 94.23, status: 'active', battery_level: 91, location_name: 'Jorhat Sensor #1' },
      { sensor_id: 'IOT-NAG-001', latitude: 26.36, longitude: 92.70, status: 'inactive', battery_level: 0, location_name: 'Nagaon Sensor #1' },
    ],
  });

  const totalSymptoms = heatmapData?.symptom_clusters?.reduce((s, c) => s + (c.case_count || 0), 0) || 0;
  const highRiskWater = heatmapData?.water_quality?.filter(w => w.risk_level === 'HIGH').length || 0;
  const activeSensors = heatmapData?.sensors?.filter(s => s.status === 'active').length || 0;
  const totalSensors = heatmapData?.sensors?.length || 0;

  return (
    <div>
      <h2 className="section-title">
        <span className="section-title__icon">🗺️</span>
        Disease Surveillance Heatmap
      </h2>

      {/* Stats Row */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card">
          <span className="stat-card__label">Total Cases (Mapped)</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-red)' }}>{totalSymptoms}</span>
          <span className="stat-card__change" style={{ color: 'var(--text-muted)' }}>Last {days} days</span>
        </div>
        <div className="stat-card">
          <span className="stat-card__label">Disease Clusters</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-orange)' }}>
            {heatmapData?.symptom_clusters?.length || 0}
          </span>
          <span className="stat-card__change">Active hotspots</span>
        </div>
        <div className="stat-card">
          <span className="stat-card__label">High-Risk Water</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-red)' }}>{highRiskWater}</span>
          <span className="stat-card__change" style={{ color: 'var(--accent-red)' }}>⚠ Sources contaminated</span>
        </div>
        <div className="stat-card">
          <span className="stat-card__label">Active Sensors</span>
          <span className="stat-card__value" style={{ color: 'var(--accent-cyan)' }}>
            {activeSensors}/{totalSensors}
          </span>
          <span className="stat-card__change" style={{ color: activeSensors === totalSensors ? 'var(--accent-green)' : 'var(--accent-orange)' }}>
            {activeSensors === totalSensors ? '✅ All online' : '⚠ Some offline'}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          className="select"
          value={days}
          onChange={(e) => setDays(parseInt(e.target.value))}
          style={{ background: 'var(--bg-input)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', padding: '8px 14px', borderRadius: 'var(--radius-sm)' }}
        >
          <option value="1">Last 24 hours</option>
          <option value="3">Last 3 days</option>
          <option value="7">Last 7 days</option>
          <option value="14">Last 14 days</option>
          <option value="30">Last 30 days</option>
        </select>

        {/* Layer toggles */}
        {[
          { key: 'symptoms', label: '🦠 Disease Cases', color: '#ff5252' },
          { key: 'water', label: '💧 Water Quality', color: '#448aff' },
          { key: 'sensors', label: '📡 IoT Sensors', color: '#00e5ff' },
        ].map(layer => (
          <button
            key={layer.key}
            className={`btn ${showLayers[layer.key] ? 'btn--primary' : 'btn--outline'}`}
            onClick={() => setShowLayers(prev => ({ ...prev, [layer.key]: !prev[layer.key] }))}
            style={{
              padding: '8px 14px',
              fontSize: '0.8rem',
              borderColor: showLayers[layer.key] ? 'transparent' : layer.color,
              color: showLayers[layer.key] ? 'white' : layer.color,
            }}
          >
            {layer.label}
          </button>
        ))}

        <button className="btn btn--outline" onClick={fetchHeatmapData} style={{ padding: '8px 14px', fontSize: '0.8rem' }}>
          🔄 Refresh
        </button>
      </div>

      {/* Map Container */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', height: '520px', position: 'relative' }}>
        {loading && (
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(10, 14, 39, 0.8)', zIndex: 1000,
          }}>
            <div className="spinner" />
          </div>
        )}
        <div ref={mapRef} style={{ width: '100%', height: '100%' }} id="disease-heatmap" />
      </div>

      {/* Legend */}
      <div className="card" style={{ marginTop: '1rem' }}>
        <div className="card__title">📋 Map Legend</div>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          {[
            { color: '#ff5252', label: 'High Risk / Severe Cases', shape: 'circle' },
            { color: '#ffab40', label: 'Medium Risk / Moderate Cases', shape: 'circle' },
            { color: '#448aff', label: 'Low Risk Water Sources', shape: 'circle' },
            { color: '#00e676', label: 'Safe Water Sources', shape: 'circle' },
            { color: '#00e5ff', label: 'Active IoT Sensor', shape: 'diamond' },
            { color: '#ff5252', label: 'Offline/Error Sensor', shape: 'diamond' },
          ].map((item, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{
                width: 12, height: 12,
                borderRadius: item.shape === 'circle' ? '50%' : '2px',
                background: item.color,
                transform: item.shape === 'diamond' ? 'rotate(45deg)' : 'none',
                boxShadow: `0 0 8px ${item.color}40`,
              }} />
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DiseaseHeatmap;
