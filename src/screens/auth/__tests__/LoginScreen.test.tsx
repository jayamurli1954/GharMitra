/**
 * Unit tests for LoginScreen component
 */
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import LoginScreen from '../LoginScreen';

// Mock the auth service
jest.mock('../../../services/authService', () => ({
  authService: {
    login: jest.fn(),
    isAuthenticated: jest.fn(),
    getCurrentUser: jest.fn(),
    logout: jest.fn(),
  },
}));

// Mock React Navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

// Mock Alert
jest.spyOn(Alert, 'alert');

describe('LoginScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly', () => {
    const { getByText, getByPlaceholderText } = render(
      <LoginScreen navigation={{} as any} onLoginSuccess={jest.fn()} />
    );

    expect(getByText('GharMitra')).toBeTruthy();
    expect(getByText('Your Society, Digitally Simplified')).toBeTruthy();
    expect(getByPlaceholderText('Email')).toBeTruthy();
    expect(getByPlaceholderText('Password')).toBeTruthy();
    expect(getByText('Login')).toBeTruthy();
  });

  it('shows validation error when fields are empty', async () => {
    const { getByText } = render(
      <LoginScreen navigation={{} as any} onLoginSuccess={jest.fn()} />
    );

    const loginButton = getByText('Login');
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith('Error', 'Please enter email and password');
    });
  });

  it('handles successful login', async () => {
    const mockOnLoginSuccess = jest.fn();
    const { authService } = require('../../../services/authService');

    authService.login.mockResolvedValue({
      user: { name: 'Test User' },
    });

    const { getByText, getByPlaceholderText } = render(
      <LoginScreen navigation={{} as any} onLoginSuccess={mockOnLoginSuccess} />
    );

    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
      expect(Alert.alert).toHaveBeenCalledWith(
        'Success',
        'Welcome back, Test User!'
      );
      expect(mockOnLoginSuccess).toHaveBeenCalled();
    });
  });

  it('handles login error', async () => {
    const { authService } = require('../../../services/authService');

    const mockError = {
      response: {
        status: 401,
        data: { detail: 'Invalid credentials' },
      },
    };
    authService.login.mockRejectedValue(mockError);

    const { getByText, getByPlaceholderText } = render(
      <LoginScreen navigation={{} as any} onLoginSuccess={jest.fn()} />
    );

    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'wrongpassword');
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Login Error',
        'Invalid credentials'
      );
    });
  });

  it('navigates to register society screen', () => {
    const { getByText } = render(
      <LoginScreen navigation={{} as any} onLoginSuccess={jest.fn()} />
    );

    const registerButton = getByText('Register Your Society');
    fireEvent.press(registerButton);

    expect(mockNavigate).toHaveBeenCalledWith('RegisterSociety');
  });

  it('navigates to register screen', () => {
    const { getByText } = render(
      <LoginScreen navigation={{} as any} onLoginSuccess={jest.fn()} />
    );

    const joinButton = getByText('Already a member? Join Existing Society');
    fireEvent.press(joinButton);

    expect(mockNavigate).toHaveBeenCalledWith('Register');
  });

  it('toggles password visibility', () => {
    const { getByPlaceholderText, getByTestId } = render(
      <LoginScreen navigation={{} as any} onLoginSuccess={jest.fn()} />
    );

    const passwordInput = getByPlaceholderText('Password');
    const eyeIcon = getByTestId('eye-icon'); // Assuming testID is set

    // Initially password should be hidden
    expect(passwordInput.props.secureTextEntry).toBe(true);

    fireEvent.press(eyeIcon);

    // After pressing eye icon, password should be visible
    expect(passwordInput.props.secureTextEntry).toBe(false);
  });

  it('shows loading state during login', async () => {
    const { authService } = require('../../../services/authService');

    authService.login.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ user: { name: 'Test' } }), 100))
    );

    const { getByText, getByPlaceholderText } = render(
      <LoginScreen navigation={{} as any} onLoginSuccess={jest.fn()} />
    );

    const emailInput = getByPlaceholderText('Email');
    const passwordInput = getByPlaceholderText('Password');
    const loginButton = getByText('Login');

    fireEvent.changeText(emailInput, 'test@example.com');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Should show loading text
    expect(getByText('Logging in...')).toBeTruthy();

    await waitFor(() => {
      expect(getByText('Login')).toBeTruthy(); // Back to normal text
    });
  });
});