/**
 * Unit tests for authService
 */
import { authService } from '../authService';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}));

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    post: jest.fn(),
    get: jest.fn(),
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() },
    },
  })),
}));

describe('authService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const mockResponse = {
        data: {
          access_token: 'mock-token',
          user: {
            id: 1,
            email: 'test@example.com',
            name: 'Test User',
          },
        },
      };

      // Mock the axios instance
      const mockAxiosInstance = {
        post: jest.fn().mockResolvedValue(mockResponse),
        get: jest.fn(),
        interceptors: {
          request: { use: jest.fn(), eject: jest.fn() },
          response: { use: jest.fn(), eject: jest.fn() },
        },
      };

      // Mock AsyncStorage
      const mockAsyncStorage = {
        getItem: jest.fn(),
        setItem: jest.fn().mockResolvedValue(null),
        removeItem: jest.fn(),
      };

      // Replace the service's axios instance and storage
      (authService as any).api = mockAxiosInstance;
      (authService as any).storage = mockAsyncStorage;

      const result = await authService.login({
        email: 'test@example.com',
        password: 'password123',
      });

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      });
      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'access_token',
        'mock-token'
      );
      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith(
        'user',
        JSON.stringify(mockResponse.data.user)
      );
      expect(result).toEqual(mockResponse.data);
    });

    it('should throw error on login failure', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Invalid credentials' },
        },
      };

      const mockAxiosInstance = {
        post: jest.fn().mockRejectedValue(mockError),
        get: jest.fn(),
        interceptors: {
          request: { use: jest.fn(), eject: jest.fn() },
          response: { use: jest.fn(), eject: jest.fn() },
        },
      };

      (authService as any).api = mockAxiosInstance;

      await expect(
        authService.login({
          email: 'test@example.com',
          password: 'wrongpassword',
        })
      ).rejects.toThrow();

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'wrongpassword',
      });
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when token exists', async () => {
      const mockAsyncStorage = {
        getItem: jest.fn().mockResolvedValue('mock-token'),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      };

      (authService as any).storage = mockAsyncStorage;

      const result = await authService.isAuthenticated();

      expect(result).toBe(true);
      expect(mockAsyncStorage.getItem).toHaveBeenCalledWith('access_token');
    });

    it('should return false when no token exists', async () => {
      const mockAsyncStorage = {
        getItem: jest.fn().mockResolvedValue(null),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      };

      (authService as any).storage = mockAsyncStorage;

      const result = await authService.isAuthenticated();

      expect(result).toBe(false);
      expect(mockAsyncStorage.getItem).toHaveBeenCalledWith('access_token');
    });
  });

  describe('getCurrentUser', () => {
    it('should return user data when authenticated', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
      };

      const mockResponse = {
        data: mockUser,
      };

      const mockAxiosInstance = {
        post: jest.fn(),
        get: jest.fn().mockResolvedValue(mockResponse),
        interceptors: {
          request: { use: jest.fn(), eject: jest.fn() },
          response: { use: jest.fn(), eject: jest.fn() },
        },
      };

      const mockAsyncStorage = {
        getItem: jest.fn().mockResolvedValue('mock-token'),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      };

      (authService as any).api = mockAxiosInstance;
      (authService as any).storage = mockAsyncStorage;

      const result = await authService.getCurrentUser();

      expect(result).toEqual(mockUser);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/auth/me');
    });

    it('should throw error when not authenticated', async () => {
      const mockAsyncStorage = {
        getItem: jest.fn().mockResolvedValue(null),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      };

      (authService as any).storage = mockAsyncStorage;

      await expect(authService.getCurrentUser()).rejects.toThrow(
        'No access token found'
      );
    });
  });

  describe('logout', () => {
    it('should clear stored data on logout', async () => {
      const mockAsyncStorage = {
        getItem: jest.fn(),
        setItem: jest.fn(),
        removeItem: jest.fn().mockResolvedValue(null),
      };

      (authService as any).storage = mockAsyncStorage;

      await authService.logout();

      expect(mockAsyncStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockAsyncStorage.removeItem).toHaveBeenCalledWith('user');
    });
  });
});