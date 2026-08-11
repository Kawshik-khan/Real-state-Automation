import React from 'react';
import { Search, Bell, Activity, ShieldCheck } from 'lucide-react';

export default function Header({ activeTabTitle = "Dashboard Overview" }) {
  return (
    <header style={{
      height: '70px',
      borderBottom: '1px solid var(--border-glass)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
      background: 'rgba(11, 15, 25, 0.5)',
      backdropFilter: 'blur(16px)'
    }}>
      {/* Title */}
      <div>
        <h1 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-main)' }}>
          {activeTabTitle}
        </h1>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Real Estate AI Automation & Knowledge Operations Platform
        </p>
      </div>

      {/* Center Search & Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ position: 'relative' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search leads, projects, documents..."
            className="glass-input"
            style={{ paddingLeft: '36px', width: '280px', fontSize: '0.85rem' }}
          />
        </div>

        {/* Telemetry Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 12px',
          borderRadius: '8px',
          background: 'rgba(16, 185, 129, 0.1)',
          color: '#34D399'
        }}>
          <Activity size={14} color="#34D399" />
          <span>Pinecone RAG &amp; pgvector Active</span>
        </div>

        <button className="glass-card" style={{ padding: '8px', borderRadius: '10px', color: 'var(--text-muted)', cursor: 'pointer' }}>
          <Bell size={18} />
        </button>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '4px 12px',
          borderRadius: '20px',
          background: 'rgba(139, 92, 246, 0.15)',
          border: '1px solid rgba(139, 92, 246, 0.3)'
        }}>
          <ShieldCheck size={16} color="#C084FC" />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#FFFFFF' }}>Admin Lead</span>
        </div>
      </div>
    </header>
  );
}
