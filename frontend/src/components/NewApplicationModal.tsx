import React, { useState } from 'react';
import { X, Send, Sparkles } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmitted: () => void;
}

export const NewApplicationModal: React.FC<Props> = ({ isOpen, onClose, onSubmitted }) => {
  const [formData, setFormData] = useState({
    borrower_name: 'Sarah Jenkins',
    borrower_email: 'sarah.j@example.com',
    loan_amount: '45000',
    annual_income: '115000',
    partner_id: 'partner_a',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/v1/applications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          borrower_name: formData.borrower_name,
          borrower_email: formData.borrower_email,
          loan_amount: parseFloat(formData.loan_amount),
          annual_income: parseFloat(formData.annual_income),
          partner_id: formData.partner_id,
          idempotency_key: `web_${Date.now()}`,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Submission failed');
      }

      onSubmitted();
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
    }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', padding: '28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={20} color="#3b82f6" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>New Loan Application</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ padding: '10px', backgroundColor: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.3)', borderRadius: '6px', color: '#f87171', fontSize: '0.85rem', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#9ca3af', marginBottom: '6px' }}>Borrower Full Name</label>
            <input
              type="text"
              required
              className="input-field"
              value={formData.borrower_name}
              onChange={(e) => setFormData({ ...formData, borrower_name: e.target.value })}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#9ca3af', marginBottom: '6px' }}>Email Address</label>
            <input
              type="email"
              required
              className="input-field"
              value={formData.borrower_email}
              onChange={(e) => setFormData({ ...formData, borrower_email: e.target.value })}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#9ca3af', marginBottom: '6px' }}>Loan Amount ($)</label>
              <input
                type="number"
                required
                className="input-field"
                value={formData.loan_amount}
                onChange={(e) => setFormData({ ...formData, loan_amount: e.target.value })}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: '#9ca3af', marginBottom: '6px' }}>Annual Income ($)</label>
              <input
                type="number"
                required
                className="input-field"
                value={formData.annual_income}
                onChange={(e) => setFormData({ ...formData, annual_income: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: '#9ca3af', marginBottom: '6px' }}>Lending Partner ID</label>
            <select
              className="input-field"
              value={formData.partner_id}
              onChange={(e) => setFormData({ ...formData, partner_id: e.target.value })}
            >
              <option value="partner_a">Partner A (Standard)</option>
              <option value="partner_b">Partner B (Conservative)</option>
              <option value="partner_c">Partner C (High Growth)</option>
            </select>
          </div>

          <button type="submit" disabled={loading} className="btn btn-primary" style={{ marginTop: '12px' }}>
            <Send size={16} />
            {loading ? 'Submitting to Saga...' : 'Submit Application'}
          </button>
        </form>
      </div>
    </div>
  );
};
