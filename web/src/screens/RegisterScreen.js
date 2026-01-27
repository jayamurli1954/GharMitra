/**
 * Web-compatible Register Screen
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';

const RegisterScreen = ({ onRegisterSuccess }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    apartment_number: '',
    phone_number: '',
    terms_accepted: false,
    privacy_accepted: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!formData.name || !formData.email || !formData.password || !formData.apartment_number) {
      setError('Please fill in all required fields');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (!formData.terms_accepted || !formData.privacy_accepted) {
      setError('You must accept the Terms of Service and Privacy Policy');
      return;
    }

    setLoading(true);
    try {
      const registerData = {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        apartment_number: formData.apartment_number,
        phone_number: formData.phone_number || undefined,
        terms_accepted: formData.terms_accepted,
        privacy_accepted: formData.privacy_accepted,
      };

      await authService.register(registerData);

      if (onRegisterSuccess) {
        onRegisterSuccess();
      }
      navigate('/splash');
    } catch (err) {
      let errorMessage = 'Registration failed. Please try again.';

      if (err.name === 'SupabaseAuthError') {
        errorMessage = err.message || errorMessage;
      } else if (err.response) {
        const detail = err.response.data?.detail || err.response.data?.message;
        errorMessage = detail || errorMessage;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card" style={{ maxWidth: '450px' }}>
        {/* Logo */}
        <div className="login-logo-container">
          <img
            src="/GharMitra_Logo.png"
            alt="GharMitra Logo"
            className="login-logo"
            style={{ width: '120px', height: '120px', borderRadius: '20px' }}
          />
        </div>
        <h1 className="login-title">Create Account</h1>
        <p className="login-subtitle">Join GharMitra today</p>

        {error && (
          <div className="login-error">
            <div className="login-error-text">{error}</div>
          </div>
        )}

        <form onSubmit={handleRegister} className="login-form">
          <div className="login-input-container">
            <label className="login-label">Full Name *</label>
            <input
              type="text"
              name="name"
              className="login-input"
              placeholder="Enter your full name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="login-input-container">
            <label className="login-label">Email *</label>
            <input
              type="email"
              name="email"
              className="login-input"
              placeholder="Enter your email"
              value={formData.email}
              onChange={handleChange}
              autoComplete="email"
              required
            />
          </div>

          <div className="login-input-container">
            <label className="login-label">Flat/Apartment Number *</label>
            <input
              type="text"
              name="apartment_number"
              className="login-input"
              placeholder="e.g., A-101, B-202"
              value={formData.apartment_number}
              onChange={handleChange}
              required
            />
          </div>

          <div className="login-input-container">
            <label className="login-label">Phone Number</label>
            <input
              type="tel"
              name="phone_number"
              className="login-input"
              placeholder="Enter phone number (optional)"
              value={formData.phone_number}
              onChange={handleChange}
            />
          </div>

          <div className="login-input-container">
            <label className="login-label">Password *</label>
            <input
              type="password"
              name="password"
              className="login-input"
              placeholder="Minimum 6 characters"
              value={formData.password}
              onChange={handleChange}
              autoComplete="new-password"
              required
            />
          </div>

          <div className="login-input-container">
            <label className="login-label">Confirm Password *</label>
            <input
              type="password"
              name="confirmPassword"
              className="login-input"
              placeholder="Re-enter your password"
              value={formData.confirmPassword}
              onChange={handleChange}
              autoComplete="new-password"
              required
            />
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }}>
              <input
                type="checkbox"
                name="terms_accepted"
                checked={formData.terms_accepted}
                onChange={handleChange}
                style={{ width: '18px', height: '18px' }}
              />
              I accept the <a href="/terms" target="_blank" rel="noopener noreferrer" style={{ color: '#E67E22' }}>Terms of Service</a>
            </label>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }}>
              <input
                type="checkbox"
                name="privacy_accepted"
                checked={formData.privacy_accepted}
                onChange={handleChange}
                style={{ width: '18px', height: '18px' }}
              />
              I accept the <a href="/privacy" target="_blank" rel="noopener noreferrer" style={{ color: '#E67E22' }}>Privacy Policy</a>
            </label>
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>

        <div className="login-footer">
          <p className="login-footer-text">
            Already have an account?{' '}
            <a href="/login" className="login-link">Login</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterScreen;
