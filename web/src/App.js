/**
 * Web Version of GharMitra App
 * Adapted from React Native App.tsx for web/desktop
 */
import React, { useEffect, useState, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import './styles.css';

// Auth Service (web-compatible)
import { authService } from './services/authService';

// Web-compatible screens
import LoginScreen from './screens/LoginScreen';
import RegisterScreen from './screens/RegisterScreen';
import SplashScreen from './screens/SplashScreen';
import DashboardScreen from './screens/DashboardScreen';
import AccountingScreen from './screens/AccountingScreen';
import ProfileScreen from './screens/ProfileScreen';
import SettingsScreen from './screens/SettingsScreen';
import ComingSoonScreen from './screens/ComingSoonScreen';
import MembersScreen from './screens/MembersScreen';
import MaintenanceScreen from './screens/MaintenanceScreen';
import MessagesScreen from './screens/MessagesScreen';
import MeetingsScreen from './screens/MeetingsScreen';
import ReportsScreen from './screens/ReportsScreen';
import ComplaintsScreen from './screens/ComplaintsScreen';
import AssetRegisterScreen from './screens/AssetRegisterScreen';
import AddAssetScreen from './screens/AddAssetScreen';
import AssetDetailScreen from './screens/AssetDetailScreen';
import SocietySearchScreen from './screens/SocietySearchScreen';
import JoinRequestsScreen from './screens/JoinRequestsScreen';
import MyMembershipsScreen from './screens/MyMembershipsScreen';

const MobileNav = () => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path || (path === '/' && location.pathname === '/dashboard');

  return (
    <div className="mobile-bottom-nav">
      <Link to="/" className={`nav-item ${isActive('/') ? 'active' : ''}`}>
        <span className="nav-icon">🏠</span>
        <span>Home</span>
      </Link>
      <Link to="/accounting" className={`nav-item ${isActive('/accounting') ? 'active' : ''}`}>
        <span className="nav-icon">💰</span>
        <span>Account</span>
      </Link>
      <Link to="/reports" className={`nav-item ${isActive('/reports') ? 'active' : ''}`}>
        <span className="nav-icon">📊</span>
        <span>Reports</span>
      </Link>
      <Link to="/members" className={`nav-item ${isActive('/members') ? 'active' : ''}`}>
        <span className="nav-icon">👥</span>
        <span>Members</span>
      </Link>
      <Link to="/settings" className={`nav-item ${isActive('/settings') ? 'active' : ''}`}>
        <span className="nav-icon">⚙️</span>
        <span>Setup</span>
      </Link>
    </div>
  );
};

const App = () => {
  console.log('App component rendering...');
  const [initializing, setInitializing] = useState(true);
  const [user, setUser] = useState(null);

  const checkAuthStatus = useCallback(async () => {
    setInitializing(true);
    try {
      // Check authentication status
      const isAuthenticated = await authService.isAuthenticated();

      if (isAuthenticated) {
        try {
          // Get user - this will use storage first (fast), only calls API if needed
          const currentUser = await authService.getCurrentUser();
          if (currentUser) {
            setUser(currentUser);
          } else {
            // User not found, but token exists - don't logout immediately
            setUser(null);
          }
        } catch (error) {
          console.error('Failed to get current user:', error);
          setUser(null);
        }
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setInitializing(false);
    }
  }, []);

  useEffect(() => {
    const initializeAuth = async () => {
      await authService.initAuthListener();
      await checkAuthStatus();
    };
    initializeAuth();
  }, [checkAuthStatus]);

  if (initializing) {
    return (
      <div className="loading-container">
        <div>
          <div className="loading-text">Loading GharMitra...</div>
        </div>
      </div>
    );
  }

  return (
    <Router>
        {user && <MobileNav />}
        <Routes>
          {user ? (
            <>
              <Route path="/splash" element={<SplashScreen />} />
              <Route path="/" element={<DashboardScreen />} />
              <Route path="/dashboard" element={<DashboardScreen />} />
              <Route path="/maintenance" element={<MaintenanceScreen />} />
              <Route path="/accounting" element={<AccountingScreen />} />
              <Route path="/members" element={<MembersScreen />} />
              <Route path="/complaints" element={<ComplaintsScreen />} />
              <Route path="/reports" element={<ReportsScreen />} />
              <Route path="/message" element={<MessagesScreen />} />
              <Route path="/meeting" element={<MeetingsScreen />} />
              <Route path="/assets" element={<AssetRegisterScreen />} />
              <Route path="/assets/add" element={<AddAssetScreen />} />
              <Route path="/assets/:asset_id" element={<AssetDetailScreen />} />
              <Route path="/onboarding/search" element={<SocietySearchScreen />} />
              <Route path="/onboarding/requests" element={<JoinRequestsScreen />} />
              <Route path="/onboarding/memberships" element={<MyMembershipsScreen />} />
              <Route path="/settings" element={<SettingsScreen />} />
              <Route path="/profile" element={<ProfileScreen />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </>
          ) : (
            <>
              <Route path="/login" element={<LoginScreen onLoginSuccess={checkAuthStatus} />} />
              <Route path="/register" element={<RegisterScreen onRegisterSuccess={checkAuthStatus} />} />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </>
          )}
        </Routes>
      </Router>
  );
};

export default App;

