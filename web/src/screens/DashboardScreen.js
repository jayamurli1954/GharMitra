/**
 * GharMitra Dashboard Screen
 * Warm, trust-based design with brand colors
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import api from '../services/api';

const DashboardScreen = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recentActivity, setRecentActivity] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      if (!currentUser) {
        navigate('/login');
        return;
      }
      setUser(currentUser);

      // Load dashboard stats
      try {
        const response = await api.get('/dashboard/summary');
        console.log('Dashboard API Response:', response.data);
        
        // Extract stats from admin_stats object
        const adminStats = response.data?.admin_stats || {};
        console.log('Admin Stats extracted:', adminStats);
        
        const statsData = {
          society_balance: adminStats.society_balance || 0,
          monthly_billing: adminStats.monthly_billing || 0,
          dues_pending: adminStats.dues_pending || 0,
          complaints_open: adminStats.complaints_open || 0,
        };
        
        console.log('Stats data to set:', statsData);
        setStats(statsData);
      } catch (error) {
        console.error('Error loading dashboard stats:', error);
        console.error('Error details:', error.response?.data);
        // Set to 0 if API fails - no hardcoded values
        setStats({
          society_balance: 0,
          monthly_billing: 0,
          dues_pending: 0,
          complaints_open: 0,
        });
      }

      // Load recent activity (mock data for now)
      setRecentActivity([
        { id: 1, text: 'Flat 302 paid ₹5,500', icon: '💰' },
        { id: 2, text: 'Water bill added', icon: '💧' },
        { id: 3, text: 'Complaint: Lift not working', icon: '🛠️' },
        { id: 4, text: 'New tenant approved', icon: '✅' },
      ]);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      if (error.response?.status === 401) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };


  const formatCurrency = (amount) => {
    if (!amount) return '₹ 0';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatSocietyBalance = (amount) => {
    // Society Balance: Remove negative sign (debit balance, not negative)
    if (!amount) return '₹ 0';
    const absAmount = Math.abs(amount);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(absAmount);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-text">Loading...</div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div className="dashboard-header-left">
          <img 
            src="/GharMitra_Logo.png" 
            alt="GharMitra Logo" 
            className="dashboard-logo"
          />
          <div className="dashboard-header-text">
            <div className="dashboard-society-name">
              {user?.society_name || 'GharMitra Demo Society'}
            </div>
            <div className="dashboard-tagline">
              Your Society, Digitally Simplified
            </div>
          </div>
        </div>
        <div className="dashboard-header-right">
          <span className="dashboard-header-icon" title="Notifications">🔔</span>
          <div 
            className="dashboard-user-info"
            onClick={() => navigate('/profile')}
            style={{ cursor: 'pointer' }}
          >
            <div className="dashboard-user-name">{user?.name || user?.email}</div>
            <div className="dashboard-user-role">{user?.role || 'Admin'}</div>
          </div>
          <button onClick={async () => {
            await authService.logout();
            window.location.href = '/login';
          }} className="dashboard-logout-button">
            👤 Logout
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {/* Metric Cards */}
        <div className="dashboard-metrics-grid">
          <div className="dashboard-metric-card">
            <span className="dashboard-metric-icon">💰</span>
            <div className="dashboard-metric-label">Society Balance</div>
            <div className="dashboard-metric-value">
              {formatSocietyBalance(stats?.society_balance || 0)}
            </div>
          </div>

          <div className="dashboard-metric-card">
            <span className="dashboard-metric-icon">🧾</span>
            <div className="dashboard-metric-label">This Month Billing</div>
            <div className="dashboard-metric-value">
              {formatCurrency(stats?.monthly_billing || 0)}
            </div>
          </div>

          <div className="dashboard-metric-card">
            <span className="dashboard-metric-icon">⏳</span>
            <div className="dashboard-metric-label">Dues Pending</div>
            <div className="dashboard-metric-value" style={{ color: 'var(--gm-warning)' }}>
              {formatCurrency(stats?.dues_pending || 0)}
            </div>
          </div>

          <div className="dashboard-metric-card">
            <span className="dashboard-metric-icon">🛠️</span>
            <div className="dashboard-metric-label">Complaints Open</div>
            <div className="dashboard-metric-value" style={{ color: 'var(--gm-danger)' }}>
              {stats?.complaints_open || 0}
            </div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="dashboard-main-grid">
          {/* Quick Actions */}
          <div className="dashboard-quick-actions">
            <h2 className="dashboard-section-title">Quick Actions</h2>
            <div className="dashboard-actions-grid">
              <button 
                className="dashboard-quick-tile"
                onClick={() => navigate('/accounting')}
              >
                <span className="dashboard-quick-tile-icon">🧮</span>
                <p className="dashboard-quick-tile-label">Accounting</p>
              </button>

              <button 
                className="dashboard-quick-tile"
                onClick={() => navigate('/maintenance')}
              >
                <span className="dashboard-quick-tile-icon">🧾</span>
                <p className="dashboard-quick-tile-label">Generate Bills</p>
              </button>

              <button 
                className="dashboard-quick-tile"
                onClick={() => navigate('/members')}
              >
                <span className="dashboard-quick-tile-icon">👥</span>
                <p className="dashboard-quick-tile-label">Members</p>
              </button>

              <button 
                className="dashboard-quick-tile"
                onClick={() => navigate('/complaints')}
              >
                <span className="dashboard-quick-tile-icon">🛠️</span>
                <p className="dashboard-quick-tile-label">Complaints</p>
              </button>

              <button 
                className="dashboard-quick-tile"
                onClick={() => navigate('/reports')}
              >
                <span className="dashboard-quick-tile-icon">📊</span>
                <p className="dashboard-quick-tile-label">Reports</p>
              </button>

              <button 
                className="dashboard-quick-tile"
                onClick={() => navigate('/message')}
              >
                <span className="dashboard-quick-tile-icon">💬</span>
                <p className="dashboard-quick-tile-label">Message</p>
              </button>

              <button 
                className="dashboard-quick-tile"
                onClick={() => navigate('/meeting')}
              >
                <span className="dashboard-quick-tile-icon">📅</span>
                <p className="dashboard-quick-tile-label">Meeting</p>
              </button>

              <button 
                className="dashboard-quick-tile"
                onClick={() => navigate('/settings')}
              >
                <span className="dashboard-quick-tile-icon">⚙️</span>
                <p className="dashboard-quick-tile-label">Settings</p>
              </button>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="dashboard-recent-activity">
            <h2 className="dashboard-section-title">Recent Activity</h2>
            <ul className="dashboard-activity-list">
              {recentActivity.map((activity) => (
                <li key={activity.id} className="dashboard-activity-item">
                  <span className="dashboard-activity-icon">{activity.icon}</span>
                  <span>{activity.text}</span>
                </li>
              ))}
              {recentActivity.length === 0 && (
                <li className="dashboard-activity-item">
                  <span>No recent activity</span>
                </li>
              )}
            </ul>
          </div>
        </div>

        {/* Monthly Collection Trend */}
        <div className="dashboard-chart-section">
          <h2 className="dashboard-section-title">Monthly Collection Trend</h2>
          <div className="dashboard-chart-placeholder">
            📈 Chart visualization coming soon
            <br />
            <span style={{ fontSize: '12px', color: 'var(--gm-text-muted)' }}>
              [ ▁▃▅▇▆▅▇ ]
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardScreen;
