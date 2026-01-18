import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const AddAssetScreen = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [assetAccounts, setAssetAccounts] = useState([]);

    const [formData, setFormData] = useState({
        name: '',
        category: 'lift',
        account_code: '1500',
        quantity: 1,
        location: '',
        status: 'Active',
        acquisition_type: 'builder_handover',
        handover_date: new Date().toISOString().split('T')[0],
        purchase_date: '',
        original_cost: '',
        depreciation_method: 'straight_line',
        depreciation_rate: '10',
        useful_life_years: '10',
        residual_value: '1',
        amc_vendor: '',
        amc_expiry: '',
        insurance_policy_no: '',
        insurance_expiry: '',
        vendor_name: '',
        invoice_no: '',
        notes: ''
    });

    useEffect(() => {
        const fetchAccounts = async () => {
            try {
                const response = await api.get('/accounting/accounts?type=asset');
                // Filter for specific asset categories if possible, or just show all assets
                setAssetAccounts(response.data.filter(a => a.code.startsWith('15')) || []);
            } catch (err) {
                console.error('Error fetching asset accounts:', err);
            }
        };
        fetchAccounts();
    }, []);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const payload = {
                ...formData,
                original_cost: parseFloat(formData.original_cost) || 0,
                depreciation_rate: parseFloat(formData.depreciation_rate),
                useful_life_years: parseInt(formData.useful_life_years),
                residual_value: parseFloat(formData.residual_value),
                quantity: parseInt(formData.quantity)
            };

            // Clean up dates based on acquisition type
            if (formData.acquisition_type === 'builder_handover') {
                payload.purchase_date = null;
                payload.vendor_name = null;
                payload.invoice_no = null;
            } else {
                payload.handover_date = null;
            }

            await api.post('/assets/', payload);
            navigate('/assets');
        } catch (err) {
            console.error('Error creating asset:', err);
            setError(err.response?.data?.detail || 'Failed to create asset. Please check all fields.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="dashboard-container">
            <div className="screen-header">
                <div>
                    <h1 className="screen-title">Add Society Asset</h1>
                    <p className="screen-subtitle">Register new common property or equipment</p>
                </div>
                <button className="btn btn-secondary" onClick={() => navigate('/assets')}>
                    Cancel
                </button>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <form onSubmit={handleSubmit}>
                {/* Section 1: Asset Identity */}
                <div className="card" style={{ marginBottom: '20px' }}>
                    <div className="card-header">
                        <h4 className="card-title">🧩 Section 1 — Asset Identity</h4>
                    </div>
                    <div className="card-body">
                        <div className="form-grid">
                            <div className="form-group">
                                <label className="form-label">Asset Name*</label>
                                <input
                                    type="text"
                                    name="name"
                                    className="form-input"
                                    placeholder="e.g. Lift - Tower A"
                                    value={formData.name}
                                    onChange={handleChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Category*</label>
                                <select name="category" className="form-input" value={formData.category} onChange={handleChange}>
                                    <option value="lift">Lift</option>
                                    <option value="electrical">Electrical</option>
                                    <option value="plumbing">Plumbing</option>
                                    <option value="furniture">Furniture</option>
                                    <option value="equipment">Equipment</option>
                                    <option value="infrastructure">Infrastructure</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Quantity</label>
                                <input
                                    type="number"
                                    name="quantity"
                                    className="form-input"
                                    value={formData.quantity}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Location</label>
                                <input
                                    type="text"
                                    name="location"
                                    className="form-input"
                                    placeholder="e.g. Basement, Tower B"
                                    value={formData.location}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Section 2: Asset Source */}
                <div className="card" style={{ marginBottom: '20px' }}>
                    <div className="card-header">
                        <h4 className="card-title">🧩 Section 2 — Asset Source</h4>
                    </div>
                    <div className="card-body">
                        <div className="form-group">
                            <label className="form-label" style={{ display: 'block', marginBottom: '10px' }}>How was this asset acquired?*</label>
                            <div style={{ display: 'flex', gap: '20px' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                    <input
                                        type="radio"
                                        name="acquisition_type"
                                        value="builder_handover"
                                        checked={formData.acquisition_type === 'builder_handover'}
                                        onChange={handleChange}
                                    />
                                    From Builder at Society Formation
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                                    <input
                                        type="radio"
                                        name="acquisition_type"
                                        value="society_purchase"
                                        checked={formData.acquisition_type === 'society_purchase'}
                                        onChange={handleChange}
                                    />
                                    Purchased by Society
                                </label>
                            </div>
                        </div>

                        <div className="form-grid" style={{ marginTop: '20px' }}>
                            {formData.acquisition_type === 'builder_handover' ? (
                                <>
                                    <div className="form-group">
                                        <label className="form-label">Handover Date*</label>
                                        <input
                                            type="date"
                                            name="handover_date"
                                            className="form-input"
                                            value={formData.handover_date}
                                            onChange={handleChange}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Value at Handover*</label>
                                        <input
                                            type="number"
                                            name="original_cost"
                                            className="form-input"
                                            placeholder="₹"
                                            value={formData.original_cost}
                                            onChange={handleChange}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Credit Account (Offset)</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            value="Corpus Fund (3010)"
                                            disabled
                                            style={{ backgroundColor: '#f0f0f0' }}
                                        />
                                        <small className="form-help">Builder assets post a credit to the Corpus Fund automatically.</small>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="form-group">
                                        <label className="form-label">Purchase Date*</label>
                                        <input
                                            type="date"
                                            name="purchase_date"
                                            className="form-input"
                                            value={formData.purchase_date}
                                            onChange={handleChange}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Purchase Cost*</label>
                                        <input
                                            type="number"
                                            name="original_cost"
                                            className="form-input"
                                            placeholder="₹"
                                            value={formData.original_cost}
                                            onChange={handleChange}
                                            required
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Vendor Name</label>
                                        <input
                                            type="text"
                                            name="vendor_name"
                                            className="form-input"
                                            value={formData.vendor_name}
                                            onChange={handleChange}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Invoice No.</label>
                                        <input
                                            type="text"
                                            name="invoice_no"
                                            className="form-input"
                                            value={formData.invoice_no}
                                            onChange={handleChange}
                                        />
                                    </div>
                                </>
                            )}

                            <div className="form-group">
                                <label className="form-label">Asset Account Code*</label>
                                <select name="account_code" className="form-input" value={formData.account_code} onChange={handleChange} required>
                                    {assetAccounts.map(acc => (
                                        <option key={acc.code} value={acc.code}>{acc.code} - {acc.name}</option>
                                    ))}
                                    {assetAccounts.length === 0 && <option value="1500">1500 - Common Area Assets</option>}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Section 3: Financials */}
                <div className="card" style={{ marginBottom: '20px' }}>
                    <div className="card-header">
                        <h4 className="card-title">🧩 Section 3 — Financials (Depreciation)</h4>
                    </div>
                    <div className="card-body">
                        <div className="form-grid">
                            <div className="form-group">
                                <label className="form-label">Depreciation Method*</label>
                                <select name="depreciation_method" className="form-input" value={formData.depreciation_method} onChange={handleChange}>
                                    <option value="straight_line">Straight Line Method</option>
                                    <option value="written_down_value">Written Down Value (WDV)</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Depreciation Rate (%)*</label>
                                <input
                                    type="number"
                                    name="depreciation_rate"
                                    className="form-input"
                                    value={formData.depreciation_rate}
                                    onChange={handleChange}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Useful Life (Years)</label>
                                <input
                                    type="number"
                                    name="useful_life_years"
                                    className="form-input"
                                    value={formData.useful_life_years}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Residual Value (₹)</label>
                                <input
                                    type="number"
                                    name="residual_value"
                                    className="form-input"
                                    value={formData.residual_value}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Section 4: Maintenance & Insurance */}
                <div className="card" style={{ marginBottom: '20px' }}>
                    <div className="card-header">
                        <h4 className="card-title">🧩 Section 4 — Maintenance & Insurance</h4>
                    </div>
                    <div className="card-body">
                        <div className="form-grid">
                            <div className="form-group">
                                <label className="form-label">AMC Vendor</label>
                                <input
                                    type="text"
                                    name="amc_vendor"
                                    className="form-input"
                                    value={formData.amc_vendor}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">AMC End Date</label>
                                <input
                                    type="date"
                                    name="amc_expiry"
                                    className="form-input"
                                    value={formData.amc_expiry}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Insurance Policy No.</label>
                                <input
                                    type="text"
                                    name="insurance_policy_no"
                                    className="form-input"
                                    value={formData.insurance_policy_no}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Insurance Expiry</label>
                                <input
                                    type="date"
                                    name="insurance_expiry"
                                    className="form-input"
                                    value={formData.insurance_expiry}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>

                        <div className="form-group" style={{ marginTop: '15px' }}>
                            <label className="form-label">Additional Notes</label>
                            <textarea
                                name="notes"
                                className="form-input"
                                rows="3"
                                value={formData.notes}
                                onChange={handleChange}
                            ></textarea>
                        </div>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '15px', justifyContent: 'flex-end', marginBottom: '40px' }}>
                    <button type="button" className="btn btn-secondary" onClick={() => navigate('/assets')}>
                        Cancel
                    </button>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? 'Processing...' : '🧾 Save & Create Asset'}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default AddAssetScreen;
