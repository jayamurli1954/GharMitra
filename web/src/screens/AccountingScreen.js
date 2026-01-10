/**
 * GharMitra Accounting Screen
 * Complete accounting system with Chart of Accounts, Quick Entry, Journal Voucher, and Reports
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import accountingService from '../services/accountingService';
import journalService from '../services/journalService';
import transactionsService from '../services/transactionsService';
import flatsService from '../services/flatsService';

// Helper function to safely extract error message from API errors
const getErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    if (Array.isArray(detail)) {
      // Pydantic validation errors - extract messages
      return detail.map(err => {
        if (typeof err === 'string') return err;
        if (typeof err === 'object' && err.msg) return err.msg;
        if (typeof err === 'object' && err.message) return err.message;
        return JSON.stringify(err);
      }).join(', ');
    } else if (typeof detail === 'string') {
      return detail;
    } else if (typeof detail === 'object') {
      return detail.msg || detail.message || 'Validation error occurred';
    }
  }
  if (error.message) {
    return error.message;
  }
  return 'An error occurred. Please try again.';
};

// Helper function to format current month/year as "January, 2026"
const getCurrentMonthYear = () => {
  const now = new Date();
  const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  return `${monthNames[now.getMonth()]}, ${now.getFullYear()}`;
};

const AccountingScreen = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('chart-of-accounts');
  const [loading, setLoading] = useState(false);

  const accountingTabs = [
    { id: 'chart-of-accounts', label: '📊 Chart of Accounts', icon: '📊' },
    { id: 'quick-entry', label: '⚡ Quick Entry', icon: '⚡' },
    { id: 'journal-voucher', label: '📝 Journal Voucher', icon: '📝' },
    { id: 'reports', label: '📈 Reports', icon: '📈' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'chart-of-accounts':
        return <ChartOfAccountsTab />;
      case 'quick-entry':
        return <QuickEntryTab />;
      case 'journal-voucher':
        return <JournalVoucherTab />;
      case 'reports':
        return <ReportsTab />;
      default:
        return <ChartOfAccountsTab />;
    }
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div className="dashboard-header-left">
          <h1 className="dashboard-header-title">💰 Accounting</h1>
          <span className="dashboard-header-subtitle">Financial Management System</span>
        </div>
        <div className="dashboard-header-right">
          <button onClick={() => navigate('/dashboard')} className="dashboard-logout-button">
            ← Back to Dashboard
          </button>
        </div>
      </div>

      <div className="settings-container">
        {/* Sidebar Navigation */}
        <div className="settings-sidebar">
          <div className="settings-sidebar-header">
            <h3>Accounting Menu</h3>
          </div>
          <nav className="settings-nav">
            {accountingTabs.map((tab) => (
              <button
                key={tab.id}
                className={`settings-nav-item ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="settings-nav-icon">{tab.icon}</span>
                <span className="settings-nav-label">{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Main Content Area */}
        <div className="settings-content">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

// Chart of Accounts Tab
const ChartOfAccountsTab = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [editingAccount, setEditingAccount] = useState(null);
  const [editingName, setEditingName] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAccount, setNewAccount] = useState({
    code: '',
    name: '',
    type: 'asset',
    description: '',
    opening_balance: 0
  });

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const accountsList = await accountingService.getAccounts();
      setAccounts(accountsList || []);
      // Clear any previous error messages if successful
      if (accountsList && accountsList.length > 0) {
        setMessage({ type: '', text: '' });
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
      let errorMsg = 'Failed to load accounts. Please try again.';

      if (error.response) {
        // Server responded with error status
        if (error.response.status === 401) {
          errorMsg = 'Authentication required. Please login again.';
        } else if (error.response.status === 403) {
          errorMsg = 'You do not have permission to view accounts.';
        } else if (error.response.status === 404) {
          errorMsg = 'Accounts endpoint not found. Please check backend configuration.';
        } else {
          errorMsg = getErrorMessage(error) || errorMsg;
        }
      } else {
        errorMsg = getErrorMessage(error) || errorMsg;
      }

      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleInitialize = async () => {
    if (!window.confirm('This will initialize the chart of accounts with predefined accounts. Continue?')) {
      return;
    }

    setSaving(true);
    setMessage({ type: '', text: '' });
    try {
      const result = await accountingService.initializeChartOfAccounts();
      setMessage({ type: 'success', text: `Chart of accounts initialized successfully! ${result.accounts_created} accounts created.` });
      setTimeout(() => setMessage({ type: '', text: '' }), 5000);
      await loadAccounts();
    } catch (error) {
      console.error('Error initializing accounts:', error);
      const errorMsg = getErrorMessage(error) || 'Failed to initialize chart of accounts.';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setSaving(false);
    }
  };

  const handleEditName = (account) => {
    setEditingAccount(account.code);
    setEditingName(account.name);
  };

  const handleSaveName = async (code) => {
    if (!editingName.trim()) {
      setMessage({ type: 'error', text: 'Account name cannot be empty.' });
      return;
    }

    setSaving(true);
    try {
      await accountingService.updateAccount(code, { name: editingName });
      setMessage({ type: 'success', text: 'Account name updated successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      setEditingAccount(null);
      await loadAccounts();
    } catch (error) {
      console.error('Error updating account:', error);
      const errorMsg = getErrorMessage(error) || 'Failed to update account name.';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditingAccount(null);
    setEditingName('');
  };

  const handleAddAccount = async (e) => {
    e.preventDefault();

    // Validation
    if (!newAccount.code.trim()) {
      setMessage({ type: 'error', text: 'Account code is required.' });
      return;
    }
    if (!newAccount.name.trim()) {
      setMessage({ type: 'error', text: 'Account name is required.' });
      return;
    }
    if (!newAccount.type) {
      setMessage({ type: 'error', text: 'Account type is required.' });
      return;
    }

    // Validate code format (should be numeric, 4-10 digits)
    if (!/^\d{4,10}$/.test(newAccount.code.trim())) {
      setMessage({ type: 'error', text: 'Account code must be 4-10 digits (e.g., 1000, 1010, 5001).' });
      return;
    }

    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      await accountingService.createAccount({
        code: newAccount.code.trim(),
        name: newAccount.name.trim(),
        type: newAccount.type,
        description: newAccount.description.trim() || null,
        opening_balance: parseFloat(newAccount.opening_balance) || 0
      });

      setMessage({ type: 'success', text: 'Account created successfully!' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);

      // Reset form
      setNewAccount({
        code: '',
        name: '',
        type: 'asset',
        description: '',
        opening_balance: 0
      });
      setShowAddForm(false);

      // Reload accounts
      await loadAccounts();
    } catch (error) {
      console.error('Error creating account:', error);
      let errorMsg = 'Failed to create account. Please try again.';

      if (error.response) {
        if (error.response.status === 400) {
          errorMsg = getErrorMessage(error) || 'Invalid account data. Account code may already exist.';
        } else if (error.response.status === 401) {
          errorMsg = 'Authentication required. Please login again.';
        } else if (error.response.status === 403) {
          errorMsg = 'You do not have permission to create accounts.';
        } else {
          errorMsg = getErrorMessage(error) || errorMsg;
        }
      } else {
        errorMsg = getErrorMessage(error) || errorMsg;
      }

      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setSaving(false);
    }
  };

  // Filter accounts
  const filteredAccounts = accounts.filter(account => {
    const matchesSearch = !searchTerm ||
      account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      account.code.includes(searchTerm);
    const matchesType = !filterType || account.type.toLowerCase() === filterType.toLowerCase();
    return matchesSearch && matchesType;
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // TODO: API call to create account
      console.log('Creating account:', formData);
      setShowAddForm(false);
      setFormData({ code: '', name: '', type: 'Asset', parent_code: '', opening_balance: 0 });
      loadAccounts();
    } catch (error) {
      console.error('Error creating account:', error);
    }
  };

  const accountTypes = ['asset', 'liability', 'capital', 'income', 'expense'];

  if (loading) {
    return (
      <div className="settings-tab-content">
        <h2 className="settings-tab-title">📊 Chart of Accounts</h2>
        <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
          Loading chart of accounts...
        </div>
      </div>
    );
  }

  return (
    <div className="settings-tab-content">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 className="settings-tab-title">📊 Chart of Accounts</h2>
          <p className="settings-tab-description">Manage your accounting chart of accounts. Account names are editable, codes are read-only.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="settings-add-btn"
            onClick={() => setShowAddForm(!showAddForm)}
            disabled={saving}
          >
            {showAddForm ? '✕ Cancel' : '+ Add Account'}
          </button>
          {accounts.length === 0 && (
            <button
              className="settings-add-btn"
              onClick={handleInitialize}
              disabled={saving}
              style={{ backgroundColor: '#4CAF50' }}
            >
              {saving ? 'Initializing...' : '📥 Initialize Chart of Accounts'}
            </button>
          )}
        </div>
      </div>

      {/* Success/Error Message */}
      {message.text && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '20px',
          backgroundColor: message.type === 'success' ? '#E8F5E9' : '#FFEBEE',
          color: message.type === 'success' ? '#2E7D32' : '#C62828',
          border: `1px solid ${message.type === 'success' ? '#4CAF50' : '#EF5350'}`,
        }}>
          {message.text}
        </div>
      )}

      {/* Add Account Form */}
      {showAddForm && (
        <div className="settings-section" style={{ marginBottom: '20px', backgroundColor: '#f9f9f9', padding: '20px', borderRadius: '8px' }}>
          <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Add New Account</h3>
          <form className="settings-form" onSubmit={handleAddAccount}>
            <div className="settings-form-row">
              <div className="settings-form-group">
                <label>Account Code *</label>
                <input
                  type="text"
                  value={newAccount.code}
                  onChange={(e) => setNewAccount({ ...newAccount, code: e.target.value })}
                  placeholder="e.g., 1000, 1010, 5001"
                  required
                  pattern="[0-9]{4,10}"
                  title="Account code must be 4-10 digits"
                  disabled={saving}
                />
                <small style={{ color: '#666', fontSize: '12px' }}>
                  Must be 4-10 digits. Follow standard ranges: 1000-1999 (Assets), 2000-2999 (Liabilities), 3000-3999 (Capital), 4000-4999 (Income), 5000-5999 (Expenses)
                </small>
              </div>
              <div className="settings-form-group">
                <label>Account Name *</label>
                <input
                  type="text"
                  value={newAccount.name}
                  onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })}
                  placeholder="e.g., Cash in Hand, Bank Account, etc."
                  required
                  disabled={saving}
                />
              </div>
              <div className="settings-form-group">
                <label>Account Type *</label>
                <select
                  value={newAccount.type}
                  onChange={(e) => setNewAccount({ ...newAccount, type: e.target.value })}
                  required
                  disabled={saving}
                >
                  <option value="asset">Asset</option>
                  <option value="liability">Liability</option>
                  <option value="capital">Capital/Equity</option>
                  <option value="income">Income</option>
                  <option value="expense">Expense</option>
                </select>
              </div>
            </div>
            <div className="settings-form-row">
              <div className="settings-form-group" style={{ flex: 2 }}>
                <label>Description (Optional)</label>
                <textarea
                  value={newAccount.description}
                  onChange={(e) => setNewAccount({ ...newAccount, description: e.target.value })}
                  placeholder="Brief description of the account..."
                  rows="2"
                  disabled={saving}
                />
              </div>
              <div className="settings-form-group">
                <label>Opening Balance (₹)</label>
                <input
                  type="number"
                  value={newAccount.opening_balance}
                  onChange={(e) => setNewAccount({ ...newAccount, opening_balance: e.target.value })}
                  step="0.01"
                  placeholder="0.00"
                  disabled={saving}
                />
              </div>
            </div>
            <div className="settings-form-actions">
              <button type="submit" className="settings-save-btn" disabled={saving}>
                {saving ? 'Creating...' : 'Create Account'}
              </button>
              <button
                type="button"
                className="settings-cancel-btn"
                onClick={() => {
                  setShowAddForm(false);
                  setNewAccount({
                    code: '',
                    name: '',
                    type: 'asset',
                    description: '',
                    opening_balance: 0
                  });
                }}
                disabled={saving}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {accounts.length === 0 ? (
        <div className="settings-section" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <h3 style={{ color: '#666', marginBottom: '20px' }}>No accounts found</h3>
          <p style={{ color: '#999', marginBottom: '30px' }}>
            Click "Initialize Chart of Accounts" to load the predefined chart of accounts with proper account codes.
          </p>
        </div>
      ) : (
        <div className="settings-section">
          <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
            <input
              type="text"
              placeholder="Search by code or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ flex: 1, padding: '10px', border: '2px solid #e0e0e0', borderRadius: '8px' }}
            />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              style={{ padding: '10px', border: '2px solid #e0e0e0', borderRadius: '8px' }}
            >
              <option value="">All Types</option>
              {accountTypes.map(type => (
                <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
              ))}
            </select>
          </div>

          <div className="settings-table-container">
            <table className="settings-table">
              <thead>
                <tr>
                  <th style={{ width: '100px' }}>Code</th>
                  <th>Account Name</th>
                  <th style={{ width: '120px' }}>Type</th>
                  <th style={{ width: '150px' }}>Balance (₹)</th>
                  <th style={{ width: '120px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAccounts.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                      No accounts found matching your search.
                    </td>
                  </tr>
                ) : (
                  filteredAccounts.map((account) => (
                    <tr key={account.code}>
                      <td>
                        <strong style={{ color: '#666' }}>{account.code}</strong>
                      </td>
                      <td>
                        {editingAccount === account.code ? (
                          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <input
                              type="text"
                              value={editingName}
                              onChange={(e) => setEditingName(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleSaveName(account.code);
                                if (e.key === 'Escape') handleCancelEdit();
                              }}
                              style={{ flex: 1, padding: '6px', border: '2px solid #4CAF50', borderRadius: '4px' }}
                              autoFocus
                            />
                            <button
                              onClick={() => handleSaveName(account.code)}
                              disabled={saving}
                              style={{ padding: '6px 12px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                            >
                              ✓
                            </button>
                            <button
                              onClick={handleCancelEdit}
                              style={{ padding: '6px 12px', backgroundColor: '#999', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <span>{account.name}</span>
                        )}
                      </td>
                      <td>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '600',
                          background: account.type === 'asset' ? '#E8F5E9' :
                            account.type === 'liability' ? '#FFEBEE' :
                              account.type === 'income' ? '#E3F2FD' :
                                account.type === 'capital' ? '#F3E5F5' : '#FFF3E0',
                          color: account.type === 'asset' ? '#2E7D32' :
                            account.type === 'liability' ? '#C62828' :
                              account.type === 'income' ? '#1565C0' :
                                account.type === 'capital' ? '#7B1FA2' : '#E65100'
                        }}>
                          {account.type.charAt(0).toUpperCase() + account.type.slice(1)}
                        </span>
                      </td>
                      <td style={{ fontWeight: '600', color: (account.current_balance || 0) >= 0 ? '#2E7D32' : '#C62828' }}>
                        {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(account.current_balance || 0)}
                      </td>
                      <td>
                        {editingAccount !== account.code && (
                          <button
                            className="settings-action-btn"
                            onClick={() => handleEditName(account)}
                            disabled={saving}
                          >
                            Edit Name
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: '15px', color: '#666', fontSize: '14px' }}>
            Showing {filteredAccounts.length} of {accounts.length} accounts
          </div>
        </div>
      )}
    </div>
  );
};

// Quick Entry Tab
const QuickEntryTab = () => {
  const [entryType, setEntryType] = useState('income');
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    expense_for_month: getCurrentMonthYear(),
    account: '',
    amount: '',
    description: '',
    payment_mode: 'cash',
    reference: '',
  });
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [transactions, setTransactions] = useState([]);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [editingTransaction, setEditingTransaction] = useState(null);
  const [editFormData, setEditFormData] = useState({
    date: '',
    expense_for_month: '',
    account: '',
    amount: '',
    description: '',
    payment_mode: 'cash',
    reference: '',
  });

  useEffect(() => {
    loadAccounts();
    loadRecentTransactions();
  }, [entryType]);

  const loadRecentTransactions = async () => {
    try {
      const data = await transactionsService.getTransactions({ limit: 10 });
      setTransactions(data || []);
    } catch (error) {
      console.error('Error loading transactions:', error);
    }
  };

  const loadAccounts = async () => {
    try {
      const typeMap = {
        'income': 'income',
        'expense': 'expense',
        'transfer': null
      };
      const accountsList = await accountingService.getAccounts(typeMap[entryType]);
      setAccounts(accountsList || []);
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  };

  const handleEditTxn = async (txn) => {
    try {
      // Load full transaction details
      const fullTxn = await transactionsService.getTransaction(txn.id);
      
      // Set entry type based on transaction type
      const txnType = fullTxn.type || 'expense';
      setEntryType(txnType);
      
      // Load accounts for this transaction type
      const typeMap = {
        'income': 'income',
        'expense': 'expense',
        'transfer': null
      };
      const accountsList = await accountingService.getAccounts(typeMap[txnType]);
      setAccounts(accountsList || []);
      
      setEditingTransaction(txn.id);
      setEditFormData({
        date: fullTxn.date,
        expense_for_month: fullTxn.expense_month || getCurrentMonthYear(),
        account: fullTxn.account_code || '',
        amount: fullTxn.amount?.toString() || '',
        description: fullTxn.description || '',
        payment_mode: fullTxn.payment_method === 'bank' ? 'bank' : 'cash',
        reference: fullTxn.document_number || '',
      });
      setMessage({ type: '', text: '' });
    } catch (error) {
      console.error('Error loading transaction for edit:', error);
      const errorMsg = getErrorMessage(error) || 'Failed to load transaction details for editing.';
      setMessage({ type: 'error', text: errorMsg });
    }
  };

  const handleCancelEdit = (clearMessage = true) => {
    setEditingTransaction(null);
    setEditFormData({
      date: '',
      expense_for_month: '',
      account: '',
      amount: '',
      description: '',
      payment_mode: 'cash',
      reference: '',
    });
    if (clearMessage) {
      setMessage({ type: '', text: '' });
    }
  };

  const handleUpdateTxn = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const payload = {};
      
      // Only include fields that have actual values (not empty strings)
      if (editFormData.date && editFormData.date.trim()) {
        payload.date = editFormData.date;
      }
      if (editFormData.account && editFormData.account.trim()) {
        payload.account_code = editFormData.account;
      }
      if (editFormData.amount && !isNaN(parseFloat(editFormData.amount))) {
        payload.amount = parseFloat(editFormData.amount);
      }
      if (editFormData.description && editFormData.description.trim()) {
        payload.description = editFormData.description;
      }
      if (editFormData.account.startsWith('5') && editFormData.expense_for_month && editFormData.expense_for_month.trim()) {
        payload.expense_month = editFormData.expense_for_month;
      }
      if (editFormData.payment_mode) {
        payload.payment_method = editFormData.payment_mode === 'cash' ? 'cash' : 'bank';
      }
      if (editFormData.reference && editFormData.reference.trim()) {
        payload.document_number = editFormData.reference;
      }

      await transactionsService.updateTransaction(editingTransaction, payload);
      loadRecentTransactions();
      
      // Show success message and close edit form after a short delay
      setMessage({ type: 'success', text: 'Transaction updated successfully!' });
      
      // Delay canceling edit to show success message (don't clear message)
      setTimeout(() => {
        handleCancelEdit(false); // Don't clear message when canceling after success
      }, 2000);
    } catch (error) {
      console.error('Error updating transaction:', error);
      const errorMsg = getErrorMessage(error) || 'Failed to update transaction. Please try again.';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleReverseTxn = async (txn) => {
    if (!window.confirm(`Are you sure you want to REVERSE this transaction (${txn.document_number})?`)) {
      return;
    }
    setLoading(true);
    try {
      await transactionsService.reverseTransaction(txn.id);
      setMessage({ type: 'success', text: `Transaction reversed successfully!` });
      loadRecentTransactions();
    } catch (error) {
      console.error('Error reversing transaction:', error);
      const errorMsg = getErrorMessage(error) || 'Failed to reverse transaction.';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const entryTypes = [
    { id: 'income', label: '💰 Income', icon: '💰' },
    { id: 'expense', label: '💸 Expense', icon: '💸' },
    { id: 'transfer', label: '🔄 Transfer', icon: '🔄' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate flat_id if account 1100 is selected
    if (formData.account === '1100' && !formData.flat_id) {
      setMessage({ type: 'error', text: 'Flat selection is required when account 1100 (Maintenance Dues Receivable) is selected.' });
      return;
    }
    
    setLoading(true);
    try {
      const selectedFlat = flats.find(f => f.id === parseInt(formData.flat_id));
      let description = formData.description;
      
      // Add flat info to description if 1100 is selected
      if (formData.account === '1100' && selectedFlat) {
        description = `${formData.description} - Flat: ${selectedFlat.flat_number}`;
      }
      
      const payload = {
        type: entryType,
        category: accounts.find(a => a.code === formData.account)?.name || 'General',
        account_code: formData.account,
        amount: parseFloat(formData.amount),
        description: description,
        date: formData.date,
        expense_month: formData.account.startsWith('5') ? formData.expense_for_month : null,
        payment_method: formData.payment_mode === 'cash' ? 'cash' : 'bank',
        bank_account_code: formData.payment_mode === 'bank' ? null : null,
        document_number: formData.reference || null
      };

      await transactionsService.createTransaction(payload);
      setMessage({ type: 'success', text: 'Entry created successfully!' });
      loadRecentTransactions();
      setFormData({
        date: new Date().toISOString().split('T')[0],
        expense_for_month: getCurrentMonthYear(),
        account: '',
        amount: '',
        description: '',
        payment_mode: 'cash',
        reference: '',
        flat_id: '',
      });
      setAccountSearch('');
    } catch (error) {
      console.error('Error creating entry:', error);
      const errorMsg = getErrorMessage(error) || 'Error creating entry. Please try again.';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings-tab-content">
      <h2 className="settings-tab-title">⚡ Quick Entry</h2>
      <p className="settings-tab-description">Quickly record income, expenses, or transfers</p>

      {/* Success/Error Message */}
      {message.text && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '20px',
          backgroundColor: message.type === 'success' ? '#E8F5E9' : '#FFEBEE',
          color: message.type === 'success' ? '#2E7D32' : '#C62828',
          border: `1px solid ${message.type === 'success' ? '#4CAF50' : '#EF5350'}`,
        }}>
          {message.text}
        </div>
      )}

      <div className="settings-section">
        <h3>Entry Type</h3>
        <div style={{ display: 'flex', gap: '15px', marginBottom: '20px' }}>
          {entryTypes.map((type) => (
            <button
              key={type.id}
              onClick={() => setEntryType(type.id)}
              style={{
                flex: 1,
                padding: '15px',
                border: `3px solid ${entryType === type.id ? 'var(--gm-orange)' : '#e0e0e0'}`,
                borderRadius: '12px',
                background: entryType === type.id ? 'var(--gm-bg-light)' : 'white',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: entryType === type.id ? '600' : '400',
                transition: 'all 0.2s'
              }}
            >
              <span style={{ fontSize: '24px', display: 'block', marginBottom: '5px' }}>{type.icon}</span>
              {type.label}
            </button>
          ))}
        </div>

        <form className="settings-form" onSubmit={handleSubmit}>
          <div className="settings-form-row">
            <div className="settings-form-group">
              <label>Date *</label>
              <input
                type="date"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
              />
            </div>
            {formData.account.startsWith('5') && (
              <div className="settings-form-group">
                <label>Expense For Month *</label>
                <input
                  type="text"
                  value={formData.expense_for_month}
                  onChange={(e) => setFormData({ ...formData, expense_for_month: e.target.value })}
                  placeholder="January, 2026"
                  required
                />
              </div>
            )}
          </div>

          <div className="settings-form-row">
            <div className="settings-form-group" style={{ position: 'relative' }}>
              <label>Account *</label>
              <input
                type="text"
                value={accountSearch || (formData.account ? `${formData.account} - ${accounts.find(a => a.code === formData.account)?.name || ''}` : '')}
                onChange={(e) => {
                  const value = e.target.value;
                  setAccountSearch(value);
                  setShowAccountDropdown(true);
                  // If user types account code directly, try to match
                  const match = accounts.find(acc => acc.code === value || `${acc.code} - ${acc.name}` === value);
                  if (match) {
                    setFormData({ ...formData, account: match.code });
                    setAccountSearch('');
                    setShowAccountDropdown(false);
                  }
                }}
                onFocus={() => setShowAccountDropdown(true)}
                onBlur={() => setTimeout(() => setShowAccountDropdown(false), 200)}
                placeholder="Type account code or name to search..."
                required
                style={{ width: '100%' }}
              />
              {showAccountDropdown && filteredAccounts.length > 0 && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  backgroundColor: 'white',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  maxHeight: '200px',
                  overflowY: 'auto',
                  zIndex: 1000,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  {filteredAccounts.map(acc => (
                    <div
                      key={acc.code}
                      onClick={() => {
                        setFormData({ ...formData, account: acc.code });
                        setAccountSearch('');
                        setShowAccountDropdown(false);
                      }}
                      style={{
                        padding: '10px',
                        cursor: 'pointer',
                        borderBottom: '1px solid #eee'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = '#f5f5f5'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                    >
                      <strong>{acc.code}</strong> - {acc.name}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {formData.account === '1100' && (
            <div className="settings-form-row">
              <div className="settings-form-group">
                <label>Flat * (Required for 1100 - Maintenance Dues Receivable)</label>
                <select
                  value={formData.flat_id}
                  onChange={(e) => setFormData({ ...formData, flat_id: e.target.value })}
                  required
                >
                  <option value="">Select Flat</option>
                  {flats.map(flat => (
                    <option key={flat.id} value={flat.id}>
                      {flat.flat_number} - {flat.owner_name || 'N/A'}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <div className="settings-form-row">
            <div className="settings-form-group">
              <label>Amount (₹) *</label>
              <input
                type="number"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                step="0.01"
                placeholder="0.00"
                required
              />
            </div>
            <div className="settings-form-group">
              <label>Payment Mode *</label>
              <select
                value={formData.payment_mode}
                onChange={(e) => setFormData({ ...formData, payment_mode: e.target.value })}
                required
              >
                <option value="cash">Cash</option>
                <option value="bank">Bank Transfer</option>
                <option value="cheque">Cheque</option>
                <option value="online">Online Payment</option>
              </select>
            </div>
          </div>

          {entryType === 'transfer' && (
            <div className="settings-form-group">
              <label>To Account *</label>
              <select required>
                <option value="">Select Account</option>
                <option value="1001">1001 - Cash</option>
                <option value="1002">1002 - Bank - HDFC</option>
              </select>
            </div>
          )}

          <div className="settings-form-group">
            <label>Description *</label>
            <textarea
              rows="3"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Enter description..."
              required
            />
          </div>

          <div className="settings-form-group">
            <label>Reference Number (Optional)</label>
            <input
              type="text"
              value={formData.reference}
              onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
              placeholder="Cheque number, transaction ID, etc"
            />
          </div>

          <div className="settings-form-actions">
            <button type="submit" className="settings-save-btn" disabled={loading}>
              {loading ? 'Saving...' : 'Save Entry'}
            </button>
            <button type="button" className="settings-cancel-btn" onClick={() => setFormData({
              date: new Date().toISOString().split('T')[0],
              expense_for_month: getCurrentMonthYear(),
              account: '',
              amount: '',
              description: '',
              payment_mode: 'cash',
              reference: '',
            })} disabled={loading}>
              Clear
            </button>
          </div>
        </form>
      </div>

      {/* Edit Transaction Modal/Form */}
      {editingTransaction && (
        <div className="settings-section" style={{ marginTop: '30px', marginBottom: '30px', backgroundColor: '#f9f9f9', padding: '20px', borderRadius: '8px', border: '2px solid var(--gm-orange)' }}>
          <h3 style={{ marginTop: 0 }}>Edit Transaction</h3>
          <form className="settings-form" onSubmit={handleUpdateTxn}>
            <div className="settings-form-row">
              <div className="settings-form-group">
                <label>Date *</label>
                <input
                  type="date"
                  value={editFormData.date}
                  onChange={(e) => setEditFormData({ ...editFormData, date: e.target.value })}
                  required
                  disabled={loading}
                />
              </div>
              {editFormData.account.startsWith('5') && (
                <div className="settings-form-group">
                  <label>Expense For Month *</label>
                  <input
                    type="text"
                    value={editFormData.expense_for_month}
                    onChange={(e) => setEditFormData({ ...editFormData, expense_for_month: e.target.value })}
                    placeholder="December, 2025"
                    required
                    disabled={loading}
                  />
                  <small style={{ color: '#666', fontSize: '12px' }}>
                    Format: Month, Year (e.g., December, 2025)
                  </small>
                </div>
              )}
            </div>

            <div className="settings-form-row">
              <div className="settings-form-group">
                <label>Account *</label>
                <select
                  value={editFormData.account}
                  onChange={(e) => setEditFormData({ ...editFormData, account: e.target.value })}
                  required
                  disabled={loading}
                >
                  <option value="">Select Account</option>
                  {accounts.map(acc => (
                    <option key={acc.code} value={acc.code}>
                      {acc.code} - {acc.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="settings-form-row">
              <div className="settings-form-group">
                <label>Amount (₹) *</label>
                <input
                  type="number"
                  value={editFormData.amount}
                  onChange={(e) => setEditFormData({ ...editFormData, amount: e.target.value })}
                  step="0.01"
                  placeholder="0.00"
                  required
                  disabled={loading}
                />
              </div>
              <div className="settings-form-group">
                <label>Payment Mode *</label>
                <select
                  value={editFormData.payment_mode}
                  onChange={(e) => setEditFormData({ ...editFormData, payment_mode: e.target.value })}
                  required
                  disabled={loading}
                >
                  <option value="cash">Cash</option>
                  <option value="bank">Bank Transfer</option>
                  <option value="cheque">Cheque</option>
                  <option value="online">Online Payment</option>
                </select>
              </div>
            </div>

            <div className="settings-form-group">
              <label>Description *</label>
              <textarea
                rows="3"
                value={editFormData.description}
                onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                placeholder="Enter description..."
                required
                disabled={loading}
              />
            </div>

            <div className="settings-form-group">
              <label>Reference Number (Optional)</label>
              <input
                type="text"
                value={editFormData.reference}
                onChange={(e) => setEditFormData({ ...editFormData, reference: e.target.value })}
                placeholder="Cheque number, transaction ID, etc"
                disabled={loading}
              />
            </div>

            <div className="settings-form-actions">
              <button type="submit" className="settings-save-btn" disabled={loading}>
                {loading ? 'Updating...' : 'Update Transaction'}
              </button>
              <button type="button" className="settings-cancel-btn" onClick={handleCancelEdit} disabled={loading}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="settings-section" style={{ marginTop: '30px' }}>
        <h3>Recent Transactions</h3>
        <div className="settings-table-container">
          <table className="settings-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Voucher #</th>
                <th>Category / Account</th>
                <th>Description</th>
                <th style={{ textAlign: 'right' }}>Amount</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '20px', color: '#999' }}>No recent transactions found</td>
                </tr>
              ) : (
                transactions.map((txn) => (
                  <tr key={txn.id}>
                    <td>{txn.date}</td>
                    <td>{txn.document_number}</td>
                    <td>
                      <div><strong>{txn.type.toUpperCase()}</strong></div>
                      <div style={{ fontSize: '11px', color: '#666' }}>{txn.account_code} - {txn.category}</div>
                    </td>
                    <td>{txn.description}</td>
                    <td style={{ textAlign: 'right', fontWeight: 'bold' }}>
                      ₹{txn.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          className="settings-action-btn"
                          onClick={() => handleEditTxn(txn)}
                          disabled={loading}
                        >
                          Edit
                        </button>
                        <button
                          className="settings-action-btn danger"
                          onClick={() => handleReverseTxn(txn)}
                          disabled={loading}
                        >
                          Reverse
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Journal Voucher Tab
const JournalVoucherTab = () => {
  const [vouchers, setVouchers] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [showForm, setShowForm] = useState(false);
  const [editingVoucher, setEditingVoucher] = useState(null);
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    expense_for_month: getCurrentMonthYear(),
    description: '',
    entries: [
      { account_code: '', debit_amount: '', credit_amount: '', description: '' },
      { account_code: '', debit_amount: '', credit_amount: '', description: '' },
    ],
  });

  useEffect(() => {
    loadAccounts();
    loadFlats();
    loadVouchers();
  }, []);

  const loadFlats = async () => {
    try {
      const flatsList = await flatsService.getFlats();
      setFlats(flatsList || []);
    } catch (error) {
      console.error('Error loading flats:', error);
    }
  };

  const loadAccounts = async () => {
    try {
      const accountsList = await accountingService.getAccounts();
      setAccounts(accountsList || []);
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  };

  const loadVouchers = async () => {
    setLoading(true);
    try {
      const vouchersList = await journalService.getJournalEntries();
      setVouchers(vouchersList || []);
    } catch (error) {
      console.error('Error loading vouchers:', error);
      setMessage({ type: 'error', text: 'Failed to load journal vouchers. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async (voucher) => {
    try {
      // Load full voucher details
      const fullVoucher = await journalService.getJournalEntry(voucher.id);

      setEditingVoucher(voucher.id);
      setFormData({
        date: fullVoucher.date,
        expense_for_month: fullVoucher.expense_month || getCurrentMonthYear(),
        description: fullVoucher.description || '',
        entries: fullVoucher.entries.map(entry => ({
          account_code: entry.account_code,
          debit_amount: entry.debit_amount > 0 ? entry.debit_amount.toString() : '',
          credit_amount: entry.credit_amount > 0 ? entry.credit_amount.toString() : '',
          description: entry.description || ''
        }))
      });
      setShowForm(true);
      setMessage({ type: '', text: '' });
    } catch (error) {
      console.error('Error loading voucher for edit:', error);
      setMessage({ type: 'error', text: 'Failed to load voucher details for editing.' });
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingVoucher(null);
      setFormData({
        date: new Date().toISOString().split('T')[0],
        expense_for_month: getCurrentMonthYear(),
        description: '',
        entries: [
          { account_code: '', debit_amount: '', credit_amount: '', description: '', flat_id: '' },
          { account_code: '', debit_amount: '', credit_amount: '', description: '', flat_id: '' },
        ],
      });
      setAccountSearches({});
    setMessage({ type: '', text: '' });
  };

  const addEntry = () => {
    setFormData({
      ...formData,
      entries: [...formData.entries, { account_code: '', debit_amount: '', credit_amount: '', description: '', flat_id: '' }],
    });
  };

  const removeEntry = (index) => {
    if (formData.entries.length > 2) {
      setFormData({
        ...formData,
        entries: formData.entries.filter((_, i) => i !== index),
      });
    }
  };

  const calculateTotal = () => {
    const totalDebit = formData.entries.reduce((sum, entry) => sum + (parseFloat(entry.debit_amount) || 0), 0);
    const totalCredit = formData.entries.reduce((sum, entry) => sum + (parseFloat(entry.credit_amount) || 0), 0);
    return { totalDebit, totalCredit, balanced: totalDebit === totalCredit && totalDebit > 0 };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { balanced } = calculateTotal();
    if (!balanced) {
      setMessage({ type: 'error', text: 'Debit and Credit totals must be equal and greater than zero!' });
      return;
    }

    // Validate entries
    if (formData.entries.length < 2) {
      setMessage({ type: 'error', text: 'At least 2 entries are required (one debit, one credit).' });
      return;
    }

    // Validate each entry has account and either debit or credit
    for (let i = 0; i < formData.entries.length; i++) {
      const entry = formData.entries[i];
      if (!entry.account_code) {
        setMessage({ type: 'error', text: `Entry ${i + 1}: Account is required.` });
        return;
      }
      // Validate flat_id if account 1100 is selected
      if (entry.account_code === '1100' && !entry.flat_id) {
        setMessage({ type: 'error', text: `Entry ${i + 1}: Flat selection is required when account 1100 (Maintenance Dues Receivable) is selected.` });
        return;
      }
      const hasDebit = parseFloat(entry.debit_amount) > 0;
      const hasCredit = parseFloat(entry.credit_amount) > 0;
      if (!hasDebit && !hasCredit) {
        setMessage({ type: 'error', text: `Entry ${i + 1}: Either debit or credit amount is required.` });
        return;
      }
      if (hasDebit && hasCredit) {
        setMessage({ type: 'error', text: `Entry ${i + 1}: Cannot have both debit and credit.` });
        return;
      }
    }

    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      // Prepare data for API - include flat info in description for 1100 entries
      const entryData = {
        date: formData.date,
        expense_month: formData.entries.some(e => e.account_code && e.account_code.startsWith('5'))
          ? formData.expense_for_month
          : null,
        description: formData.description,
        entries: formData.entries.map(entry => {
          let description = entry.description || '';
          // Add flat info to description if 1100 is selected
          if (entry.account_code === '1100' && entry.flat_id) {
            const selectedFlat = flats.find(f => f.id === parseInt(entry.flat_id));
            if (selectedFlat) {
              description = description ? `${description} - Flat: ${selectedFlat.flat_number}` : `Flat: ${selectedFlat.flat_number}`;
            }
          }
          return {
            account_code: entry.account_code,
            debit_amount: parseFloat(entry.debit_amount) || 0,
            credit_amount: parseFloat(entry.credit_amount) || 0,
            description: description
          };
        })
      };

      if (editingVoucher) {
        // Update existing voucher
        await journalService.updateJournalEntry(editingVoucher, entryData);
        setMessage({ type: 'success', text: 'Journal voucher updated successfully!' });
      } else {
        // Create new voucher
        await journalService.createJournalEntry(entryData);
        setMessage({ type: 'success', text: 'Journal voucher created successfully!' });
      }

      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
      handleCancel();
      await loadVouchers();
    } catch (error) {
      console.error('Error saving voucher:', error);
      const errorMsg = getErrorMessage(error) || 'Failed to save journal voucher. Please try again.';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setSaving(false);
    }
  };

  const { totalDebit, totalCredit, balanced } = calculateTotal();

  if (loading) {
    return (
      <div className="settings-tab-content">
        <h2 className="settings-tab-title">📝 Journal Voucher</h2>
        <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
          Loading journal vouchers...
        </div>
      </div>
    );
  }

  return (
    <div className="settings-tab-content">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 className="settings-tab-title">📝 Journal Voucher</h2>
          <p className="settings-tab-description">Create double-entry journal vouchers</p>
        </div>
        <button className="settings-add-btn" onClick={() => {
          handleCancel();
          setShowForm(true);
        }}>
          {showForm ? '✕ Cancel' : '+ New Voucher'}
        </button>
      </div>

      {/* Success/Error Message */}
      {message.text && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '20px',
          backgroundColor: message.type === 'success' ? '#E8F5E9' : '#FFEBEE',
          color: message.type === 'success' ? '#2E7D32' : '#C62828',
          border: `1px solid ${message.type === 'success' ? '#4CAF50' : '#EF5350'}`,
        }}>
          {message.text}
        </div>
      )}

      {showForm && (
        <div className="settings-section" style={{ marginBottom: '20px' }}>
          <h3>{editingVoucher ? 'Edit Journal Voucher' : 'Create Journal Voucher'}</h3>
          <form className="settings-form" onSubmit={handleSubmit}>
            <div className="settings-form-row">
              <div className="settings-form-group">
                <label>Voucher Date *</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  required
                  disabled={saving}
                />
              </div>
              {formData.entries.some(e => e.account_code && e.account_code.startsWith('5')) && (
                <div className="settings-form-group">
                  <label>Expense For Month *</label>
                  <input
                    type="text"
                    value={formData.expense_for_month}
                    onChange={(e) => setFormData({ ...formData, expense_for_month: e.target.value })}
                    placeholder="January, 2026"
                    required
                    disabled={saving}
                    style={{ position: 'relative' }}
                  />
                </div>
              )}
            </div>
            <div className="settings-form-row">
              <div className="settings-form-group" style={{ width: '100%' }}>
                <label>Description/Narration *</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enter description/narration..."
                  required
                  disabled={saving}
                />
              </div>
            </div>

            <div className="settings-section" style={{ marginTop: '20px', padding: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                <h4 style={{ margin: 0 }}>Journal Entries</h4>
                <button type="button" className="settings-add-btn" onClick={addEntry}>
                  + Add Entry
                </button>
              </div>

              <div className="settings-table-container">
                <table className="settings-table">
                  <thead>
                    <tr>
                      <th>Account</th>
                      <th>Debit (₹)</th>
                      <th>Credit (₹)</th>
                      <th>Description</th>
                      {formData.entries.some(e => e.account_code === '1100') && <th>Flat</th>}
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {formData.entries.map((entry, index) => {
                      const searchKey = `entry_${index}`;
                      const accountSearch = accountSearches[searchKey] || '';
                      const filteredAccounts = accountSearch.trim() === '' 
                        ? accounts 
                        : accounts.filter(acc =>
                            acc.code.toLowerCase().includes(accountSearch.toLowerCase()) ||
                            acc.name.toLowerCase().includes(accountSearch.toLowerCase())
                          );
                      const showDropdown = showAccountDropdowns[searchKey] && filteredAccounts.length > 0;
                      
                      return (
                        <tr key={index}>
                        <td style={{ position: 'relative' }}>
                          <input
                            type="text"
                            value={accountSearch || (entry.account_code ? `${entry.account_code} - ${accounts.find(a => a.code === entry.account_code)?.name || ''}` : '')}
                            onChange={(e) => {
                              const value = e.target.value;
                              setAccountSearches({ ...accountSearches, [searchKey]: value });
                              setShowAccountDropdowns({ ...showAccountDropdowns, [searchKey]: true });
                              // If user types account code directly, try to match
                              const match = accounts.find(acc => acc.code === value || `${acc.code} - ${acc.name}` === value);
                              if (match) {
                                const newEntries = [...formData.entries];
                                newEntries[index].account_code = match.code;
                                setFormData({ ...formData, entries: newEntries });
                                setAccountSearches({ ...accountSearches, [searchKey]: '' });
                                setShowAccountDropdowns({ ...showAccountDropdowns, [searchKey]: false });
                              }
                            }}
                            onFocus={() => setShowAccountDropdowns({ ...showAccountDropdowns, [searchKey]: true })}
                            onBlur={() => setTimeout(() => setShowAccountDropdowns({ ...showAccountDropdowns, [searchKey]: false }), 200)}
                            placeholder="Type account code or name..."
                            required
                            disabled={saving}
                            style={{ width: '100%', padding: '8px' }}
                          />
                          {showDropdown && (
                            <div style={{
                              position: 'absolute',
                              top: '100%',
                              left: 0,
                              right: 0,
                              backgroundColor: 'white',
                              border: '1px solid #ddd',
                              borderRadius: '4px',
                              maxHeight: '150px',
                              overflowY: 'auto',
                              zIndex: 1000,
                              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                            }}>
                              {filteredAccounts.map(acc => (
                                <div
                                  key={acc.code}
                                  onClick={() => {
                                    const newEntries = [...formData.entries];
                                    newEntries[index].account_code = acc.code;
                                    setFormData({ ...formData, entries: newEntries });
                                    setAccountSearches({ ...accountSearches, [searchKey]: '' });
                                    setShowAccountDropdowns({ ...showAccountDropdowns, [searchKey]: false });
                                  }}
                                  style={{
                                    padding: '8px',
                                    cursor: 'pointer',
                                    borderBottom: '1px solid #eee',
                                    fontSize: '12px'
                                  }}
                                  onMouseEnter={(e) => e.target.style.backgroundColor = '#f5f5f5'}
                                  onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                                >
                                  <strong>{acc.code}</strong> - {acc.name}
                                </div>
                              ))}
                            </div>
                          )}
                        </td>
                        <td>
                          <input
                            type="number"
                            value={entry.debit_amount}
                            onChange={(e) => {
                              const newEntries = [...formData.entries];
                              newEntries[index].debit_amount = e.target.value;
                              newEntries[index].credit_amount = '';
                              setFormData({ ...formData, entries: newEntries });
                            }}
                            step="0.01"
                            placeholder="0.00"
                            disabled={saving}
                            style={{ width: '100%', padding: '8px' }}
                          />
                        </td>
                        <td>
                          <input
                            type="number"
                            value={entry.credit_amount}
                            onChange={(e) => {
                              const newEntries = [...formData.entries];
                              newEntries[index].credit_amount = e.target.value;
                              newEntries[index].debit_amount = '';
                              setFormData({ ...formData, entries: newEntries });
                            }}
                            step="0.01"
                            placeholder="0.00"
                            disabled={saving}
                            style={{ width: '100%', padding: '8px' }}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={entry.description}
                            onChange={(e) => {
                              const newEntries = [...formData.entries];
                              newEntries[index].description = e.target.value;
                              setFormData({ ...formData, entries: newEntries });
                            }}
                            placeholder="Description"
                            style={{ width: '100%', padding: '8px' }}
                            disabled={saving}
                          />
                        </td>
                        {formData.entries.some(e => e.account_code === '1100') && (
                          <td>
                            {entry.account_code === '1100' ? (
                              <select
                                value={entry.flat_id}
                                onChange={(e) => {
                                  const newEntries = [...formData.entries];
                                  newEntries[index].flat_id = e.target.value;
                                  setFormData({ ...formData, entries: newEntries });
                                }}
                                required
                                disabled={saving}
                                style={{ width: '100%', padding: '8px' }}
                              >
                                <option value="">Select Flat</option>
                                {flats.map(flat => (
                                  <option key={flat.id} value={flat.id}>
                                    {flat.flat_number}
                                  </option>
                                ))}
                              </select>
                            ) : (
                              <span style={{ color: '#999' }}>-</span>
                            )}
                          </td>
                        )}
                        <td>
                          {formData.entries.length > 2 && (
                            <button
                              type="button"
                              className="settings-action-btn danger"
                              onClick={() => removeEntry(index)}
                              disabled={saving}
                            >
                              Remove
                            </button>
                          )}
                        </td>
                      </tr>
                      );
                    })}
                    <tr style={{ background: '#f5f5f5', fontWeight: 'bold' }}>
                      <td>Total</td>
                      <td style={{ color: balanced ? '#2E7D32' : '#C62828' }}>
                        {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(totalDebit)}
                      </td>
                      <td style={{ color: balanced ? '#2E7D32' : '#C62828' }}>
                        {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(totalCredit)}
                      </td>
                      <td colSpan="2">
                        {balanced ? (
                          <span style={{ color: '#2E7D32' }}>✅ Balanced</span>
                        ) : (
                          <span style={{ color: '#C62828' }}>❌ Not Balanced</span>
                        )}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="settings-form-actions">
              <button type="submit" className="settings-save-btn" disabled={!balanced || saving}>
                {saving ? 'Saving...' : editingVoucher ? 'Update Voucher' : 'Save Voucher'}
              </button>
              <button type="button" className="settings-cancel-btn" onClick={handleCancel} disabled={saving}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="settings-section">
        <h3>Journal Vouchers</h3>
        {vouchers.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
            No journal vouchers found. Create a new voucher to get started.
          </div>
        ) : (
          <div className="settings-table-container">
            <table className="settings-table">
              <thead>
                <tr>
                  <th>Voucher #</th>
                  <th>Date</th>
                  <th>Entries</th>
                  <th>Total Amount</th>
                  <th>Description</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {vouchers.map((voucher) => (
                  <tr key={voucher.id}>
                    <td><strong>{voucher.entry_number || `JV-${voucher.id}`}</strong></td>
                    <td>{voucher.date}</td>
                    <td>
                      {voucher.entries && voucher.entries.map((e, i) => {
                        const account = accounts.find(acc => acc.code === e.account_code);
                        const accountName = account ? `${e.account_code} - ${account.name}` : e.account_code;
                        return (
                          <div key={i} style={{ fontSize: '12px', marginBottom: '4px' }}>
                            {accountName}: {e.debit_amount > 0 ? `Dr ₹${e.debit_amount.toLocaleString('en-IN')}` : `Cr ₹${e.credit_amount.toLocaleString('en-IN')}`}
                          </div>
                        );
                      })}
                    </td>
                    <td>
                      {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(
                        voucher.total_debit || voucher.total_credit || 0
                      )}
                    </td>
                    <td>{voucher.description || '-'}</td>
                    <td>
                      <button
                        className="settings-action-btn"
                        onClick={() => handleEdit(voucher)}
                        disabled={saving}
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

// Reports Tab
const ReportsTab = () => {
  const [selectedReport, setSelectedReport] = useState('');
  const [reportParams, setReportParams] = useState({
    from_date: '',
    to_date: '',
    account: '',
    as_on_date: '', // For trial balance and balance sheet
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [reportData, setReportData] = useState(null);
  const [accounts, setAccounts] = useState([]);

  useEffect(() => {
    const loadAccounts = async () => {
      try {
        const data = await accountingService.getAccounts();
        setAccounts(data || []);
      } catch (error) {
        console.error('Error loading accounts for reports:', error);
      }
    };
    loadAccounts();
  }, []);

  const reports = [
    { id: 'trial-balance', label: 'Trial Balance', icon: '⚖️' },
    { id: 'profit-loss', label: 'Profit & Loss', icon: '📊' },
    { id: 'balance-sheet', label: 'Balance Sheet', icon: '📋' },
    { id: 'ledger', label: 'Ledger Statement', icon: '📖' },
    { id: 'daybook', label: 'Day Book', icon: '📅' },
    { id: 'cash-flow', label: 'Cash Flow', icon: '💵' },
  ];

  const handleGenerateReport = async () => {
    if (!selectedReport) {
      setError('Please select a report type');
      setSuccess('');
      return;
    }

    // Validate date for trial balance
    if (selectedReport === 'trial-balance' || selectedReport === 'balance-sheet') {
      const asOnDate = reportParams.as_on_date || reportParams.to_date || reportParams.from_date;
      if (!asOnDate) {
        setError('Please select a date (As On Date)');
        setSuccess('');
        return;
      }
    } else {
      if (!reportParams.from_date || !reportParams.to_date) {
        setError('Please select both From Date and To Date');
        setSuccess('');
        return;
      }
    }

    setLoading(true);
    setError('');
    setSuccess('');
    setReportData(null);

    try {
      let response;

      if (selectedReport === 'trial-balance') {
        const asOnDate = reportParams.as_on_date || reportParams.to_date || reportParams.from_date;
        response = await api.get('/reports/trial-balance', {
          params: { as_on_date: asOnDate }
        });
        setReportData(response.data);
        setSuccess(`Trial Balance generated successfully for ${asOnDate}`);
      } else if (selectedReport === 'ledger') {
        if (!reportParams.account) {
          setError('Please select an account for the Ledger Statement');
          setLoading(false);
          return;
        }
        response = await api.get('/reports/ledger', {
          params: {
            from_date: reportParams.from_date,
            to_date: reportParams.to_date,
            account_code: reportParams.account
          }
        });
        setReportData(response.data);
        setSuccess(`Ledger Statement generated successfully for ${response.data.account_name}`);
      } else if (selectedReport === 'balance-sheet') {
        response = await api.get('/reports/balance-sheet', {
          params: {
            from_date: reportParams.from_date || reportParams.as_on_date,
            to_date: reportParams.to_date || reportParams.as_on_date
          }
        });
        setReportData(response.data);
        setSuccess(`Balance Sheet generated successfully`);
      } else if (selectedReport === 'profit-loss') {
        response = await api.get('/reports/income-and-expenditure', {
          params: {
            from_date: reportParams.from_date,
            to_date: reportParams.to_date
          }
        });
        setReportData(response.data);
        setSuccess(`Income & Expenditure report generated successfully`);
      } else if (selectedReport === 'cash-flow') {
        response = await api.get('/reports/receipts-and-payments', {
          params: {
            from_date: reportParams.from_date,
            to_date: reportParams.to_date
          }
        });
        setReportData(response.data);
        setSuccess(`Receipts & Payments report generated successfully`);
      } else {
        // Other reports - TODO: Implement when backend endpoints are ready
        setError(`${reports.find(r => r.id === selectedReport)?.label} report generation is not yet implemented`);
        setLoading(false);
        return;
      }

      setLoading(false);
    } catch (err) {
      setLoading(false);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to generate report. Please try again.';
      setError(errorMessage);
      setReportData(null);
      console.error('Error generating report:', err);
    }
  };

  return (
    <div className="settings-tab-content">
      <h2 className="settings-tab-title">📈 Accounting Reports</h2>
      <p className="settings-tab-description">Generate financial reports and statements</p>

      <div className="settings-section">
        <h3>Select Report Type</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
          {reports.map((report) => (
            <button
              key={report.id}
              onClick={() => {
                setSelectedReport(report.id);
                setReportData(null);
                setError('');
                setSuccess('');
              }}
              style={{
                padding: '20px',
                border: `3px solid ${selectedReport === report.id ? 'var(--gm-orange)' : '#e0e0e0'}`,
                borderRadius: '12px',
                background: selectedReport === report.id ? 'var(--gm-bg-light)' : 'white',
                cursor: 'pointer',
                textAlign: 'center',
                transition: 'all 0.2s'
              }}
            >
              <span style={{ fontSize: '32px', display: 'block', marginBottom: '8px' }}>{report.icon}</span>
              <strong>{report.label}</strong>
            </button>
          ))}
        </div>

        {selectedReport && (
          <div className="settings-form">
            <h4 style={{ marginBottom: '15px' }}>Report Parameters</h4>

            {/* Trial Balance and Balance Sheet use As On Date */}
            {(selectedReport === 'trial-balance' || selectedReport === 'balance-sheet') ? (
              <div className="settings-form-group">
                <label>As On Date <span style={{ color: 'red' }}>*</span></label>
                <input
                  type="date"
                  value={reportParams.as_on_date || reportParams.to_date || reportParams.from_date}
                  onChange={(e) => {
                    const date = e.target.value;
                    setReportParams({ ...reportParams, as_on_date: date, to_date: date, from_date: date });
                  }}
                  required
                />
              </div>
            ) : (
              <div className="settings-form-row">
                <div className="settings-form-group">
                  <label>From Date <span style={{ color: 'red' }}>*</span></label>
                  <input
                    type="date"
                    value={reportParams.from_date}
                    onChange={(e) => setReportParams({ ...reportParams, from_date: e.target.value })}
                    required
                  />
                </div>
                <div className="settings-form-group">
                  <label>To Date <span style={{ color: 'red' }}>*</span></label>
                  <input
                    type="date"
                    value={reportParams.to_date}
                    onChange={(e) => setReportParams({ ...reportParams, to_date: e.target.value })}
                    required
                  />
                </div>
              </div>
            )}

            {(selectedReport === 'ledger' || selectedReport === 'daybook') && (
              <div className="settings-form-group">
                <label>Account</label>
                <select
                  value={reportParams.account}
                  onChange={(e) => setReportParams({ ...reportParams, account: e.target.value })}
                >
                  <option value="">Select Account</option>
                  <option value="all">All Accounts (with non-zero activity)</option>
                  {accounts.map(account => (
                    <option key={account.code} value={account.code}>
                      {account.code} - {account.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Error and Success Messages */}
            {error && (
              <div style={{
                padding: '12px',
                backgroundColor: '#fee',
                border: '1px solid #fcc',
                borderRadius: '6px',
                color: '#c33',
                marginBottom: '15px'
              }}>
                <strong>Error:</strong> {error}
              </div>
            )}
            {success && (
              <div style={{
                padding: '12px',
                backgroundColor: '#efe',
                border: '1px solid #cfc',
                borderRadius: '6px',
                color: '#3c3',
                marginBottom: '15px'
              }}>
                <strong>Success:</strong> {success}
              </div>
            )}

            <div className="settings-form-actions">
              <button
                className="settings-save-btn"
                onClick={handleGenerateReport}
                disabled={loading}
              >
                {loading ? 'Generating...' : 'Generate Report'}
              </button>
              {reportData && (
                <>
                  <button className="settings-action-btn">Export PDF</button>
                  <button className="settings-action-btn">Export Excel</button>
                </>
              )}
            </div>
          </div>
        )}

        {/* Report Results Display */}
        {reportData && selectedReport === 'trial-balance' && (
          <div className="settings-section" style={{ marginTop: '30px' }}>
            <h3>Trial Balance Report</h3>
            <div style={{ marginBottom: '15px', color: '#666' }}>
              <strong>As On Date:</strong> {reportData.as_on_date} |
              <strong> Total Debit:</strong> ₹{reportData.total_debit.toLocaleString('en-IN', { minimumFractionDigits: 2 })} |
              <strong> Total Credit:</strong> ₹{reportData.total_credit.toLocaleString('en-IN', { minimumFractionDigits: 2 })} |
              <strong> Difference:</strong> ₹{reportData.difference.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              {reportData.is_balanced ? (
                <span style={{ color: 'green', marginLeft: '10px' }}>✓ Balanced</span>
              ) : (
                <span style={{ color: 'red', marginLeft: '10px' }}>⚠ Not Balanced</span>
              )}
            </div>
            <div className="settings-table-container">
              <table className="settings-table">
                <thead>
                  <tr>
                    <th>Account Code</th>
                    <th>Account Name</th>
                    <th style={{ textAlign: 'right' }}>Debit Balance</th>
                    <th style={{ textAlign: 'right' }}>Credit Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.items && reportData.items.length > 0 ? (
                    reportData.items.map((item, index) => (
                      <tr key={index}>
                        <td>{item.account_code}</td>
                        <td>{item.account_name}</td>
                        <td style={{ textAlign: 'right' }}>
                          {item.debit_balance > 0 ? `₹${item.debit_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          {item.credit_balance > 0 ? `₹${item.credit_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                        No accounts with balances found
                      </td>
                    </tr>
                  )}
                  {/* Totals Row */}
                  {reportData.items && reportData.items.length > 0 && (
                    <tr style={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>
                      <td colSpan="2">Total</td>
                      <td style={{ textAlign: 'right' }}>
                        ₹{reportData.total_debit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        ₹{reportData.total_credit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {reportData && selectedReport === 'balance-sheet' && (
          <div className="settings-section" style={{ marginTop: '30px' }}>
            <h3>Balance Sheet Report</h3>
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
                      {reportData.assets && reportData.assets.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.account_name}</td>
                          <td style={{ textAlign: 'right' }}>₹{item.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr style={{ fontWeight: 'bold' }}>
                        <td>Total Assets</td>
                        <td style={{ textAlign: 'right' }}>₹{reportData.total_assets.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
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
                      {reportData.liabilities && reportData.liabilities.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.account_name}</td>
                          <td style={{ textAlign: 'right' }}>₹{item.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        </tr>
                      ))}
                      {reportData.capital && reportData.capital.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.account_name}</td>
                          <td style={{ textAlign: 'right' }}>₹{item.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr style={{ fontWeight: 'bold' }}>
                        <td>Total Liabilities & Capital</td>
                        <td style={{ textAlign: 'right' }}>₹{reportData.total_liabilities_capital.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {reportData && selectedReport === 'profit-loss' && (
          <div className="settings-section" style={{ marginTop: '30px' }}>
            <h3>Income & Expenditure Report</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
              <div style={{ padding: '15px', backgroundColor: '#f0f8ff', borderRadius: '8px' }}>
                <h4 style={{ marginTop: 0, color: '#007AFF' }}>Total Income</h4>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007AFF' }}>
                  ₹{reportData.total_income.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div style={{ padding: '15px', backgroundColor: '#fff0f0', borderRadius: '8px' }}>
                <h4 style={{ marginTop: 0, color: '#FF3B30' }}>Total Expenditure</h4>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#FF3B30' }}>
                  ₹{reportData.total_expenditure.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>
            <div style={{ padding: '15px', backgroundColor: reportData.net_income >= 0 ? '#f0fff0' : '#fff0f0', borderRadius: '8px', marginBottom: '20px' }}>
              <h4 style={{ marginTop: 0 }}>Net Income / (Loss)</h4>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: reportData.net_income >= 0 ? '#34C759' : '#FF3B30' }}>
                ₹{reportData.net_income.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </div>
            </div>
            {reportData.income_items && reportData.income_items.length > 0 && (
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
                      {reportData.income_items.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.account_code}</td>
                          <td>{item.account_name}</td>
                          <td style={{ textAlign: 'right' }}>₹{item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            {reportData.expenditure_items && reportData.expenditure_items.length > 0 && (
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
                      {reportData.expenditure_items.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.account_code}</td>
                          <td>{item.account_name}</td>
                          <td style={{ textAlign: 'right' }}>₹{item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {reportData && selectedReport === 'cash-flow' && (
          <div className="settings-section" style={{ marginTop: '30px' }}>
            <h3>Receipts & Payments Report</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
              <div style={{ padding: '15px', backgroundColor: '#f0f8ff', borderRadius: '8px' }}>
                <h4 style={{ marginTop: 0, color: '#007AFF' }}>Receipts</h4>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007AFF' }}>
                  ₹{reportData.total_receipts.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div style={{ padding: '15px', backgroundColor: '#fff0f0', borderRadius: '8px' }}>
                <h4 style={{ marginTop: 0, color: '#FF3B30' }}>Payments</h4>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#FF3B30' }}>
                  ₹{reportData.total_payments.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>
            {reportData.receipts && reportData.receipts.length > 0 && (
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
                      {reportData.receipts.map((item, idx) => (
                        <tr key={idx}>
                          <td>{new Date(item.date).toLocaleDateString()}</td>
                          <td>{item.description}</td>
                          <td style={{ textAlign: 'right' }}>₹{item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            {reportData.payments && reportData.payments.length > 0 && (
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
                      {reportData.payments.map((item, idx) => (
                        <tr key={idx}>
                          <td>{new Date(item.date).toLocaleDateString()}</td>
                          <td>{item.description}</td>
                          <td style={{ textAlign: 'right' }}>₹{item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {reportData && selectedReport === 'ledger' && (
          <div className="settings-section" style={{ marginTop: '30px' }}>
            {reportData.ledgers ? (
              // Bulk Ledger Rendering
              <div>
                <h3>Bulk Ledger Statements</h3>
                <div style={{ marginBottom: '20px', color: '#666' }}>
                  <strong>Period:</strong> {reportData.from_date} to {reportData.to_date} |
                  <strong> Total Accounts:</strong> {reportData.ledgers.length}
                </div>
                {reportData.ledgers.map((ledger, idx) => (
                  <div key={idx} style={{ marginBottom: '40px', borderBottom: '2px solid #eee', paddingBottom: '20px' }}>
                    <h4 style={{ color: '#d35400' }}>{ledger.account_code} - {ledger.account_name}</h4>
                    <div style={{ marginBottom: '10px', fontSize: '14px' }}>
                      <strong>Opening:</strong> ₹{ledger.opening_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })} |
                      <strong> Closing:</strong> ₹{ledger.closing_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </div>
                    <div className="settings-table-container">
                      <table className="settings-table">
                        <thead>
                          <tr>
                            <th>Date</th>
                            <th>Description</th>
                            <th>Reference</th>
                            <th style={{ textAlign: 'right' }}>Debit</th>
                            <th style={{ textAlign: 'right' }}>Credit</th>
                            <th style={{ textAlign: 'right' }}>Balance</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr style={{ backgroundColor: '#f9f9f9', fontStyle: 'italic' }}>
                            <td colSpan="5">Opening Balance</td>
                            <td style={{ textAlign: 'right' }}>₹{ledger.opening_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                          </tr>
                          {ledger.entries.map((entry, eIdx) => (
                            <tr key={eIdx}>
                              <td>{entry.date}</td>
                              <td>{entry.description}</td>
                              <td>{entry.reference || '-'}</td>
                              <td style={{ textAlign: 'right' }}>{entry.debit > 0 ? `₹${entry.debit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}</td>
                              <td style={{ textAlign: 'right' }}>{entry.credit > 0 ? `₹${entry.credit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}</td>
                              <td style={{ textAlign: 'right', fontWeight: 'bold' }}>₹{entry.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                            </tr>
                          ))}
                          <tr style={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>
                            <td colSpan="3">Totals</td>
                            <td style={{ textAlign: 'right' }}>₹{ledger.total_debit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                            <td style={{ textAlign: 'right' }}>₹{ledger.total_credit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                            <td style={{ textAlign: 'right' }}>Closing: ₹{ledger.closing_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // Single Ledger Rendering (original logic)
              <div>
                <h3>Ledger Statement: {reportData.account_name} ({reportData.account_code})</h3>
                <div style={{ marginBottom: '15px', color: '#666' }}>
                  <strong>Period:</strong> {reportData.from_date} to {reportData.to_date} |
                  <strong> Opening Balance:</strong> ₹{reportData.opening_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
                <div className="settings-table-container">
                  <table className="settings-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Reference</th>
                        <th style={{ textAlign: 'right' }}>Debit</th>
                        <th style={{ textAlign: 'right' }}>Credit</th>
                        <th style={{ textAlign: 'right' }}>Balance</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ backgroundColor: '#f9f9f9', fontStyle: 'italic' }}>
                        <td colSpan="5">Opening Balance</td>
                        <td style={{ textAlign: 'right' }}>
                          ₹{reportData.opening_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                      {reportData.entries && reportData.entries.length > 0 ? (
                        reportData.entries.map((entry, index) => (
                          <tr key={index}>
                            <td>{entry.date}</td>
                            <td>{entry.description}</td>
                            <td>{entry.reference || '-'}</td>
                            <td style={{ textAlign: 'right' }}>
                              {entry.debit > 0 ? `₹${entry.debit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              {entry.credit > 0 ? `₹${entry.credit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '-'}
                            </td>
                            <td style={{ textAlign: 'right', fontWeight: 'bold' }}>
                              ₹{entry.balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="6" style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                            No transactions found for this period
                          </td>
                        </tr>
                      )}
                      <tr style={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>
                        <td colSpan="3">Total Movements</td>
                        <td style={{ textAlign: 'right' }}>
                          ₹{reportData.total_debit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          ₹{reportData.total_credit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          Closing: ₹{reportData.closing_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="settings-section">
        <h3>Recent Reports</h3>
        <div className="settings-table-container">
          <table className="settings-table">
            <thead>
              <tr>
                <th>Report Type</th>
                <th>Generated On</th>
                <th>Period</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Trial Balance</td>
                <td>2026-01-05 10:30 AM</td>
                <td>Jan 2026</td>
                <td>
                  <button className="settings-action-btn">View</button>
                  <button className="settings-action-btn">Download</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AccountingScreen;


