import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { authService } from '../services/authService';

const ReportsScreen = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [dateRange, setDateRange] = useState({
    from_date: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0], // Jan 1 of current year
    to_date: new Date().toISOString().split('T')[0], // Today
    as_on_date: new Date().toISOString().split('T')[0] // For trial balance
  });

  // Check authentication and backend connectivity on mount
  useEffect(() => {
    const checkAuthAndConnectivity = async () => {
      try {
        const isAuthenticated = await authService.isAuthenticated();
        if (!isAuthenticated) {
          navigate('/login');
          return;
        }
        const user = await authService.getCurrentUser();
        if (!user) {
          navigate('/login');
          return;
        }
        console.log('ReportsScreen: User authenticated:', user.email);
      } catch (error) {
        console.error('ReportsScreen: Auth check failed:', error);
        navigate('/login');
      }
    };
    checkAuthAndConnectivity();
  }, [navigate]);

  const reports = [
    {
      id: 'trial_balance',
      title: 'Trial Balance',
      description: 'Account balances as on a specific date',
      icon: '⚖️',
      color: '#007AFF',
      needsDate: 'as_on_date',
      endpoint: '/reports/trial-balance'
    },
    {
      id: 'general_ledger',
      title: 'General Ledger',
      description: 'Consolidated transaction ledger by account',
      icon: '📊',
      color: '#34C759',
      needsDate: 'date_range',
      endpoint: '/reports/general-ledger'
    },
    {
      id: 'receipts_payments',
      title: 'Receipts & Payments',
      description: 'Cash-based report showing all receipts and payments',
      icon: '💰',
      color: '#FF9500',
      needsDate: 'date_range',
      endpoint: '/reports/receipts-and-payments'
    },
    {
      id: 'income_expenditure',
      title: 'Income & Expenditure',
      description: 'Accrual-based profit & loss statement',
      icon: '📈',
      color: '#5856D6',
      needsDate: 'date_range',
      endpoint: '/reports/income-and-expenditure'
    },
    {
      id: 'balance_sheet',
      title: 'Balance Sheet',
      description: 'Assets, Liabilities and Capital position',
      icon: '📋',
      color: '#AF52DE',
      needsDate: 'date_range',
      endpoint: '/reports/balance-sheet'
    },
    {
      id: 'member_dues',
      title: 'Member Dues Report',
      description: 'Outstanding dues from all members',
      icon: '👥',
      color: '#FF3B30',
      needsDate: 'date_range',
      endpoint: '/reports/member-dues'
    }
  ];

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '₹ 0';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleGenerateReport = async (report) => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    setSelectedReport(report);
    setReportData(null);

    try {
      let response;
      const params = new URLSearchParams();

      // Check authentication before making API call
      const isAuthenticated = await authService.isAuthenticated();
      if (!isAuthenticated) {
        setMessage({ type: 'error', text: 'Session expired. Please login again.' });
        setTimeout(() => navigate('/login'), 2000);
        setLoading(false);
        return;
      }

      // Get full URL for debugging
      const baseURL = api.defaults.baseURL || 'http://localhost:8001/api';
      const fullURL = `${baseURL}${report.endpoint}?${params.toString()}`;
      console.log('ReportsScreen: Full API URL:', fullURL);
      console.log('ReportsScreen: Base URL:', baseURL);
      console.log('ReportsScreen: Endpoint:', report.endpoint);

      if (report.needsDate === 'as_on_date') {
        if (!dateRange.as_on_date) {
          setMessage({ type: 'error', text: 'Please select an "As On Date" for this report' });
          setLoading(false);
          return;
        }
        params.append('as_on_date', dateRange.as_on_date);
        console.log('Generating report:', report.endpoint, 'with params:', params.toString());
        response = await api.get(`${report.endpoint}?${params.toString()}`);
      } else {
        if (!dateRange.from_date || !dateRange.to_date) {
          setMessage({ type: 'error', text: 'Please select both "From Date" and "To Date" for this report' });
          setLoading(false);
          return;
        }
        params.append('from_date', dateRange.from_date);
        params.append('to_date', dateRange.to_date);
        console.log('Generating report:', report.endpoint, 'with params:', params.toString());
        response = await api.get(`${report.endpoint}?${params.toString()}`);
      }

      console.log('Report response:', response.data);
      setReportData(response.data);
      setMessage({ type: 'success', text: `${report.title} generated successfully!` });
    } catch (error) {
      console.error('Error generating report:', error);
      let errorMessage = 'Failed to generate report';
      
      if (error.code === 'CONNECTION_ERROR' || !error.response) {
        errorMessage = 'Cannot connect to server. Please check:\n1. Backend is running\n2. Correct API URL in config';
      } else if (error.response?.status === 401) {
        errorMessage = 'Session expired. Please login again.';
      } else if (error.response?.status === 403) {
        errorMessage = 'You do not have permission to view reports.';
      } else if (error.response?.status === 404) {
        errorMessage = 'Report endpoint not found. Please check the API path.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setMessage({
        type: 'error',
        text: errorMessage
      });
    } finally {
      setLoading(false);
    }
  };

  const renderTrialBalance = (data) => {
    if (!data || !data.accounts) return null;

    return (
      <div style={{ marginTop: '20px' }}>
        <h3 style={{ marginBottom: '15px' }}>Trial Balance as on {dateRange.as_on_date}</h3>
        <div className="settings-table-container">
          <table className="settings-table">
            <thead>
              <tr>
                <th>Account Code</th>
                <th>Account Name</th>
                <th style={{ textAlign: 'right' }}>Debit (₹)</th>
                <th style={{ textAlign: 'right' }}>Credit (₹)</th>
              </tr>
            </thead>
            <tbody>
              {data.accounts.map((account, idx) => (
                <tr key={idx}>
                  <td>{account.account_code}</td>
                  <td>{account.account_name}</td>
                  <td style={{ textAlign: 'right' }}>{formatCurrency(account.debit_balance)}</td>
                  <td style={{ textAlign: 'right' }}>{formatCurrency(account.credit_balance)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr style={{ fontWeight: 'bold', backgroundColor: '#f0f0f0' }}>
                <td colSpan="2">Total</td>
                <td style={{ textAlign: 'right' }}>{formatCurrency(data.total_debit)}</td>
                <td style={{ textAlign: 'right' }}>{formatCurrency(data.total_credit)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    );
  };

  const renderGeneralLedger = (data) => {
    if (!data || !data.accounts) return null;

    return (
      <div style={{ marginTop: '20px' }}>
        <h3 style={{ marginBottom: '15px' }}>
          General Ledger from {dateRange.from_date} to {dateRange.to_date}
        </h3>
        {data.accounts.map((account, idx) => (
          <div key={idx} style={{ marginBottom: '30px', border: '1px solid #ddd', borderRadius: '8px', padding: '15px' }}>
            <h4 style={{ marginTop: 0, color: '#007AFF' }}>
              {account.account_code} - {account.account_name}
            </h4>
            <div style={{ marginBottom: '10px', fontSize: '14px', color: '#666' }}>
              Opening Balance: {formatCurrency(account.opening_balance)} | 
              Closing Balance: {formatCurrency(account.closing_balance)}
            </div>
            {account.entries && account.entries.length > 0 ? (
              <div className="settings-table-container">
                <table className="settings-table" style={{ fontSize: '13px' }}>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Description</th>
                      <th style={{ textAlign: 'right' }}>Debit (₹)</th>
                      <th style={{ textAlign: 'right' }}>Credit (₹)</th>
                      <th style={{ textAlign: 'right' }}>Balance (₹)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {account.entries.map((entry, eIdx) => (
                      <tr key={eIdx}>
                        <td>{new Date(entry.date).toLocaleDateString()}</td>
                        <td>{entry.description || '-'}</td>
                        <td style={{ textAlign: 'right' }}>{formatCurrency(entry.debit_amount)}</td>
                        <td style={{ textAlign: 'right' }}>{formatCurrency(entry.credit_amount)}</td>
                        <td style={{ textAlign: 'right' }}>{formatCurrency(entry.balance)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: '#666', fontStyle: 'italic' }}>No transactions in this period</p>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderReceiptsPayments = (data) => {
    if (!data) return null;

    return (
      <div style={{ marginTop: '20px' }}>
        <h3 style={{ marginBottom: '15px' }}>
          Receipts & Payments from {dateRange.from_date} to {dateRange.to_date}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          <div style={{ padding: '15px', backgroundColor: '#f0f8ff', borderRadius: '8px' }}>
            <h4 style={{ marginTop: 0, color: '#007AFF' }}>Receipts</h4>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007AFF' }}>
              {formatCurrency(data.total_receipts)}
            </div>
          </div>
          <div style={{ padding: '15px', backgroundColor: '#fff0f0', borderRadius: '8px' }}>
            <h4 style={{ marginTop: 0, color: '#FF3B30' }}>Payments</h4>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#FF3B30' }}>
              {formatCurrency(data.total_payments)}
            </div>
          </div>
        </div>
        {data.receipts && data.receipts.length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <h4>Receipts Details</h4>
            <div className="settings-table-container">
              <table className="settings-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th style={{ textAlign: 'right' }}>Amount (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.receipts.map((item, idx) => (
                    <tr key={idx}>
                      <td>{new Date(item.date).toLocaleDateString()}</td>
                      <td>{item.description}</td>
                      <td style={{ textAlign: 'right' }}>{formatCurrency(item.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {data.payments && data.payments.length > 0 && (
          <div>
            <h4>Payments Details</h4>
            <div className="settings-table-container">
              <table className="settings-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th style={{ textAlign: 'right' }}>Amount (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.payments.map((item, idx) => (
                    <tr key={idx}>
                      <td>{new Date(item.date).toLocaleDateString()}</td>
                      <td>{item.description}</td>
                      <td style={{ textAlign: 'right' }}>{formatCurrency(item.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderIncomeExpenditure = (data) => {
    if (!data) return null;

    return (
      <div style={{ marginTop: '20px' }}>
        <h3 style={{ marginBottom: '15px' }}>
          Income & Expenditure from {dateRange.from_date} to {dateRange.to_date}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          <div style={{ padding: '15px', backgroundColor: '#f0f8ff', borderRadius: '8px' }}>
            <h4 style={{ marginTop: 0, color: '#007AFF' }}>Total Income</h4>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007AFF' }}>
              {formatCurrency(data.total_income)}
            </div>
          </div>
          <div style={{ padding: '15px', backgroundColor: '#fff0f0', borderRadius: '8px' }}>
            <h4 style={{ marginTop: 0, color: '#FF3B30' }}>Total Expenditure</h4>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#FF3B30' }}>
              {formatCurrency(data.total_expenditure)}
            </div>
          </div>
        </div>
        <div style={{ padding: '15px', backgroundColor: data.net_income >= 0 ? '#f0fff0' : '#fff0f0', borderRadius: '8px', marginBottom: '20px' }}>
          <h4 style={{ marginTop: 0 }}>Net Income / (Loss)</h4>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: data.net_income >= 0 ? '#34C759' : '#FF3B30' }}>
            {formatCurrency(data.net_income)}
          </div>
        </div>
        {data.income_items && data.income_items.length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <h4>Income Details</h4>
            <div className="settings-table-container">
              <table className="settings-table">
                <thead>
                  <tr>
                    <th>Account</th>
                    <th>Description</th>
                    <th style={{ textAlign: 'right' }}>Amount (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.income_items.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.account_code}</td>
                      <td>{item.account_name}</td>
                      <td style={{ textAlign: 'right' }}>{formatCurrency(item.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {data.expenditure_items && data.expenditure_items.length > 0 && (
          <div>
            <h4>Expenditure Details</h4>
            <div className="settings-table-container">
              <table className="settings-table">
                <thead>
                  <tr>
                    <th>Account</th>
                    <th>Description</th>
                    <th style={{ textAlign: 'right' }}>Amount (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.expenditure_items.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.account_code}</td>
                      <td>{item.account_name}</td>
                      <td style={{ textAlign: 'right' }}>{formatCurrency(item.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderBalanceSheet = (data) => {
    if (!data) return null;

    return (
      <div style={{ marginTop: '20px' }}>
        <h3 style={{ marginBottom: '15px' }}>
          Balance Sheet as on {dateRange.to_date}
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div>
            <h4 style={{ color: '#007AFF', marginBottom: '10px' }}>Assets</h4>
            <div className="settings-table-container">
              <table className="settings-table">
                <thead>
                  <tr>
                    <th>Account</th>
                    <th style={{ textAlign: 'right' }}>Amount (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.assets && data.assets.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.account_name}</td>
                      <td style={{ textAlign: 'right' }}>{formatCurrency(item.balance)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr style={{ fontWeight: 'bold' }}>
                    <td>Total Assets</td>
                    <td style={{ textAlign: 'right' }}>{formatCurrency(data.total_assets)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
          <div>
            <h4 style={{ color: '#FF3B30', marginBottom: '10px' }}>Liabilities & Capital</h4>
            <div className="settings-table-container">
              <table className="settings-table">
                <thead>
                  <tr>
                    <th>Account</th>
                    <th style={{ textAlign: 'right' }}>Amount (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.liabilities && data.liabilities.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.account_name}</td>
                      <td style={{ textAlign: 'right' }}>{formatCurrency(item.balance)}</td>
                    </tr>
                  ))}
                  {data.capital && data.capital.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.account_name}</td>
                      <td style={{ textAlign: 'right' }}>{formatCurrency(item.balance)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr style={{ fontWeight: 'bold' }}>
                    <td>Total Liabilities & Capital</td>
                    <td style={{ textAlign: 'right' }}>{formatCurrency(data.total_liabilities_capital)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMemberDues = (data) => {
    if (!data || !data.members) return null;

    return (
      <div style={{ marginTop: '20px' }}>
        <h3 style={{ marginBottom: '15px' }}>
          Member Dues Report as on {dateRange.to_date}
        </h3>
        <div style={{ marginBottom: '15px', padding: '15px', backgroundColor: '#fff0f0', borderRadius: '8px' }}>
          <strong>Total Outstanding: {formatCurrency(data.total_outstanding)}</strong>
        </div>
        <div className="settings-table-container">
          <table className="settings-table">
            <thead>
              <tr>
                <th>Flat Number</th>
                <th>Member Name</th>
                <th style={{ textAlign: 'right' }}>Outstanding (₹)</th>
                <th>Last Payment</th>
              </tr>
            </thead>
            <tbody>
              {data.members.map((member, idx) => (
                <tr key={idx}>
                  <td><strong>{member.flat_number}</strong></td>
                  <td>{member.owner_name || member.member_name || '-'}</td>
                  <td style={{ textAlign: 'right', color: (member.outstanding_amount || member.outstanding || 0) > 0 ? '#FF3B30' : '#34C759' }}>
                    {formatCurrency(member.outstanding_amount || member.outstanding || 0)}
                  </td>
                  <td>{member.last_payment_date ? new Date(member.last_payment_date).toLocaleDateString() : 'Never'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderReportData = () => {
    if (!selectedReport || !reportData) return null;

    switch (selectedReport.id) {
      case 'trial_balance':
        return renderTrialBalance(reportData);
      case 'general_ledger':
        return renderGeneralLedger(reportData);
      case 'receipts_payments':
        return renderReceiptsPayments(reportData);
      case 'income_expenditure':
        return renderIncomeExpenditure(reportData);
      case 'balance_sheet':
        return renderBalanceSheet(reportData);
      case 'member_dues':
        return renderMemberDues(reportData);
      default:
        return <pre>{JSON.stringify(reportData, null, 2)}</pre>;
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1 className="dashboard-header-title">📊 Reports</h1>
        <div className="dashboard-header-right">
          <button onClick={() => navigate('/dashboard')} className="dashboard-logout-button">
            Back to Dashboard
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {message.text && (
          <div className={`message ${message.type}`} style={{
            marginBottom: '20px',
            padding: '15px',
            borderRadius: '8px',
            backgroundColor: message.type === 'error' ? '#fee' : message.type === 'success' ? '#efe' : '#eef',
            border: `1px solid ${message.type === 'error' ? '#f44' : message.type === 'success' ? '#4f4' : '#44f'}`,
            color: message.type === 'error' ? '#c00' : message.type === 'success' ? '#0c0' : '#00c',
          }}>
            {message.text}
          </div>
        )}

        {/* Date Range Selection */}
        <div className="settings-section" style={{ marginBottom: '30px' }}>
          <h2 className="settings-section-title">Date Range Selection</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
            <div className="settings-form-group">
              <label>From Date</label>
              <input
                type="date"
                value={dateRange.from_date}
                onChange={(e) => setDateRange({ ...dateRange, from_date: e.target.value })}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div className="settings-form-group">
              <label>To Date</label>
              <input
                type="date"
                value={dateRange.to_date}
                onChange={(e) => setDateRange({ ...dateRange, to_date: e.target.value })}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div className="settings-form-group">
              <label>As On Date (for Trial Balance)</label>
              <input
                type="date"
                value={dateRange.as_on_date}
                onChange={(e) => setDateRange({ ...dateRange, as_on_date: e.target.value })}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
          </div>
        </div>

        {/* Reports Grid */}
        <div className="settings-section">
          <h2 className="settings-section-title">Available Reports</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {reports.map((report) => (
              <div
                key={report.id}
                style={{
                  padding: '20px',
                  border: '2px solid #ddd',
                  borderRadius: '8px',
                  backgroundColor: 'white',
                  cursor: 'pointer',
                  transition: 'all 0.3s',
                  boxShadow: selectedReport?.id === report.id ? '0 4px 12px rgba(0,0,0,0.15)' : '0 2px 4px rgba(0,0,0,0.1)'
                }}
                onClick={() => handleGenerateReport(report)}
              >
                <div style={{ fontSize: '32px', marginBottom: '10px' }}>{report.icon}</div>
                <h3 style={{ marginTop: 0, marginBottom: '8px', color: report.color }}>
                  {report.title}
                </h3>
                <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
                  {report.description}
                </p>
                {loading && selectedReport?.id === report.id && (
                  <div style={{ marginTop: '10px', color: report.color }}>
                    Generating...
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Report Results */}
        {reportData && (
          <div className="settings-section" style={{ marginTop: '30px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h2 className="settings-section-title" style={{ margin: 0 }}>
                {selectedReport?.title} Report
              </h2>
              <button
                onClick={() => {
                  setReportData(null);
                  setSelectedReport(null);
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#ccc',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Close Report
              </button>
            </div>
            {renderReportData()}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportsScreen;
