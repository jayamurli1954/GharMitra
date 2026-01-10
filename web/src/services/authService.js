/**
 * Web-compatible Authentication Service
 */
import api from './api';
import storage from '../utils/storage';

export const authService = {
  /**
   * Login with email and password
   */
  async login(credentials) {
    const response = await api.post('/auth/login', credentials);
    const { access_token, user } = response.data;

    // Store token and user data
    await storage.setItem('access_token', access_token);
    await storage.setItem('user', JSON.stringify(user));

    return response.data;
  },

  /**
   * Register new user
   */
  async register(data) {
    const response = await api.post('/auth/register', data);
    const { access_token, user } = response.data;

    // Store token and user data
    await storage.setItem('access_token', access_token);
    await storage.setItem('user', JSON.stringify(user));

    return response.data;
  },

  /**
   * Logout user
   */
  async logout() {
    await storage.removeItem('access_token');
    await storage.removeItem('user');
  },

  /**
   * Check if user is authenticated
   */
  async isAuthenticated() {
    const token = await storage.getItem('access_token');
    return !!token;
  },

  /**
   * Get current user from storage
   */
  async getCurrentUser() {
    try {
      // First, try to get user from storage (fast, no API call)
      const userStr = await storage.getItem('user');
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          // Validate that user object has required fields
          if (user && (user.email || user.id || user.username)) {
            return user;
          }
        } catch (parseError) {
          console.warn('Failed to parse stored user data:', parseError);
          // Continue to try API fetch
        }
      }
      
      // Only try to fetch from API if we have a token but no user in storage
      const token = await storage.getItem('access_token');
      if (!token) {
        return null;
      }
      
      // If not in storage but have token, try to fetch from API with timeout
      // But don't fail if API is unavailable - just return null
      try {
        const response = await Promise.race([
          api.get('/auth/me'),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Request timeout')), 3000)
          )
        ]);
        const user = response.data;
        if (user) {
          await storage.setItem('user', JSON.stringify(user));
          return user;
        }
        return null;
      } catch (apiError) {
        // API call failed - but don't logout, just return null
        // Token might still be valid, user just needs to refresh
        console.warn('Could not fetch user from API:', apiError.message);
        return null;
      }
    } catch (error) {
      console.error('Error getting current user:', error);
      // Don't logout on error - let the app handle it
      return null;
    }
  },

  /**
   * Get stored access token
   */
  async getToken() {
    return await storage.getItem('access_token');
  },
};

