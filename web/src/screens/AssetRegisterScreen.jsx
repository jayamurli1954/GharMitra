import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { authService } from '../services/authService';

const AssetRegisterScreen = () => {
    const navigate = useNavigate();
    const [assets, setAssets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchAssets = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.get('/assets/');
            setAssets(response.data);
            setError(null);
        } catch (err) {
            console.error('Error fetching assets:', err);
            setError('Failed to load asset register. Please try again.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAssets();
    }, [fetchAssets]);

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(amount);
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'active': return '#28a745';
            case 'under maintenance': return '#ffc107';
            case 'scrapped': return '#dc3545';
            default: return '#6c757d';
        }
    };

    if (loading) return <div className="loading-container"><div className="loading-spinner"></div></div>;

    return (
        <div className="dashboard-container">
            <div className="screen-header">
                <div>
                    <h1 className="screen-title">Asset Register</h1>
                    <p className="screen-subtitle">Complete record of society assets and common property</p>
                </div>
                <button
                    className="btn btn-primary"
                    onClick={() => navigate('/assets/add')}
                >
                    + Add New Asset
                </button>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <div className="card" style={{ marginTop: '20px', overflowX: 'auto' }}>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Code</th>
                            <th>Asset Name</th>
                            <th>Category</th>
                            <th>Location</th>
                            <th>Original Cost</th>
                            <th>Acquisition</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {assets.length === 0 ? (
                            <tr>
                                <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                                    No assets recorded yet. Start by adding a society asset.
                                </td>
                            </tr>
                        ) : (
                            assets.map((asset) => (
                                <tr key={asset.id} onClick={() => navigate(`/assets/${asset.id}`)} style={{ cursor: 'pointer' }}>
                                    <td className="font-mono">{asset.asset_code}</td>
                                    <td style={{ fontWeight: '500' }}>{asset.name}</td>
                                    <td style={{ textTransform: 'capitalize' }}>{asset.category}</td>
                                    <td>{asset.location}</td>
                                    <td>{formatCurrency(asset.original_cost)}</td>
                                    <td style={{ fontSize: '12px' }}>
                                        {asset.acquisition_type === 'builder_handover' ? 'Builder Handover' : 'Society Purchase'}
                                    </td>
                                    <td>
                                        <span
                                            className="badge"
                                            style={{
                                                backgroundColor: getStatusColor(asset.status) + '20',
                                                color: getStatusColor(asset.status),
                                                border: `1px solid ${getStatusColor(asset.status)}40`
                                            }}
                                        >
                                            {asset.status}
                                        </span>
                                    </td>
                                    <td>
                                        <button
                                            className="btn-icon"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                navigate(`/assets/${asset.id}`);
                                            }}
                                        >
                                            👁️
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div className="info-box" style={{ marginTop: '20px', backgroundColor: '#e8f4fd' }}>
                <h4 style={{ color: '#0056b3', marginBottom: '10px' }}>💡 Audit Tip</h4>
                <p style={{ fontSize: '14px', color: '#444' }}>
                    GharMitra ensures that all builder-handed-over assets are automatically balanced against the <strong>Corpus Fund</strong>.
                    For purchased assets, ensure you have a corresponding Payment Voucher for audit trail.
                </p>
            </div>
        </div>
    );
};

export default AssetRegisterScreen;
