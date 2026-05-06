/**
 * ============================================
 * API Service — Smart Health Surveillance System
 * ============================================
 * Handles all communication with the Flask backend.
 * Supports: YOLO detection, ML prediction, alerts,
 * patient data, symptom reporting, heatmap, resources,
 * offline sync, and IoT sensor data.
 */

import axios from 'axios';

// Base URL for the Flask API
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Accept': 'application/json',
  },
});

// Add interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('aquaguard_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ============================================
// YOLO Detection
// ============================================

/**
 * YOLO Image Detection
 * @param {File} imageFile - Image file to analyze
 * @param {string} model - YOLO model name (default: water_contamination)
 * @param {number} confidence - Confidence threshold (default: 0.25)
 * @returns {Promise<Object>} Detection results
 */
export const predictImage = async (imageFile, model = 'water_contamination', confidence = 0.25) => {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('model', model);
  formData.append('confidence', confidence.toString());

  const response = await api.post('/predict-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/**
 * Run all YOLO models on an image
 */
export const predictImageAllModels = async (imageFile) => {
  const formData = new FormData();
  formData.append('image', imageFile);

  const response = await api.post('/predict-image/all', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// ============================================
// ML Risk Prediction
// ============================================

/**
 * ML Risk Prediction
 * @param {Object} sensorData - Water quality sensor readings
 * @returns {Promise<Object>} Risk prediction results
 */
export const predictRisk = async (sensorData) => {
  const response = await api.post('/predict-risk', sensorData);
  return response.data;
};

// ============================================
// Alerts
// ============================================

/**
 * Send Manual Alert
 */
export const sendAlert = async (riskLevel, message) => {
  const response = await api.post('/send-alert', {
    risk_level: riskLevel,
    message: message,
    alert_type: 'manual',
  });
  return response.data;
};

/**
 * Get alert history
 */
export const getAlertHistory = async (limit = 20) => {
  const response = await api.get(`/alerts/history?limit=${limit}`);
  return response.data;
};

/**
 * Get alert statistics
 */
export const getAlertStats = async () => {
  const response = await api.get('/api/alerts');
  // Temporary transform if it returns the full alerts array instead of stats
  if (response.data.alerts) {
    const alerts = response.data.alerts;
    return {
      total: alerts.length,
      high_risk_alerts: alerts.filter(a => a.risk_level === 'HIGH').length,
    };
  }
  return response.data;
};

export const getWaterTrends = async () => {
  const response = await api.get('/api/water-trends');
  return response.data;
};

export const getRiskDistribution = async () => {
  const response = await api.get('/api/risk-distribution');
  return response.data;
};

export const getDiseaseStats = async () => {
  const response = await api.get('/api/disease-stats');
  return response.data;
};

// ============================================
// Health Surveillance APIs
// ============================================

/**
 * Register a new patient
 */
export const registerPatient = async (patientData) => {
  const response = await api.post('/api/patients', patientData);
  return response.data;
};

/**
 * List patients
 */
export const getPatients = async (filters = {}) => {
  const params = new URLSearchParams(filters).toString();
  const response = await api.get(`/api/patients?${params}`);
  return response.data;
};

/**
 * Submit symptom report
 */
export const submitSymptomReport = async (reportData) => {
  const response = await api.post('/api/symptoms', reportData);
  return response.data;
};

/**
 * Get symptom reports
 */
export const getSymptomReports = async (filters = {}) => {
  const params = new URLSearchParams(filters).toString();
  const response = await api.get(`/api/symptoms?${params}`);
  return response.data;
};

/**
 * Submit water quality reading
 */
export const submitWaterQuality = async (readingData) => {
  const response = await api.post('/api/water-quality', readingData);
  return response.data;
};

/**
 * Get water quality readings
 */
export const getWaterQuality = async (filters = {}) => {
  const params = new URLSearchParams(filters).toString();
  const response = await api.get(`/api/water-quality?${params}`);
  return response.data;
};

// ============================================
// Heatmap & Dashboard
// ============================================

/**
 * Get heatmap data (geo-located disease clusters, water quality, sensors)
 */
export const getHeatmapData = async (type = 'all', days = 7) => {
  const response = await api.get(`/api/heatmap?type=${type}&days=${days}`);
  return response.data;
};

/**
 * Get dashboard statistics
 */
export const getDashboardStats = async () => {
  const response = await api.get('/api/dashboard/stats');
  return response.data;
};

// ============================================
// IoT Sensors
// ============================================

/**
 * Send IoT sensor data
 */
export const sendSensorData = async (sensorData) => {
  const response = await api.post('/api/sensors', sensorData);
  return response.data;
};

/**
 * Get list of IoT sensors
 */
export const getSensors = async () => {
  const response = await api.get('/api/sensors');
  return response.data;
};

// ============================================
// Resource Allocation
// ============================================

/**
 * Get resource allocation data
 */
export const getResources = async () => {
  const response = await api.get('/api/resources');
  return response.data;
};

/**
 * Allocate resources to a village
 */
export const allocateResource = async (village, resourceType, quantity) => {
  const response = await api.post('/api/resources/allocate', {
    village,
    resource_type: resourceType,
    quantity,
  });
  return response.data;
};

// ============================================
// Offline Sync
// ============================================

/**
 * Sync offline collected data
 */
export const syncOfflineData = async (records, deviceId = 'web_dashboard') => {
  const response = await api.post('/api/sync', {
    device_id: deviceId,
    records: records,
  });
  return response.data;
};

/**
 * Process SMS input
 */
export const processSmsInput = async (message, from = 'web_dashboard') => {
  const response = await api.post('/api/sms-input', { message, from });
  return response.data;
};

// ============================================
// System
// ============================================

/**
 * Get available YOLO models
 */
export const getModels = async () => {
  const response = await api.get('/models');
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
