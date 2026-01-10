/**
 * API Service - Axios instance with authentication interceptors
 */
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import ENV from '../config/env';

// Create axios instance
const api = axios.create({
  baseURL: ENV.API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token to all requests
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await AsyncStorage.getItem('access_token');
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
    if (error.code === 'ECONNREFUSED' || error.code === 'NETWORK_ERROR' || !error.response) {
      console.error('Network Error:', {
        message: error.message,
        code: error.code,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
      });
      
      // Return user-friendly error
      return Promise.reject({
        message: 'Cannot connect to server. Please check:\n1. Backend is running\n2. Phone and laptop are on same WiFi\n3. Correct IP address in config',
        code: 'CONNECTION_ERROR',
        originalError: error,
      });
    }
    
    // 401 Unauthorized - Token expired or invalid
    if (error.response?.status === 401) {
      // Token expired or invalid - logout user
      try {
        await AsyncStorage.removeItem('access_token');
        await AsyncStorage.removeItem('user');
        // Note: Navigation to login screen will be handled by App.tsx
        console.log('Session expired. Please login again.');
      } catch (err) {
        console.error('Error clearing storage:', err);
      }
    }
    
    // 403 Forbidden - User doesn't have permission OR not authenticated
    if (error.response?.status === 403) {
      const errorDetail = error.response?.data?.detail || error.response?.data?.message || 'You do not have permission to perform this action';
      
      // If it's an auth endpoint (like /auth/me), treat it like 401 - token invalid
      if (error.config?.url?.includes('/auth/')) {
        try {
          await AsyncStorage.removeItem('access_token');
          await AsyncStorage.removeItem('user');
          console.log('Session expired. Please login again.');
        } catch (err) {
          console.error('Error clearing storage:', err);
        }
      }
      
      console.error('Permission Error (403):', {
        message: errorDetail,
        url: error.config?.url,
        method: error.config?.method,
      });
      
      return Promise.reject({
        message: errorDetail || 'Admin access required. Please login as an administrator.',
        code: 'FORBIDDEN',
        status: 403,
        originalError: error,
      });
    }
    
    // 404 Not Found
    if (error.response?.status === 404) {
      const errorDetail = error.response?.data?.detail || 'Resource not found';
      console.error('Not Found (404):', {
        message: errorDetail,
        url: error.config?.url,
        method: error.config?.method,
      });
      
      return Promise.reject({
        message: errorDetail,
        code: 'NOT_FOUND',
        status: 404,
        originalError: error,
      });
    }
    
    // 500 Internal Server Error - Show more details
    if (error.response?.status === 500) {
      const errorDetail = error.response?.data?.error || error.response?.data?.detail || 'Internal server error';
      console.error('Server Error (500):', {
        message: errorDetail,
        url: error.config?.url,
        method: error.config?.method,
        data: error.response?.data,
      });
      
      // Return user-friendly error with details
      return Promise.reject({
        message: `Server error: ${errorDetail}`,
        code: 'SERVER_ERROR',
        status: 500,
        originalError: error,
      });
    }
    
    return Promise.reject(error);
  }
);

export default api;
export { ENV };
