import React from 'react';
import { Search, Bell, Activity, ShieldCheck, LogOut, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Header({ activeTabTitle = "Dashboard Overview" }) {
  const { user, logout } = useAuth();

  const getRoleBadgeStyle = (role) => {
    switch (role) {
      case 'admin':
        return { bg: 'rgba(139, 92, 246, 0.2)', border: '1px solid rgba(139, 92, 246, 0.4)', color: '#C084FC', label: '👑 Admin' };
      case 'manager':
        return { bg: 'rgba(59, 130, 246, 0.2)', border: '1px solid rgba(59, 130, 246, 0.4)', color: '#60A5FA', label: '👔 Manager' };
      case 'agent':
        return { bg: 'rgba(16, 185, 129, 0.2)', border: '1px solid rgba(16, 185, 129, 0.4)', color: '#34D399', label: '🎧 Agent' };
      default:
        return { bg: 'rgba(156, 163, 175, 0.2)', border: '1px solid rgba(156, 163, 175, 0.4)', color: '#9CA3AF', label: '👁️ Viewer' };
    }
  };

  const badgeStyle = getRoleBadgeStyle(user?.role);

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
          Real Estate AI Automation &amp; Knowledge Operations Platform
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
            style={{ paddingLeft: '36px', width: '240px', fontSize: '0.85rem' }}
          />
        </div>

        {/* Telemetry Indicator (Admin Only) */}
        {user?.role === 'admin' && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: '8px',
            background: 'rgba(16, 185, 129, 0.1)',
            color: '#34D399',
            fontSize: '0.8rem'
          }}>
            <Activity size={14} color="#34D399" />
            <span>Pinecone RAG Active</span>
          </div>
        )}

        <button className="glass-card" style={{ padding: '8px', borderRadius: '10px', color: 'var(--text-muted)', cursor: 'pointer' }}>
          <Bell size={18} />
        </button>

        {/* Logged in User Profile & Role Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '4px 14px',
          borderRadius: '20px',
          background: badgeStyle.bg,
          border: badgeStyle.border
        }}>
          <User size={16} color={badgeStyle.color} />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#FFFFFF', lineHeight: 1.2 }}>
              {user?.full_name || 'System User'}
            </span>
            <span style={{ fontSize: '0.65rem', fontWeight: 600, color: badgeStyle.color }}>
              {badgeStyle.label}
            </span>
          </div>
        </div>

        {/* Logout Button */}
        <button
          onClick={logout}
          title="Sign Out"
          style={{
            padding: '8px 12px',
            borderRadius: '10px',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#F87171',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.8rem',
            fontWeight: 600,
            transition: 'all 0.2s ease'
          }}
        >
          <LogOut size={16} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
}
