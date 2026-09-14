import React from 'react';

/**
 * Standardized Button Component
 * Variants: coral (primary), secondary, ghost, emerald, rose
 */
export default function Button({
  children,
  variant = 'secondary',
  size = 'md',
  icon = null,
  onClick,
  disabled = false,
  className = '',
  style = {},
  title = '',
  type = 'button'
}) {
  const getVariantClass = () => {
    switch (variant) {
      case 'coral':
      case 'primary':
        return 'btn-coral';
      case 'emerald':
        return 'btn-emerald';
      case 'rose':
        return 'btn-rose';
      case 'ghost':
        return 'btn-ghost';
      case 'secondary':
      default:
        return 'btn-secondary';
    }
  };

  const getSizeStyle = () => {
    switch (size) {
      case 'sm':
        return { padding: '5px 10px', fontSize: '0.78rem' };
      case 'lg':
        return { padding: '12px 24px', fontSize: '0.95rem' };
      case 'md':
      default:
        return {};
    }
  };

  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) {
      return icon;
    }
    if (typeof icon === 'function' || (typeof icon === 'object' && icon !== null && 'render' in icon)) {
      const IconComponent = icon;
      return <IconComponent size={14} />;
    }
    return icon;
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      title={title}
      className={`${getVariantClass()} ${className}`}
      style={{
        opacity: disabled ? 0.6 : 1,
        pointerEvents: disabled ? 'none' : 'auto',
        ...getSizeStyle(),
        ...style
      }}
    >
      {icon && <span style={{ display: 'inline-flex', alignItems: 'center', marginRight: children ? '6px' : '0' }}>{renderIcon()}</span>}
      {children}
    </button>
  );
}
