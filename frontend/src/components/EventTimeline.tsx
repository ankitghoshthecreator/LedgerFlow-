import React from 'react';
import { DomainEventItem } from '../types';
import { CheckCircle2, Clock, AlertTriangle, ShieldCheck, CreditCard, DollarSign } from 'lucide-react';

interface Props {
  events: DomainEventItem[];
}

export const EventTimeline: React.FC<Props> = ({ events }) => {
  const getIcon = (eventType: string) => {
    switch (eventType) {
      case 'application.submitted': return <Clock size={16} color="#60a5fa" />;
      case 'kyc.verified': return <ShieldCheck size={16} color="#34d399" />;
      case 'credit_score.fetched': return <CreditCard size={16} color="#a78bfa" />;
      case 'risk.scored': return <CheckCircle2 size={16} color="#f472b6" />;
      case 'decision.made': return <CheckCircle2 size={16} color="#34d399" />;
      case 'disbursal.initiated':
      case 'disbursal.completed': return <DollarSign size={16} color="#34d399" />;
      case 'kyc.failed':
      case 'application.rejected': return <AlertTriangle size={16} color="#f87171" />;
      default: return <Clock size={16} color="#9ca3af" />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {events.map((evt, idx) => (
        <div key={evt.event_id || idx} style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
          <div style={{
            padding: '8px',
            borderRadius: '50%',
            backgroundColor: 'rgba(255,255,255,0.05)',
            border: '1px solid var(--border-color)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            {getIcon(evt.event_type)}
          </div>
          <div style={{ flex: 1, backgroundColor: 'var(--bg-surface-elevated)', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                {evt.event_type}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {new Date(evt.occurred_at).toLocaleTimeString()}
              </span>
            </div>
            <pre style={{
              fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)',
              overflowX: 'auto', margin: 0, whiteSpace: 'pre-wrap'
            }}>
              {JSON.stringify(evt.payload, null, 2)}
            </pre>
          </div>
        </div>
      ))}
    </div>
  );
};
