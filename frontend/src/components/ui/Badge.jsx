import React from 'react';

/**
 * Standardized Semantic Badge Component
 * Variants: coral, emerald, amber, rose, cyan, blue, neutral
 */
export default function Badge({ 
  children, 
  variant = 'neutral', 
  pulse = false, 
  icon = null,
  style = {} 
}) {
  return (
    <span className={`badge badge-${variant}`} style={style}>
      {pulse && <span className="pulse-online" style={{ marginRight: '4px' }} />}
      {icon && <span style={{ display: 'inline-flex', alignItems: 'center' }}>{icon}</span>}
      {children}
    </span>
  );
}
