import React from 'react';
import { Clock, ShieldAlert, LogOut, CheckCircle2 } from 'lucide-react';

/**
 * Enterprise Inactivity Grace Warning Modal.
 * Prompts the user before automatic session termination.
 */
export default function IdleSessionModal({
  isOpen,
  remainingSeconds,
  onStayLoggedIn,
  onLogout,
}) {
  if (!isOpen) return null;

  const pct = Math.max(0, Math.min(100, Math.round((remainingSeconds / 60) * 100)));

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="idle-modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(10, 15, 29, 0.78)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        animation: 'fadeIn 0.2s ease-out',
      }}
    >
      <div
        className="glass-card"
        style={{
          width: '100%',
          maxWidth: '460px',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid rgba(232, 101, 74, 0.35)',
          borderRadius: '20px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5), 0 0 25px rgba(232, 101, 74, 0.15)',
          padding: '32px 28px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: '18px',
        }}
      >
        {/* Pulsing Warning Icon */}
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '18px',
            background: 'rgba(232, 101, 74, 0.12)',
            border: '1px solid rgba(232, 101, 74, 0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 24px rgba(232, 101, 74, 0.2)',
          }}
        >
          <Clock size={32} color="var(--accent-coral)" />
        </div>

        <div>
          <h3
            id="idle-modal-title"
            style={{
              margin: '0 0 8px 0',
              fontSize: '1.25rem',
              fontWeight: 800,
              color: 'var(--text-main)',
              letterSpacing: '-0.02em',
            }}
          >
            Session Inactivity Warning
          </h3>
          <p
            style={{
              margin: 0,
              fontSize: '0.86rem',
              color: 'var(--text-muted)',
              lineHeight: 1.5,
            }}
          >
            To protect confidential property records and client inquiries, your session will automatically close due to inactivity.
          </p>
        </div>

        {/* Countdown Banner */}
        <div
          style={{
            width: '100%',
            padding: '14px 18px',
            borderRadius: '12px',
            background: 'var(--bg-main)',
            border: '1px solid var(--border-glass)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              AUTO LOGOUT IN
            </span>
            <span
              style={{
                fontSize: '1.15rem',
                fontWeight: 800,
                color: remainingSeconds <= 15 ? '#DC2626' : 'var(--accent-coral)',
                fontFamily: 'monospace',
              }}
            >
              {remainingSeconds}s
            </span>
          </div>

          {/* Progress Bar */}
          <div
            style={{
              height: '6px',
              borderRadius: '3px',
              background: 'rgba(0, 0, 0, 0.08)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${pct}%`,
                background: remainingSeconds <= 15 ? '#DC2626' : 'linear-gradient(90deg, #F59E0B 0%, var(--accent-coral) 100%)',
                transition: 'width 1s linear',
                borderRadius: '3px',
              }}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px', width: '100%', marginTop: '4px' }}>
          <button
            type="button"
            onClick={onLogout}
            style={{
              flex: 1,
              padding: '11px 16px',
              borderRadius: '10px',
              background: 'transparent',
              border: '1px solid var(--border-glass)',
              color: 'var(--text-muted)',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              transition: 'all 0.15s ease',
            }}
          >
            <LogOut size={16} />
            <span>Log Out</span>
          </button>

          <button
            type="button"
            onClick={onStayLoggedIn}
            style={{
              flex: 2,
              padding: '11px 20px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, var(--accent-coral) 0%, #D95338 100%)',
              border: 'none',
              color: '#FFFFFF',
              fontSize: '0.88rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(232, 101, 74, 0.35)',
              transition: 'all 0.2s ease',
            }}
          >
            <CheckCircle2 size={17} />
            <span>Stay Logged In</span>
          </button>
        </div>
      </div>
    </div>
  );
}
