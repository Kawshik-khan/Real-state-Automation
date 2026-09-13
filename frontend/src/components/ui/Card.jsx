import React from 'react';

/**
 * Standardized Dashboard Card Container
 * Used across the FAANG-level redesigned dashboard.
 */
export default function Card({ 
  children, 
  title, 
  subtitle, 
  action, 
  footer, 
  className = '', 
  style = {},
  noPadding = false 
}) {
  return (
    <div 
      className={`dashboard-card ${className}`} 
      style={{
        display: 'flex',
        flexDirection: 'column',
        ...style
      }}
    >
      {(title || action) && (
        <div style={{
          padding: '18px 22px 14px 22px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border-glass)'
        }}>
          <div>
            {title && (
              <h3 style={{
                fontSize: '1.05rem',
                fontWeight: 700,
                color: 'var(--text-main)',
                letterSpacing: '-0.01em',
                lineHeight: 1.2
              }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <p style={{
                fontSize: '0.78rem',
                color: 'var(--text-muted)',
                marginTop: '4px'
              }}>
                {subtitle}
              </p>
            )}
          </div>
          {action && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {action}
            </div>
          )}
        </div>
      )}

      <div style={{
        padding: noPadding ? '0' : '20px 22px',
        flex: 1,
        display: 'flex',
        flexDirection: 'column'
      }}>
        {children}
      </div>

      {footer && (
        <div style={{
          padding: '12px 22px',
          borderTop: '1px solid var(--border-glass)',
          background: 'var(--bg-card-hover)',
          borderBottomLeftRadius: '16px',
          borderBottomRightRadius: '16px'
        }}>
          {footer}
        </div>
      )}
    </div>
  );
}
