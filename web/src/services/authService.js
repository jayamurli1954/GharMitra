/**
 * Web-compatible Authentication Service
 */
import api from './api';
import storage from '../utils/storage';
import supabase from './supabaseClient';

let authListenerRegistered = false;

const setAccessToken = async (token) => {
  if (token) {
    await storage.setItem('access_token', token);
  } else {
    await storage.removeItem('access_token');
  }
};

const setSupabaseUser = async (user) => {
  if (user) {
    await storage.setItem('supabase_user', JSON.stringify(user));
  } else {
    await storage.removeItem('supabase_user');
  }
};

export const authService = {
  /**
   * Register Supabase auth listener once
   */
  async initAuthListener() {
    if (authListenerRegistered) return;
    authListenerRegistered = true;

    try {
      const { data } = await supabase.auth.getSession();
      await setAccessToken(data?.session?.access_token || null);
      await setSupabaseUser(data?.session?.user || null);
    } catch (error) {
      console.warn('Failed to load initial Supabase session:', error);
    }

    supabase.auth.onAuthStateChange(async (_event, session) => {
      try {
        await setAccessToken(session?.access_token || null);
        await setSupabaseUser(session?.user || null);
      } catch (error) {
        console.error('Failed to sync Supabase session:', error);
      }
    });
  },
  /**
   * Login with email and password
   */
  async login(credentials) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: credentials.email,
      password: credentials.password,
    });

    if (error) {
      const err = new Error(error.message);
      err.name = 'SupabaseAuthError';
      throw err;
    }

    const accessToken = data?.session?.access_token || null;
    await setAccessToken(accessToken);
    await setSupabaseUser(data?.user || null);

    // Fetch profile from backend (uses Supabase JWT)
    let backendUser = null;
    try {
      const response = await api.get('/auth/me');
      backendUser = response.data;
    } catch (error) {
      console.warn('Backend profile lookup failed:', error);
    }

    // Store user data (backend profile preferred, fall back to Supabase user)
    const user = backendUser || data?.user || null;
    if (user) {
      await storage.setItem('user', JSON.stringify(user));
    }

    return { access_token: accessToken, user };
  },

  /**
   * Register new user
   */
  async register(data) {
    const { data: authData, error } = await supabase.auth.signUp({
      email: data.email,
      password: data.password,
      options: {
        data: {
          name: data.name,
          apartment_number: data.apartment_number,
          phone_number: data.phone_number || '',
        },
      },
    });

    if (error) {
      const err = new Error(error.message);
      err.name = 'SupabaseAuthError';
      throw err;
    }

    const accessToken = authData?.session?.access_token || null;
    await setAccessToken(accessToken);
    await setSupabaseUser(authData?.user || null);

    // Create or update backend profile
    let backendUser = null;
    try {
      const response = await api.post('/auth/register', data);
      backendUser = response.data?.user || response.data;
    } catch (backendError) {
      const detail = backendError.response?.data?.detail || backendError.message;
      // If already exists, try to fetch profile
      if (detail && String(detail).toLowerCase().includes('already registered')) {
        try {
          const response = await api.get('/auth/me');
          backendUser = response.data;
        } catch (fetchError) {
          console.warn('Failed to fetch backend profile after signup:', fetchError);
        }
      } else {
        console.warn('Backend profile creation failed:', backendError);
      }
    }

    // Store token and user data
    const user = backendUser || authData?.user || null;
    if (user) {
      await storage.setItem('user', JSON.stringify(user));
    }

    return { access_token: accessToken, user };
  },

  /**
   * Logout user
   */
  async logout() {
    try {
      // Trigger backup on logout (background on server)
      await api.post('/database/backup-on-logout');
    } catch (error) {
      console.warn('Backup on logout failed:', error);
    }
    try {
      await supabase.auth.signOut();
    } catch (error) {
      console.warn('Supabase sign out failed:', error);
    }
    await storage.removeItem('access_token');
    await storage.removeItem('user');
    await storage.removeItem('supabase_user');
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
        console.warn('Could not fetch user from API:', apiError.message);
        // Fall back to Supabase user
        const supaUser = await storage.getItem('supabase_user');
        if (supaUser) {
          try {
            return JSON.parse(supaUser);
          } catch (parseError) {
            return null;
          }
        }
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
  /**
   * Update stored user data (after profile update)
   */
  async updateStoredUser(userData) {
    try {
      await storage.setItem('user', JSON.stringify(userData));
    } catch (error) {
      console.error('Error updating stored user:', error);
    }
  },
};

