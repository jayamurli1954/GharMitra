/**
 * GharMitra Members Screen
 * Admin can onboard new members (owners/tenants) with flat assignment
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import memberOnboardingService from '../services/memberOnboardingService';
import flatsService from '../services/flatsService';

const MembersScreen = () => {
  const navigate = useNavigate();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadMembers();
  }, [statusFilter]);

  const loadMembers = async () => {
    setLoading(true);
    try {
      const filter = statusFilter === 'all' ? undefined : statusFilter;
      const membersList = await memberOnboardingService.listMembers(filter);
      console.log(`Loaded ${membersList.length} members`);
      setMembers(membersList);
      
      // Debug: Check if we're getting data
      if (membersList.length === 0) {
        console.warn('No members found. Checking debug endpoint...');
        try {
          const debugRes = await api.get('/member-onboarding/debug');
          console.log('Debug info:', debugRes.data);
        } catch (debugError) {
          console.error('Debug endpoint error:', debugError);
        }
      }
    } catch (error) {
      console.error('Error loading members:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      alert(`Failed to load members: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const filteredMembers = members.filter(member => {
    const matchesSearch =
      member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.flat_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (member.email && member.email.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSearch;
  }).sort((a, b) => {
    // Sort by flat number (A-101, A-102, A-103, etc.)
    return a.flat_number.localeCompare(b.flat_number, undefined, { numeric: true, sensitivity: 'base' });
  });

  const stats = {
    total: members.filter(m => m.status === 'active').reduce((sum, m) => sum + (m.total_occupants || 0), 0),
    owners: members.filter(m => m.status === 'active' && m.member_type === 'owner').length,
    tenants: members.filter(m => m.status === 'active' && m.member_type === 'tenant').length,
    active: members.filter(m => m.status === 'active').length,
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="dashboard-header">
        <div className="dashboard-header-left">
          <h1 className="dashboard-header-title">👥 Members</h1>
          <span className="dashboard-header-subtitle">Member Onboarding & Management</span>
        </div>
        <div className="dashboard-header-right">
          <button onClick={() => navigate('/dashboard')} className="dashboard-logout-button">
            ← Back to Dashboard
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {/* Stats Cards */}
        <div className="dashboard-metrics-grid">
          <div className="dashboard-metric-card">
            <span className="dashboard-metric-icon">👥</span>
            <div className="dashboard-metric-label">Total Members</div>
            <div className="dashboard-metric-value">{stats.total}</div>
          </div>
          <div className="dashboard-metric-card">
            <span className="dashboard-metric-icon">🏠</span>
            <div className="dashboard-metric-label">Owners</div>
            <div className="dashboard-metric-value">{stats.owners}</div>
          </div>
          <div className="dashboard-metric-card">
            <span className="dashboard-metric-icon">🔑</span>
            <div className="dashboard-metric-label">Tenants</div>
            <div className="dashboard-metric-value">{stats.tenants}</div>
          </div>
          <div className="dashboard-metric-card">
            <span className="dashboard-metric-icon">✅</span>
            <div className="dashboard-metric-label">Active</div>
            <div className="dashboard-metric-value">{stats.active}</div>
          </div>
        </div>

        {/* Actions Bar */}
        <div style={{
          display: 'flex',
          gap: '12px',
          marginBottom: '24px',
          flexWrap: 'wrap',
          alignItems: 'center'
        }}>
          <button
            onClick={() => setShowAddForm(true)}
            className="login-button"
            style={{ maxWidth: '200px' }}
          >
            ➕ Add New Member
          </button>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '10px 16px',
              borderRadius: '8px',
              border: '1px solid #ddd',
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="moved_out">Moved Out</option>
          </select>

          <input
            type="text"
            placeholder="Search members..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              flex: 1,
              minWidth: '200px',
              padding: '10px 16px',
              borderRadius: '8px',
              border: '1px solid #ddd',
              fontSize: '14px',
            }}
          />
        </div>

        {/* Members List */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <div style={{ fontSize: '18px', color: '#666' }}>Loading members...</div>
          </div>
        ) : filteredMembers.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>👥</div>
            <div style={{ fontSize: '18px', color: '#666', marginBottom: '8px' }}>
              {searchQuery ? 'No members found' : 'No members yet'}
            </div>
            {!searchQuery && (
              <button
                onClick={() => setShowAddForm(true)}
                className="login-button"
                style={{ maxWidth: '200px', marginTop: '16px' }}
              >
                Add First Member
              </button>
            )}
          </div>
        ) : (
          <div style={{
            background: '#fff',
            borderRadius: '12px',
            overflow: 'hidden',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            border: '1px solid #E5E5EA',
          }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#F5F5F7', borderBottom: '2px solid #E5E5EA' }}>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '14px', fontWeight: '600', color: '#666', minWidth: '100px' }}>Flat</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '14px', fontWeight: '600', color: '#666', minWidth: '150px' }}>Name</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '14px', fontWeight: '600', color: '#666', minWidth: '120px' }}>Type</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '14px', fontWeight: '600', color: '#666', minWidth: '150px' }}>Email</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '14px', fontWeight: '600', color: '#666', minWidth: '120px' }}>Phone</th>
                    <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '14px', fontWeight: '600', color: '#666', minWidth: '80px' }}>Occupants</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '14px', fontWeight: '600', color: '#666', minWidth: '120px' }}>Move-In Date</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '14px', fontWeight: '600', color: '#666', minWidth: '100px' }}>Status</th>
                    <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '14px', fontWeight: '600', color: '#666', minWidth: '120px' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMembers.map((member, index) => (
                    <MemberRow
                      key={member.id}
                      member={member}
                      onUpdate={loadMembers}
                      isEven={index % 2 === 0}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Add Member Modal */}
      {showAddForm && (
        <AddMemberModal
          onClose={() => {
            setShowAddForm(false);
            loadMembers();
          }}
        />
      )}
    </div>
  );
};

