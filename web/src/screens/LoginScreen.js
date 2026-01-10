/**
 * Web-compatible Login Screen
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';

const LoginScreen = ({ onLoginSuccess }) => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please enter email and password');
      return;
    }

    setLoading(true);
    try {
      const response = await authService.login({ email, password });
      if (onLoginSuccess) {
        onLoginSuccess();
      }
      navigate('/splash');
    } catch (err) {
      let errorMessage = 'Login failed. Please try again.';

      if (err.response) {
        const status = err.response.status;
        const detail = err.response.data?.detail || err.response.data?.message;

        if (status === 401) {
          errorMessage = detail || 'Incorrect email or password';
        } else if (status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else {
          errorMessage = detail || errorMessage;
        }
      } else if (err.message) {
        if (err.message.includes('CONNECTION_ERROR') || err.code === 'ECONNREFUSED') {
          errorMessage = 'Cannot connect to server. Please check:\n1. Backend is running\n2. Correct API URL in config';
        } else {
          errorMessage = err.message;
        }
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Logo Video */}
        <div className="login-logo-container">
          <video
            autoPlay
            loop
            muted
            playsInline
            className="login-logo-video"
          >
            <source src="/GharMitra_Logo_Video.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
        <h1 className="login-title">GharMitra</h1>
        <p className="login-subtitle">Your Society, Digitally Simplified</p>

        {error && (
          <div className="login-error">
            <div className="login-error-text">{error}</div>
          </div>
        )}

        <form onSubmit={handleLogin} className="login-form">
          <div className="login-input-container">
            <label className="login-label">Email</label>
            <input
              type="email"
              className="login-input"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          <div className="login-input-container">
            <label className="login-label">Password</label>
            <input
              type="password"
              className="login-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="login-footer">
          <p className="login-footer-text">
            Don't have an account?{' '}
            <a href="/register" className="login-link">Register</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginScreen;
