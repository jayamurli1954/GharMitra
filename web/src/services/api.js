/**
 * Web-compatible API Service
 * Uses localStorage instead of AsyncStorage
 */
import axios from 'axios';
import storage from '../utils/storage';

// Determine API URL based on environment
const getApiUrl = () => {
  // TEMPORARY: Use port 8002 until the old backend on 8001 is killed
  // TODO: Change back to 8001 after system restart
  const TEMP_PORT = '8001';  // Matches active backend

  // Check if running in Electron
  if (typeof window !== 'undefined' && window.electron && window.electron.isDesktop) {
    return `http://localhost:${TEMP_PORT}/api`;
  }
  // Check environment variable (webpack will replace this at build time)
  // Use window.__API_URL__ if set, otherwise use default
  if (typeof window !== 'undefined' && window.__API_URL__) {
    return window.__API_URL__;
  }
  // Fallback to default API URL
  return `http://localhost:${TEMP_PORT}/api`;
};

// Create axios instance
const api = axios.create({
  baseURL: getApiUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Log API configuration on initialization
if (typeof window !== 'undefined') {
  console.log('API Service initialized with baseURL:', getApiUrl());
}

// Request interceptor - Add auth token to all requests
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await storage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error getting access token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors globally
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Network error (connection failed)
    if (error.code === 'ECONNREFUSED' || error.code === 'NETWORK_ERROR' || error.code === 'ERR_NETWORK' || !error.response) {
      console.error('Network Error:', {
        message: error.message,
        code: error.code,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
        fullURL: error.config?.baseURL + error.config?.url,
      });

      // Check if it's a CORS error
      if (error.message && error.message.includes('CORS')) {
        return Promise.reject({
          message: 'CORS error: Backend may not be allowing requests from this origin. Check CORS settings.',
          code: 'CORS_ERROR',
          originalError: error,
        });
      }

      return Promise.reject({
        message: 'Cannot connect to server. Please check:\n1. Backend is running at http://localhost:8001\n2. CORS is enabled in backend\n3. No firewall blocking the connection',
        code: 'CONNECTION_ERROR',
        originalError: error,
      });
    }

    // 401 Unauthorized - Token expired or invalid
    if (error.response?.status === 401) {
      try {
        await storage.removeItem('access_token');
        await storage.removeItem('user');
        console.log('Session expired. Please login again.');
        // Redirect to login will be handled by App.js
        window.location.href = '/login';
      } catch (err) {
        console.error('Error clearing storage:', err);
      }
    }

    // 403 Forbidden
    if (error.response?.status === 403) {
      const errorDetail = error.response?.data?.detail || error.response?.data?.message || 'You do not have permission to perform this action';

      if (error.config?.url?.includes('/auth/')) {
        try {
          await storage.removeItem('access_token');
          await storage.removeItem('user');
          window.location.href = '/login';
        } catch (err) {
          console.error('Error clearing storage:', err);
        }
      }

      console.error('Permission Error (403):', {
        message: errorDetail,
        url: error.config?.url,
      });
    }

    return Promise.reject(error);
  }
);

export default api;

