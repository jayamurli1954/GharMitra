/**
 * Authentication Service
 * Handles user authentication, registration, and session management
 */
import api from './api';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  apartment_number: string;
  phone_number?: string;
  role?: 'admin' | 'member';
  // Legal consent fields (DPDP Act 2023 compliance)
  terms_accepted: boolean;
  privacy_accepted: boolean;
  consent_version?: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  apartment_number: string;
  role: 'admin' | 'member';
  phone_number?: string;
  terms_accepted?: boolean;
  privacy_accepted?: boolean;
  consent_timestamp?: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authService = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/api/auth/login', credentials);
    const { access_token, user } = response.data;

    // Store token and user data
    await AsyncStorage.setItem('access_token', access_token);
    await AsyncStorage.setItem('user', JSON.stringify(user));

    return response.data;
  },

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/api/auth/register', data);
    const { access_token, user } = response.data;

    // Store token and user data
    await AsyncStorage.setItem('access_token', access_token);
    await AsyncStorage.setItem('user', JSON.stringify(user));

    return response.data;
  },

  /**
   * Logout - clear session data
   */
  async logout(): Promise<void> {
    await AsyncStorage.removeItem('access_token');
    await AsyncStorage.removeItem('user');
  },

  /**
   * Get current user from backend
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/api/auth/me');
    await AsyncStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  },

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const token = await AsyncStorage.getItem('access_token');
    return token !== null;
  },

  /**
   * Get stored user data (from AsyncStorage)
   */
  async getStoredUser(): Promise<User | null> {
    const userStr = await AsyncStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Refresh token (if implementing token refresh)
   */
  async refreshToken(): Promise<string> {
    const response = await api.post<{ access_token: string }>('/api/auth/refresh');
    const { access_token } = response.data;
    await AsyncStorage.setItem('access_token', access_token);
    return access_token;
  },
};