// Member Row Component (Table Row with Editable Fields)
const MemberRow = ({ member, onUpdate, isEven }) => {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showMoveOut, setShowMoveOut] = useState(false);
  const [moveOutDate, setMoveOutDate] = useState('');

  const [editData, setEditData] = useState({
    name: member.name || '',
    email: member.email || '',
    phone_number: member.phone_number || '',
    total_occupants: member.total_occupants || 1,
  });

  const handleSave = async () => {
    setSaving(true);
    try {
      await memberOnboardingService.updateMember(member.id, editData);
      alert('Member updated successfully!');
      setEditing(false);
      onUpdate();
    } catch (error) {
      console.error('Error updating member:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update member';
      alert(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditData({
      name: member.name || '',
      email: member.email || '',
      phone_number: member.phone_number || '',
      total_occupants: member.total_occupants || 1,
    });
    setEditing(false);
  };

  const handleMoveOut = async () => {
    if (!moveOutDate) {
      alert('Please enter move-out date');
      return;
    }

    setSaving(true);
    try {
      await memberOnboardingService.updateMember(member.id, {
        status: 'moved_out',
        move_out_date: moveOutDate,
      });
      alert('Member marked as moved out successfully!');
      setShowMoveOut(false);
      setMoveOutDate('');
      onUpdate();
    } catch (error) {
      console.error('Error updating member:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update member';
      alert(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#34C759';
      case 'inactive': return '#8E8E93';
      case 'moved_out': return '#FF9500';
      default: return '#8E8E93';
    }
  };

  const getMemberTypeIcon = (type) => {
    return type === 'owner' ? '🏠' : '🔑';
  };

  return (
    <>
      <tr style={{
        backgroundColor: isEven ? '#FAFAFA' : '#FFF',
        borderBottom: '1px solid #E5E5EA',
      }}>
        <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: '600', color: '#1D1D1F' }}>
          {member.flat_number}
        </td>
        <td style={{ padding: '12px 16px', fontSize: '14px' }}>
          {editing ? (
            <input
              type="text"
              value={editData.name}
              onChange={(e) => setEditData({ ...editData, name: e.target.value })}
              style={{
                width: '100%',
                padding: '6px 10px',
                borderRadius: '6px',
                border: '1px solid #ddd',
                fontSize: '14px',
              }}
            />
          ) : (
            <span style={{ color: '#1D1D1F' }}>{member.name}</span>
          )}
        </td>
        <td style={{ padding: '12px 16px', fontSize: '14px' }}>
          <span style={{
            display: 'inline-block',
            padding: '4px 10px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: '600',
            backgroundColor: member.member_type === 'owner' ? '#007AFF20' : '#34C75920',
            color: member.member_type === 'owner' ? '#007AFF' : '#34C759',
            textTransform: 'capitalize',
          }}>
            {getMemberTypeIcon(member.member_type)} {member.member_type}
          </span>
        </td>
        <td style={{ padding: '12px 16px', fontSize: '14px' }}>
          {editing ? (
            <input
              type="email"
              value={editData.email}
              onChange={(e) => setEditData({ ...editData, email: e.target.value })}
              style={{
                width: '100%',
                padding: '6px 10px',
                borderRadius: '6px',
                border: '1px solid #ddd',
                fontSize: '14px',
              }}
            />
          ) : (
            <span style={{ color: '#666' }}>{member.email || '-'}</span>
          )}
        </td>
        <td style={{ padding: '12px 16px', fontSize: '14px' }}>
          {editing ? (
            <input
              type="tel"
              value={editData.phone_number}
              onChange={(e) => setEditData({ ...editData, phone_number: e.target.value })}
              style={{
                width: '100%',
                padding: '6px 10px',
                borderRadius: '6px',
                border: '1px solid #ddd',
                fontSize: '14px',
              }}
            />
          ) : (
            <span style={{ color: '#666' }}>{member.phone_number && member.phone_number !== 'Private' ? member.phone_number : '-'}</span>
          )}
        </td>
        <td style={{ padding: '12px 16px', textAlign: 'center', fontSize: '14px' }}>
          {editing ? (
            <input
              type="number"
              value={editData.total_occupants}
              onChange={(e) => setEditData({ ...editData, total_occupants: parseInt(e.target.value) || 1 })}
              min="1"
              style={{
                width: '60px',
                padding: '6px 10px',
                borderRadius: '6px',
                border: '1px solid #ddd',
                fontSize: '14px',
                textAlign: 'center',
              }}
            />
          ) : (
            <span style={{ color: '#666' }}>{member.total_occupants || '-'}</span>
          )}
        </td>
        <td style={{ padding: '12px 16px', fontSize: '14px', color: '#666' }}>
          {member.move_in_date ? new Date(member.move_in_date).toLocaleDateString('en-GB') : '-'}
        </td>
        <td style={{ padding: '12px 16px', fontSize: '14px' }}>
          <span style={{
            display: 'inline-block',
            padding: '4px 10px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: '600',
            backgroundColor: getStatusColor(member.status) + '20',
            color: getStatusColor(member.status),
            textTransform: 'uppercase',
          }}>
            {member.status}
          </span>
        </td>
        <td style={{ padding: '12px 16px', textAlign: 'center' }}>
          {editing ? (
            <div style={{ display: 'flex', gap: '6px', justifyContent: 'center' }}>
              <button
                onClick={handleSave}
                disabled={saving}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: '#34C759',
                  color: '#FFF',
                  fontSize: '12px',
                  fontWeight: '600',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  opacity: saving ? 0.6 : 1,
                }}
              >
                {saving ? '⏳' : '✓'}
              </button>
              <button
                onClick={handleCancel}
                disabled={saving}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: '1px solid #ddd',
                  backgroundColor: '#FFF',
                  color: '#666',
                  fontSize: '12px',
                  fontWeight: '600',
                  cursor: saving ? 'not-allowed' : 'pointer',
                }}
              >
                ✕
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '6px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button
                onClick={() => setEditing(true)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: '1px solid #007AFF',
                  backgroundColor: '#FFF',
                  color: '#007AFF',
                  fontSize: '12px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                ✏️ Edit
              </button>
              {(() => {
                // Show Move Out button for active members who haven't moved out yet
                const isActive = member.status === 'active' || member.status === 'ACTIVE';

                // Check if member has moved out:
                // - No move_out_date means they haven't moved out
                // - If move_out_date exists, check if it's in the future (scheduled but not moved yet)
                // - If move_out_date is in the past, they've already moved out
                const hasMovedOut = member.move_out_date &&
                  member.move_out_date !== null &&
                  member.move_out_date !== '' &&
                  new Date(member.move_out_date) <= new Date();

                // Show button if active AND not moved out yet
                const shouldShow = isActive && !hasMovedOut;

                // Debug for A-304
                if (member.flat_number === 'A-304' || (member.flat_number || '').includes('A-304')) {
                  console.log('🔍 A-304 Move Out Button Check:', {
                    status: member.status,
                    isActive: isActive,
                    move_out_date: member.move_out_date,
                    hasMovedOut: hasMovedOut,
                    shouldShow: shouldShow,
                    currentDate: new Date().toISOString(),
                    moveOutDateParsed: member.move_out_date ? new Date(member.move_out_date).toISOString() : null,
                    dateComparison: member.move_out_date ? new Date(member.move_out_date) <= new Date() : null
                  });
                }

                return shouldShow;
              })() && (
                  <button
                    onClick={() => setShowMoveOut(!showMoveOut)}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      border: '1px solid #FF9500',
                      backgroundColor: '#FFF',
                      color: '#FF9500',
                      fontSize: '12px',
                      fontWeight: '600',
                      cursor: 'pointer',
                    }}
                  >
                    🚪 Move Out
                  </button>
                )}
            </div>
          )}
        </td>
      </tr>
      {showMoveOut && (
        <tr style={{ backgroundColor: '#FFF3E0' }}>
          <td colSpan="9" style={{ padding: '16px' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', maxWidth: '500px' }}>
              <label style={{ fontSize: '14px', fontWeight: '600', minWidth: '120px' }}>
                Move-Out Date (YYYY-MM-DD):
              </label>
              <input
                type="text"
                value={moveOutDate}
                onChange={(e) => setMoveOutDate(e.target.value)}
                placeholder="2024-01-15"
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                }}
              />
              <button
                onClick={handleMoveOut}
                disabled={saving}
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: '#FF9500',
                  color: '#FFF',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  opacity: saving ? 0.6 : 1,
                }}
              >
                {saving ? 'Saving...' : 'Confirm'}
              </button>
              <button
                onClick={() => {
                  setShowMoveOut(false);
                  setMoveOutDate('');
                }}
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  border: '1px solid #ddd',
                  backgroundColor: '#FFF',
                  color: '#666',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

