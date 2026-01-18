import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';

const AssetDetailScreen = () => {
    const { asset_id } = useParams();
    const navigate = useNavigate();
    const [asset, setAsset] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [scrapping, setScrapping] = useState(false);
    const [scrapReason, setScrapReason] = useState('');

    const fetchAsset = useCallback(async () => {
        try {
            setLoading(true);
            const response = await api.get(`/assets/${asset_id}`);
            setAsset(response.data);
            setError(null);
        } catch (err) {
            console.error('Error fetching asset:', err);
            setError('Failed to load asset details.');
        } finally {
            setLoading(false);
        }
    }, [asset_id]);

    useEffect(() => {
        fetchAsset();
    }, [fetchAsset]);

    const handleScrap = async () => {
        if (!scrapReason.trim()) {
            alert('Please provide a reason for scrapping.');
            return;
        }

        try {
            await api.post(`/assets/${asset_id}/scrap?scrapping_reason=${encodeURIComponent(scrapReason)}`, {});
            setScrapping(false);
            fetchAsset();
        } catch (err) {
            console.error('Error scrapping asset:', err);
            alert('Failed to scrap asset.');
        }
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(amount);
    };

    const calculateWDV = () => {
        if (!asset) return 0;
        // Simple SLM WDV calculation for display
        if (asset.depreciation_method === 'straight_line') {
            const cost = parseFloat(asset.original_cost);
            const rate = parseFloat(asset.depreciation_rate) / 100;
            const acqDate = new Date(asset.purchase_date || asset.handover_date);
            const today = new Date();
            const yearsPassed = (today - acqDate) / (1000 * 60 * 60 * 24 * 365);
            if (yearsPassed <= 0) return cost;
            const totalDep = cost * rate * yearsPassed;
            const wdv = Math.max(parseFloat(asset.residual_value), cost - totalDep);
            return wdv;
        }
        return asset.original_cost; // Fallback
    };

    if (loading) return <div className="loading-container"><div className="loading-spinner"></div></div>;
    if (!asset) return <div className="dashboard-container"><div className="alert alert-danger">Asset not found</div></div>;

    return (
        <div className="dashboard-container">
            <div className="screen-header">
                <div>
                    <h1 className="screen-title">{asset.name}</h1>
                    <p className="screen-subtitle">Asset Code: {asset.asset_code}</p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="btn btn-secondary" onClick={() => navigate('/assets')}>
                        Back to Register
                    </button>
                    {!asset.is_scrapped && (
                        <button className="btn btn-danger" onClick={() => setScrapping(true)}>
                            Mark as Scrapped
                        </button>
                    )}
                </div>
            </div>

            <div className="dashboard-main-grid">
                <div className="asset-details-left">
                    {/* Section: Identity & Source */}
                    <div className="card" style={{ marginBottom: '20px' }}>
                        <div className="card-header">
                            <h3 className="card-title">Identity & Source</h3>
                        </div>
                        <div className="card-body">
                            <div className="detail-row">
                                <span className="detail-label">Category:</span>
                                <span className="detail-value" style={{ textTransform: 'capitalize' }}>{asset.category}</span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">Location:</span>
                                <span className="detail-value">{asset.location || 'Not Specified'}</span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">Acquisition:</span>
                                <span className="detail-value">
                                    {asset.acquisition_type === 'builder_handover' ? '🏗️ Builder Handover' : '💰 Society Purchase'}
                                </span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">Date:</span>
                                <span className="detail-value">
                                    {new Date(asset.purchase_date || asset.handover_date).toLocaleDateString()}
                                </span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">Status:</span>
                                <span className={`badge ${asset.is_scrapped ? 'badge-danger' : 'badge-success'}`}>
                                    {asset.status}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Section: Maintenance & AMC */}
                    <div className="card" style={{ marginBottom: '20px' }}>
                        <div className="card-header">
                            <h3 className="card-title">Maintenance & Insurance</h3>
                        </div>
                        <div className="card-body">
                            <div className="detail-row">
                                <span className="detail-label">AMC Vendor:</span>
                                <span className="detail-value">{asset.amc_vendor || 'None'}</span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">AMC Expiry:</span>
                                <span className="detail-value" style={{ color: asset.amc_expiry && new Date(asset.amc_expiry) < new Date() ? 'red' : 'inherit' }}>
                                    {asset.amc_expiry ? new Date(asset.amc_expiry).toLocaleDateString() : 'N/A'}
                                </span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">Insurance Policy:</span>
                                <span className="detail-value">{asset.insurance_policy_no || 'None'}</span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">Insurance Expiry:</span>
                                <span className="detail-value">
                                    {asset.insurance_expiry ? new Date(asset.insurance_expiry).toLocaleDateString() : 'N/A'}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="asset-details-right">
                    {/* Section: Financials */}
                    <div className="card" style={{ marginBottom: '20px', borderLeft: '4px solid #007AFF' }}>
                        <div className="card-header">
                            <h3 className="card-title">Financial Valuation</h3>
                        </div>
                        <div className="card-body">
                            <div className="financial-summary">
                                <div className="financial-item">
                                    <span className="financial-label">Original Cost</span>
                                    <div className="financial-value" style={{ fontSize: '24px', fontWeight: 'bold' }}>
                                        {formatCurrency(asset.original_cost)}
                                    </div>
                                </div>
                                <div className="financial-item" style={{ marginTop: '15px' }}>
                                    <span className="financial-label">Estimated Current Value (WDV)</span>
                                    <div className="financial-value" style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
                                        {formatCurrency(calculateWDV())}
                                    </div>
                                </div>
                            </div>
                            <hr style={{ margin: '20px 0', opacity: '0.1' }} />
                            <div className="detail-row">
                                <span className="detail-label">Depreciation Rate:</span>
                                <span className="detail-value">{asset.depreciation_rate}% ({asset.depreciation_method === 'straight_line' ? 'SLM' : 'WDV'})</span>
                            </div>
                            <div className="detail-row">
                                <span className="detail-label">Account Head:</span>
                                <span className="detail-value">{asset.account_code || '1500'}</span>
                            </div>
                        </div>
                    </div>

                    {/* Section: Notes */}
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">Notes & History</h3>
                        </div>
                        <div className="card-body">
                            <p style={{ whiteSpace: 'pre-wrap', color: '#666', fontSize: '14px' }}>
                                {asset.notes || 'No additional notes provided.'}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Scrapping Modal */}
            {scrapping && (
                <div className="modal-overlay">
                    <div className="modal-card">
                        <h3 className="modal-title">Confirm Asset Scrapping</h3>
                        <p className="modal-subtitle">This action is permanent for audit purposes and will mark the asset as inactive.</p>
                        <div className="form-group" style={{ marginTop: '20px' }}>
                            <label className="form-label">Reason for Scrapping*</label>
                            <textarea
                                className="form-input"
                                rows="3"
                                placeholder="e.g. Beyond economic repair, Tower replaced..."
                                value={scrapReason}
                                onChange={(e) => setScrapReason(e.target.value)}
                            />
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setScrapping(false)}>Cancel</button>
                            <button className="btn btn-danger" onClick={handleScrap}>Perform Scrapping</button>
                        </div>
                    </div>
                </div>
            )}

            <style dangerouslySetInnerHTML={{
                __html: `
        .asset-details-left { flex: 1; }
        .asset-details-right { flex: 1; }
        .detail-row { display: flex; justify-content: space-between; padding: 10px 0; border_bottom: 1px solid #f0f0f0; }
        .detail-row:last-child { border-bottom: none; }
        .detail-label { color: #888; font-size: 14px; }
        .detail-value { font-weight: 500; }
        .financial-label { color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .modal-card { background: white; padding: 30px; border-radius: 12px; width: 500px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .modal-title { margin-bottom: 10px; color: #dc3545; }
        .modal-footer { display: flex; gap: 15px; justify-content: flex-end; margin-top: 25px; }
      `}} />
        </div>
    );
};

export default AssetDetailScreen;
