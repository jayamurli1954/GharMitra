/**
 * Web Version of GharMitra App
 * Adapted from React Native App.tsx for web/desktop
 */
import React, { useEffect, useState, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './styles.css';

// Auth Service (web-compatible)
import { authService } from './services/authService';

// Web-compatible screens
import LoginScreen from './screens/LoginScreen';
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

const App = () => {
  console.log('App component rendering...');
  const [initializing, setInitializing] = useState(true);
  const [user, setUser] = useState(null);
  const [debugInfo, setDebugInfo] = useState([]);
  const [showDebug, setShowDebug] = useState(false);

  // Debug logging function
  const addDebugLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setDebugInfo(prev => [...prev.slice(-9), { timestamp, message, type }]);
    console.log(`[${timestamp}] ${message}`);
  };

  const checkAuthStatus = useCallback(async () => {
    setInitializing(true);
    addDebugLog('Starting authentication check...', 'info');
    try {
      // Check authentication status
      const isAuthenticated = await authService.isAuthenticated();
      addDebugLog(`Authentication status: ${isAuthenticated ? 'Authenticated' : 'Not authenticated'}`, 'info');

      if (isAuthenticated) {
        try {
          // Get user - this will use storage first (fast), only calls API if needed
          const currentUser = await authService.getCurrentUser();
          if (currentUser) {
            addDebugLog(`User loaded: ${currentUser.email || 'Unknown'}`, 'success');
            setUser(currentUser);
          } else {
            // User not found, but token exists - don't logout immediately
            // Token might be valid, just user data fetch failed
            addDebugLog('User data not available, but token exists', 'warning');
            setUser(null); // Show login screen, but keep token for retry
          }
        } catch (error) {
          addDebugLog(`Failed to get current user: ${error.message || 'Unknown error'}`, 'error');
          console.error('Failed to get current user:', error);
          // Don't logout on error - token might still be valid
          setUser(null);
        }
      } else {
        setUser(null);
      }
    } catch (error) {
      addDebugLog(`Auth check failed: ${error.message || 'Unknown error'}`, 'error');
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setInitializing(false);
      addDebugLog('Authentication check completed', 'info');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    addDebugLog('GharMitra app initialized', 'info');
    checkAuthStatus();
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
    <>
      {/* Debug Panel Toggle Button */}
      <button
        onClick={() => setShowDebug(!showDebug)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 10000,
          padding: '10px 15px',
          backgroundColor: '#007AFF',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '12px',
          fontWeight: 'bold',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
        }}
      >
        {showDebug ? 'Hide Debug' : 'Show Debug'}
      </button>

      {/* Debug Panel */}
      {showDebug && (
        <div style={{
          position: 'fixed',
          bottom: '70px',
          right: '20px',
          width: '400px',
          maxHeight: '400px',
          backgroundColor: '#1e1e1e',
          color: '#fff',
          padding: '15px',
          borderRadius: '8px',
          zIndex: 9999,
          overflowY: 'auto',
          fontFamily: 'monospace',
          fontSize: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
        }}>
          <div style={{ marginBottom: '10px', fontWeight: 'bold', color: '#007AFF' }}>
            Debug Console
          </div>
          {debugInfo.length === 0 ? (
            <div style={{ color: '#888' }}>No debug messages yet...</div>
          ) : (
            debugInfo.map((log, index) => (
              <div
                key={index}
                style={{
                  marginBottom: '8px',
                  padding: '5px',
                  backgroundColor: log.type === 'error' ? '#4a1e1e' :
                    log.type === 'warning' ? '#4a3e1e' :
                      log.type === 'success' ? '#1e4a1e' : '#1e1e2e',
                  borderRadius: '4px',
                  borderLeft: `3px solid ${log.type === 'error' ? '#ff4444' :
                    log.type === 'warning' ? '#ffaa00' :
                      log.type === 'success' ? '#44ff44' : '#007AFF'
                    }`
                }}
              >
                <span style={{ color: '#888' }}>[{log.timestamp}]</span>{' '}
                <span style={{
                  color: log.type === 'error' ? '#ff8888' :
                    log.type === 'warning' ? '#ffcc88' :
                      log.type === 'success' ? '#88ff88' : '#fff'
                }}>
                  {log.message}
                </span>
              </div>
            ))
          )}
        </div>
      )}

      <Router>
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
              <Route path="/settings" element={<SettingsScreen />} />
              <Route path="/profile" element={<ProfileScreen />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </>
          ) : (
            <>
              <Route path="/login" element={<LoginScreen onLoginSuccess={checkAuthStatus} />} />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </>
          )}
        </Routes>
      </Router>
    </>
  );
};

export default App;

