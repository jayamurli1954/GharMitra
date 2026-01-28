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
  const [collectionTrend, setCollectionTrend] = useState([]);
  const [societyInfo, setSocietyInfo] = useState(null);

  useEffect(() => {
    loadData();
    loadSocietyInfo();
  }, []);

  const loadSocietyInfo = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      if (currentUser && currentUser.society_id) {
        const response = await api.get(`/society/${currentUser.society_id}`);
        setSocietyInfo(response.data);
      }
    } catch (error) {
      console.error('Error loading society info:', error);
    }
  };

  const handleViewDocument = async (url) => {
    try {
      const response = await api.get(url, {
        responseType: 'blob'
      });
      const file = new Blob([response.data], { type: response.headers['content-type'] });
      const fileURL = URL.createObjectURL(file);
      window.open(fileURL, '_blank');
    } catch (error) {
      console.error('Error viewing document:', error);
      alert('Failed to open document. ' + (error.response?.data?.detail || error.message));
    }
  };

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
        setCollectionTrend(adminStats.collection_trend || []);

        // Load recent activity from API
        const activities = response.data?.recent_activities || [];
        const mappedActivities = activities.map(act => ({
          id: act.id,
          text: act.title,
          icon: act.icon || 'ℹ️',
          description: act.description
        }));
        setRecentActivity(mappedActivities);
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
                onClick={() => navigate('/onboarding/search')}
              >
                <span className="dashboard-quick-tile-icon">🔎</span>
                <p className="dashboard-quick-tile-label">Find Society</p>
              </button>

              <button
                className="dashboard-quick-tile"
                onClick={() => navigate('/onboarding/memberships')}
              >
                <span className="dashboard-quick-tile-icon">🧾</span>
                <p className="dashboard-quick-tile-label">My Memberships</p>
              </button>

              <button
                className="dashboard-quick-tile"
                onClick={() => navigate('/onboarding/requests')}
              >
                <span className="dashboard-quick-tile-icon">✅</span>
                <p className="dashboard-quick-tile-label">Join Requests</p>
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
                onClick={() => navigate('/assets')}
              >
                <span className="dashboard-quick-tile-icon">🏢</span>
                <p className="dashboard-quick-tile-label">Society Assets</p>
              </button>

              <button
                className="dashboard-quick-tile"
                onClick={() => navigate('/settings')}
              >
                <span className="dashboard-quick-tile-icon">⚙️</span>
                <p className="dashboard-quick-tile-label">Settings</p>
              </button>

              {societyInfo?.legal_config?.bye_laws_url && (
                <button
                  className="dashboard-quick-tile"
                  style={{ border: '2px solid var(--gm-orange)' }}
                  onClick={() => handleViewDocument(societyInfo.legal_config.bye_laws_url)}
                >
                  <span className="dashboard-quick-tile-icon">📜</span>
                  <p className="dashboard-quick-tile-label">Bye-laws</p>
                </button>
              )}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="dashboard-recent-activity">
            <h2 className="dashboard-section-title">Recent Activity</h2>
            <ul className="dashboard-activity-list">
              {recentActivity.map((activity) => (
                <li key={activity.id} className="dashboard-activity-item">
                  <span className="dashboard-activity-icon">{activity.icon}</span>
                  <div className="dashboard-activity-info">
                    <span className="dashboard-activity-text">{activity.text}</span>
                    {activity.description && (
                      <span className="dashboard-activity-desc">{activity.description}</span>
                    )}
                  </div>
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
          <CollectionTrendChart data={collectionTrend} />
        </div>
      </div>
    </div>
  );
};

const CollectionTrendChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="dashboard-chart-placeholder">
        No data available for trend
      </div>
    );
  }

  // Find max amount for scaling
  const maxAmount = Math.max(...data.map(d => d.amount), 1000); // at least 1000 for scale

  // Chart dimensions
  const height = 180;
  const width = 800; // Simplified scaling
  const barWidth = 60;
  const gap = 40;

  return (
    <div className="trend-chart-container">
      <div className="trend-chart-y-axis">
        <span className="y-label">{new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(maxAmount)}</span>
        <span className="y-label">{new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(maxAmount / 2)}</span>
        <span className="y-label">₹ 0</span>
      </div>
      <div className="trend-chart-main">
        <div className="trend-chart-bars">
          {data.map((item, index) => {
            const barHeight = (item.amount / maxAmount) * height;
            return (
              <div key={index} className="trend-bar-wrapper">
                <div
                  className="trend-bar"
                  style={{
                    height: `${barHeight}px`,
                    animationDelay: `${index * 0.1}s`
                  }}
                  title={`${item.month}: ₹${item.amount.toLocaleString()}`}
                >
                  <span className="trend-bar-value">
                    {item.amount > 0 ? (item.amount > 1000 ? `${(item.amount / 1000).toFixed(1)}k` : item.amount) : ''}
                  </span>
                </div>
                <span className="trend-bar-month">{item.month}</span>
              </div>
            );
          })}
        </div>
        <div className="trend-chart-grid">
          <div className="grid-line" style={{ bottom: '0%' }}></div>
          <div className="grid-line" style={{ bottom: '50%' }}></div>
          <div className="grid-line" style={{ bottom: '100%' }}></div>
        </div>
      </div>
    </div>
  );
};

export default DashboardScreen;
