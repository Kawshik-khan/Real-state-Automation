import React, { useState } from 'react';
import { X, Check, Eye, EyeOff, RotateCcw } from 'lucide-react';
import Button from '../ui/Button';

export default function EditModulesModal({ 
  isOpen, 
  onClose, 
  moduleConfig, 
  onSaveConfig, 
  onResetDefault 
}) {
  if (!isOpen) return null;

  const [localConfig, setLocalConfig] = useState({ ...moduleConfig });

  const modulesList = [
    { id: 'kpis', label: '5-Card Metric Strip', desc: 'Top operational KPIs (Properties, Pipeline, Leads, AI Rate, Hot Leads)' },
    { id: 'chart', label: 'Monthly AI Engagement Chart', desc: '6-month message throughput bar chart with summary metrics' },
    { id: 'map', label: 'Lead Acquisition & Channel Attribution', desc: 'Interactive donut breakdown of inquiries across WhatsApp, Meta Ads, Instagram, Web, and YouTube' },
    { id: 'criticalDates', label: 'Critical Dates & Milestones', desc: 'Upcoming site tours, contract renewals, and HITL approvals' },
    { id: 'valuableProps', label: 'Most Valuable Properties', desc: 'Ranked portfolio sites by market valuation in BDT' },
    { id: 'financialSummary', label: 'Financial & Deal Velocity', desc: 'Annual rental targets, automation cost savings, and commission pace' }
  ];

  const handleToggle = (id) => {
    setLocalConfig(prev => {
      const nextVal = !prev[id];
      const updated = { ...prev, [id]: nextVal };
      if (id === 'map') updated.channelDonut = nextVal;
      if (id === 'channelDonut') updated.map = nextVal;
      return updated;
    });
  };

  const handleSave = () => {
    onSaveConfig(localConfig);
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.55)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '540px',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-glass)',
        boxShadow: 'var(--shadow-dropdown)',
        borderRadius: '16px',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Modal Header */}
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid var(--border-glass)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '-0.01em' }}>
              Customize Dashboard Modules
            </h3>
            <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Configure and show/hide widgets based on your operational focus
            </p>
          </div>
          <button
            onClick={onClose}
            className="btn-secondary"
            style={{ padding: '6px', borderRadius: '8px', border: 'none' }}
          >
            <X size={18} color="var(--text-muted)" />
          </button>
        </div>

        {/* Modal Body: Modules Toggles */}
        <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {modulesList.map((m) => {
            const isEnabled = localConfig[m.id] !== false;
            return (
              <div
                key={m.id}
                onClick={() => handleToggle(m.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  background: isEnabled ? 'var(--bg-card-hover)' : 'transparent',
                  border: isEnabled ? '1px solid var(--border-glass-hover)' : '1px solid var(--border-glass)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ flex: 1, paddingRight: '12px' }}>
                  <span style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-main)' }}>
                    {m.label}
                  </span>
                  <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    {m.desc}
                  </p>
                </div>

                {/* Toggle Switch Pill */}
                <div style={{
                  width: '42px',
                  height: '24px',
                  borderRadius: '12px',
                  background: isEnabled ? 'var(--primary-coral)' : 'var(--border-glass)',
                  padding: '2px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: isEnabled ? 'flex-end' : 'flex-start',
                  transition: 'background 0.2s ease',
                  flexShrink: 0
                }}>
                  <div style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    background: 'var(--bg-card)',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
                  }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Modal Footer */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid var(--border-glass)',
          background: 'var(--bg-card-hover)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <button
            onClick={() => {
              if (onResetDefault) onResetDefault();
              onClose();
            }}
            className="btn-secondary"
            style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RotateCcw size={14} />
            <span>Reset to Default</span>
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Button variant="secondary" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="coral" size="sm" onClick={handleSave}>
              Save Layout
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
