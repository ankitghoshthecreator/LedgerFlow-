import React, { useEffect, useState } from 'react';
import { Application, ApplicationDetail } from './types';
import { NewApplicationModal } from './components/NewApplicationModal';
import { EventTimeline } from './components/EventTimeline';
import {
  Activity,
  Plus,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  ArrowRight,
  Database
} from 'lucide-react';

export const App: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [selectedApp, setSelectedApp] = useState<ApplicationDetail | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchApplications = async () => {
    try {
      const res = await fetch('/api/v1/applications');
      if (res.ok) {
        const data = await res.json();
        setApplications(data);
      }
    } catch (err) {
      console.error('Failed to fetch applications', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetail = async (appId: string) => {
    try {
      const res = await fetch(`/api/v1/applications/${appId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedApp(data);
      }
    } catch (err) {
      console.error('Failed to fetch app detail', err);
    }
  };

  useEffect(() => {
    fetchApplications();
    const interval = setInterval(fetchApplications, 3000);
    return () => clearInterval(interval);
  }, []);

  const filteredApps = applications.filter(
    (a) =>
      a.borrower_name.toLowerCase().includes(search.toLowerCase()) ||
      a.borrower_email.toLowerCase().includes(search.toLowerCase()) ||
      a.application_id.includes(search)
  );

  const approvedCount = applications.filter((a) => a.status === 'approved' || a.status === 'disbursal_completed').length;
  const rejectedCount = applications.filter((a) => a.status === 'rejected' || a.status === 'kyc_failed').length;
  const pendingCount = applications.length - approvedCount - rejectedCount;

  return (
    <div style={{ minHeight: '100vh', padding: '32px 48px', maxWidth: '1600px', margin: '0 auto' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
            <div style={{ padding: '8px', borderRadius: '10px', background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
              <Layers size={24} color="#fff" />
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em' }}>LedgerFlow</h1>
            <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(59,130,246,0.15)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.3)', fontFamily: 'var(--font-mono)' }}>
              v0.1.0-cqrs
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Event-Driven Loan Underwriting & Risk Engine • Saga Pattern Orchestrator
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            <div className="live-indicator" />
            <span>Event Bus Connected (CQRS)</span>
          </div>

          <button onClick={fetchApplications} className="btn" style={{ background: 'var(--bg-surface-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border-color)' }}>
            <RefreshCw size={16} />
            Refresh
          </button>

          <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
            <Plus size={16} />
            Submit Application
          </button>
        </div>
      </header>

      {/* Analytics KPI Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '32px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px' }}>
            <span>Total Applications</span>
            <Database size={18} color="#3b82f6" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700 }}>{applications.length}</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px' }}>
            <span>Approved & Disbursed</span>
            <CheckCircle2 size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#34d399' }}>{approvedCount}</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px' }}>
            <span>Rejected / Failed</span>
            <AlertCircle size={18} color="#f43f5e" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#f87171' }}>{rejectedCount}</div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px' }}>
            <span>In-Flight Sagas</span>
            <Activity size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#fbbf24' }}>{pendingCount}</div>
        </div>
      </div>

      {/* Main Grid: Applications Table + Detail Drawer */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedApp ? '1fr 480px' : '1fr', gap: '24px' }}>
        {/* Table Panel */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Active Borrower Sagas</h2>
            <div style={{ position: 'relative', width: '280px' }}>
              <Search size={16} color="#6b7280" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                placeholder="Search borrower or ID..."
                className="input-field"
                style={{ paddingLeft: '36px' }}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>

          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading application state...</div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '12px' }}>Borrower</th>
                  <th style={{ padding: '12px' }}>Loan Amount</th>
                  <th style={{ padding: '12px' }}>Partner</th>
                  <th style={{ padding: '12px' }}>Status</th>
                  <th style={{ padding: '12px' }}>Credit / DTI</th>
                  <th style={{ padding: '12px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredApps.map((app) => (
                  <tr
                    key={app.application_id}
                    onClick={() => fetchDetail(app.application_id)}
                    style={{
                      borderBottom: '1px solid var(--border-color)',
                      cursor: 'pointer',
                      backgroundColor: selectedApp?.application_id === app.application_id ? 'rgba(59,130,246,0.08)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '14px 12px' }}>
                      <div style={{ fontWeight: 600 }}>{app.borrower_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{app.borrower_email}</div>
                    </td>
                    <td style={{ padding: '14px 12px', fontWeight: 600 }}>${app.loan_amount.toLocaleString()}</td>
                    <td style={{ padding: '14px 12px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{app.partner_id}</td>
                    <td style={{ padding: '14px 12px' }}>
                      <span className={`badge badge-${app.status}`}>
                        {app.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td style={{ padding: '14px 12px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                      {app.credit_score ? `${app.credit_score} / ${(app.debt_to_income! * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td style={{ padding: '14px 12px' }}>
                      <button className="btn" style={{ padding: '4px 8px', fontSize: '0.75rem', background: 'var(--bg-surface-elevated)' }}>
                        Inspect <ArrowRight size={12} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Selected Application Timeline Drawer */}
        {selectedApp && (
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '14px' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{selectedApp.borrower_name}</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  ID: {selectedApp.application_id.slice(0, 18)}...
                </span>
              </div>
              <button onClick={() => setSelectedApp(null)} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.85rem' }}>
              <div style={{ background: 'var(--bg-surface-elevated)', padding: '10px', borderRadius: '6px' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Loan Amount</div>
                <div style={{ fontWeight: 600 }}>${selectedApp.loan_amount.toLocaleString()}</div>
              </div>
              <div style={{ background: 'var(--bg-surface-elevated)', padding: '10px', borderRadius: '6px' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Annual Income</div>
                <div style={{ fontWeight: 600 }}>${selectedApp.annual_income.toLocaleString()}</div>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Clock size={16} color="#3b82f6" /> Domain Event Stream
              </h4>
              <EventTimeline events={selectedApp.timeline || []} />
            </div>
          </div>
        )}
      </div>

      <NewApplicationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmitted={fetchApplications}
      />
    </div>
  );
};