// Add Member Modal Component
const AddMemberModal = ({ onClose }) => {
  const [flats, setFlats] = useState([]);
  const [members, setMembers] = useState([]);
  const [loadingFlats, setLoadingFlats] = useState(true);
  const [selectedFlat, setSelectedFlat] = useState(null);
  const [existingMember, setExistingMember] = useState(null);
  const [showFlatPicker, setShowFlatPicker] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form fields
  const [formData, setFormData] = useState({
    name: '',
    phone_number: '',
    email: '',
    member_type: 'owner',
    move_in_date: '',
    total_occupants: '1',
    occupation: '',
    is_mobile_public: false,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoadingFlats(true);
    try {
      const [flatsList, membersList] = await Promise.all([
        flatsService.getFlats(),
        memberOnboardingService.listMembers()
      ]);
      setFlats(flatsList);
      setMembers(membersList);
    } catch (error) {
      console.error('Error loading data:', error);
      alert('Failed to load data. Please try again.');
    } finally {
      setLoadingFlats(false);
    }
  };

  // Check if flat has existing active member
  const checkExistingMember = (flat) => {
    const member = members.find(m =>
      m.flat_number === flat.flat_number &&
      m.status === 'active' &&
      !m.move_out_date
    );
    return member;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (!selectedFlat) {
      alert('Please select a flat');
      return;
    }
    if (!formData.name.trim()) {
      alert('Please enter member name');
      return;
    }
    if (!formData.phone_number.trim() || formData.phone_number.length < 10) {
      alert('Please enter a valid phone number');
      return;
    }
    if (!formData.email.trim() || !formData.email.includes('@')) {
      alert('Please enter a valid email address');
      return;
    }
    if (!formData.move_in_date) {
      alert('Please enter move-in date (YYYY-MM-DD)');
      return;
    }
    if (!formData.total_occupants || parseInt(formData.total_occupants) < 1) {
      alert('Please enter valid number of occupants');
      return;
    }

    setSaving(true);
    try {
      const memberData = {
        flat_number: selectedFlat.flat_number,
        name: formData.name.trim(),
        phone_number: formData.phone_number.trim(),
        email: formData.email.trim(),
        member_type: formData.member_type,
        move_in_date: formData.move_in_date,
        total_occupants: parseInt(formData.total_occupants),
        is_primary: true,
        occupation: formData.occupation.trim() || undefined,
        is_mobile_public: formData.is_mobile_public,
      };

      await memberOnboardingService.createMember(memberData);
      alert('Member onboarded successfully!');
      onClose();
    } catch (error) {
      console.error('Error creating member:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to onboard member';
      alert(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px',
    }}>
      <div style={{
        background: '#fff',
        borderRadius: '12px',
        padding: '24px',
        maxWidth: '600px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#1D1D1F', margin: 0 }}>
            {existingMember ? 'Member Details' : 'Onboard New Member'}
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#8E8E93',
              padding: '4px 8px',
            }}
          >
            ×
          </button>
        </div>

        {/* Show existing member data if available */}
        {existingMember ? (
          <div>
            <div style={{
              padding: '20px',
              backgroundColor: '#E8F5E9',
              borderRadius: '8px',
              marginBottom: '20px',
              border: '1px solid #4CAF50'
            }}>
              <div style={{ fontSize: '16px', fontWeight: '600', color: '#2E7D32', marginBottom: '12px' }}>
                ✓ This flat already has a member onboarded
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>
                All member data is already captured. No need to onboard again.
              </div>
            </div>

            {/* Display Member Information */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ padding: '16px', backgroundColor: '#F5F5F7', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', fontWeight: '600', color: '#8E8E93', marginBottom: '8px', textTransform: 'uppercase' }}>
                  Flat Details
                </div>
                <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>
                  Flat {selectedFlat.flat_number}
                </div>
                <div style={{ fontSize: '14px', color: '#666', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                  <span>📐 {selectedFlat.area_sqft} sq ft</span>
                  {selectedFlat.bedrooms && <span>🛏️ {selectedFlat.bedrooms} BR</span>}
                </div>
              </div>

              <div style={{ padding: '16px', backgroundColor: '#F5F5F7', borderRadius: '8px' }}>
                <div style={{ fontSize: '12px', fontWeight: '600', color: '#8E8E93', marginBottom: '12px', textTransform: 'uppercase' }}>
                  Member Information
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#8E8E93', marginBottom: '4px' }}>Name</div>
                    <div style={{ fontSize: '16px', fontWeight: '600' }}>{existingMember.name}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#8E8E93', marginBottom: '4px' }}>Member Type</div>
                    <div style={{ fontSize: '16px', fontWeight: '600', textTransform: 'capitalize' }}>
                      {existingMember.member_type === 'owner' ? '🏠 Owner' : '🔑 Tenant'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#8E8E93', marginBottom: '4px' }}>Mobile Number</div>
                    <div style={{ fontSize: '16px' }}>{existingMember.phone_number || 'N/A'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#8E8E93', marginBottom: '4px' }}>Email Address</div>
                    <div style={{ fontSize: '16px' }}>{existingMember.email || 'N/A'}</div>
                  </div>
                  {existingMember.occupation && (
                    <div>
                      <div style={{ fontSize: '12px', color: '#8E8E93', marginBottom: '4px' }}>Occupation</div>
                      <div style={{ fontSize: '16px' }}>{existingMember.occupation}</div>
                    </div>
                  )}
                  <div>
                    <div style={{ fontSize: '12px', color: '#8E8E93', marginBottom: '4px' }}>Total Occupants</div>
                    <div style={{ fontSize: '16px' }}>{existingMember.total_occupants}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: '#8E8E93', marginBottom: '4px' }}>Move-In Date</div>
                    <div style={{ fontSize: '16px' }}>
                      {new Date(existingMember.move_in_date).toLocaleDateString()}
                    </div>
                  </div>
                  {existingMember.move_out_date && (
                    <div>
                      <div style={{ fontSize: '12px', color: '#8E8E93', marginBottom: '4px' }}>Move-Out Date</div>
                      <div style={{ fontSize: '16px' }}>
                        {new Date(existingMember.move_out_date).toLocaleDateString()}
                      </div>
                    </div>
                  )}
                  <div>
                    <div style={{ fontSize: '12px', color: '#8E8E93', marginBottom: '4px' }}>Status</div>
                    <div style={{
                      display: 'inline-block',
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '600',
                      backgroundColor: existingMember.status === 'active' ? '#34C75920' : '#8E8E9320',
                      color: existingMember.status === 'active' ? '#34C759' : '#8E8E93',
                      textTransform: 'uppercase',
                    }}>
                      {existingMember.status}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button
                onClick={() => {
                  setSelectedFlat(null);
                  setExistingMember(null);
                  setShowFlatPicker(true);
                }}
                style={{
                  flex: 1,
                  padding: '12px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  backgroundColor: '#fff',
                  color: '#666',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Select Different Flat
              </button>
              <button
                onClick={onClose}
                className="login-button"
                style={{ flex: 1 }}
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {/* Flat Selection */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                Select Flat *
              </label>
              <button
                type="button"
                onClick={() => setShowFlatPicker(true)}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  backgroundColor: '#fff',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: '14px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                {selectedFlat ? (
                  <span>
                    Flat {selectedFlat.flat_number} - {selectedFlat.area_sqft} sq ft
                    {selectedFlat.bedrooms && ` • ${selectedFlat.bedrooms} BR`}
                  </span>
                ) : (
                  <span style={{ color: '#8E8E93' }}>Tap to select a flat</span>
                )}
                <span>▼</span>
              </button>
            </div>

            {/* Member Details */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                Full Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                Phone Number *
              </label>
              <input
                type="tel"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                required
                maxLength={15}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                Email Address *
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                Member Type *
              </label>
              <div style={{ display: 'flex', gap: '12px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    value="owner"
                    checked={formData.member_type === 'owner'}
                    onChange={(e) => setFormData({ ...formData, member_type: e.target.value })}
                  />
                  <span>Owner</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    value="tenant"
                    checked={formData.member_type === 'tenant'}
                    onChange={(e) => setFormData({ ...formData, member_type: e.target.value })}
                  />
                  <span>Tenant</span>
                </label>
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                Occupation (Optional)
              </label>
              <input
                type="text"
                value={formData.occupation}
                onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                placeholder="e.g., Employed, Business, Professional"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                Move-In Date * (YYYY-MM-DD)
              </label>
              <input
                type="text"
                value={formData.move_in_date}
                onChange={(e) => setFormData({ ...formData, move_in_date: e.target.value })}
                placeholder="2024-01-15"
                required
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
                Total Occupants *
              </label>
              <input
                type="number"
                value={formData.total_occupants}
                onChange={(e) => setFormData({ ...formData, total_occupants: e.target.value })}
                required
                min="1"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  fontSize: '14px',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.is_mobile_public}
                  onChange={(e) => setFormData({ ...formData, is_mobile_public: e.target.checked })}
                />
                <span style={{ fontSize: '14px' }}>Make mobile number visible to other members</span>
              </label>
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button
                type="button"
                onClick={onClose}
                style={{
                  flex: 1,
                  padding: '12px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  backgroundColor: '#fff',
                  color: '#666',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="login-button"
                style={{ flex: 1, opacity: saving ? 0.6 : 1, cursor: saving ? 'not-allowed' : 'pointer' }}
              >
                {saving ? 'Onboarding...' : 'Onboard Member'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Flat Picker Modal */}
      {showFlatPicker && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1001,
          padding: '20px',
        }}>
          <div style={{
            background: '#fff',
            borderRadius: '12px',
            padding: '24px',
            maxWidth: '500px',
            width: '100%',
            maxHeight: '80vh',
            overflow: 'auto',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '20px', fontWeight: '600', margin: 0 }}>Select Flat</h3>
              <button
                onClick={() => setShowFlatPicker(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#8E8E93',
                }}
              >
                ×
              </button>
            </div>

            {loadingFlats ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>Loading flats...</div>
            ) : flats.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🏠</div>
                <div>No flats available. Please add flats first.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {flats.map((flat) => (
                  <button
                    key={flat.id}
                    onClick={() => {
                      // Check if flat already has an active member
                      const member = checkExistingMember(flat);

                      if (member) {
                        // Flat already has complete member data - show read-only view
                        setSelectedFlat(flat);
                        setExistingMember(member);
                        setShowFlatPicker(false);
                      } else {
                        // No member exists - show onboarding form with auto-filled data
                        setSelectedFlat(flat);
                        setExistingMember(null);
                        setFormData((prev) => {
                          // Derive default member type from occupancy status if available
                          let derivedMemberType = prev.member_type;
                          if (flat.occupancy_status) {
                            if (flat.occupancy_status === 'OWNER_OCCUPIED') {
                              derivedMemberType = 'owner';
                            } else if (flat.occupancy_status === 'TENANT_OCCUPIED') {
                              derivedMemberType = 'tenant';
                            }
                          }

                          return {
                            ...prev,
                            // Pre-fill core identity from flat owner data
                            name: flat.owner_name || prev.name,
                            phone_number: flat.owner_phone || prev.phone_number,
                            email: flat.owner_email || prev.email,
                            // If occupants already captured for the flat, use that as default
                            total_occupants:
                              flat.occupants && String(flat.occupants) !== '0'
                                ? String(flat.occupants)
                                : prev.total_occupants,
                            // Set sensible defaults where user shouldn't need to type again
                            member_type: derivedMemberType,
                            // Default move-in date if not already chosen (backend uses YYYY-MM-DD)
                            move_in_date: prev.move_in_date || '2025-12-01',
                          };
                        });
                        setShowFlatPicker(false);
                      }
                    }}
                    style={{
                      padding: '16px',
                      borderRadius: '8px',
                      border: selectedFlat?.id === flat.id ? '2px solid #007AFF' : '1px solid #ddd',
                      backgroundColor: selectedFlat?.id === flat.id ? '#E3F2FD' : '#fff',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                          <div style={{ fontSize: '16px', fontWeight: '600' }}>
                            Flat {flat.flat_number}
                          </div>
                          {checkExistingMember(flat) && (
                            <span style={{
                              fontSize: '11px',
                              padding: '2px 8px',
                              borderRadius: '10px',
                              backgroundColor: '#E8F5E9',
                              color: '#2E7D32',
                              fontWeight: '600'
                            }}>
                              ✓ Member Exists
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '14px', color: '#666', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                          <span>📐 {flat.area_sqft} sq ft</span>
                          {flat.bedrooms && <span>🛏️ {flat.bedrooms} BR</span>}
                          {flat.owner_name && <span>👤 {flat.owner_name}</span>}
                        </div>
                      </div>
                      {selectedFlat?.id === flat.id && (
                        <span style={{ color: '#007AFF', fontSize: '20px' }}>✓</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MembersScreen;

