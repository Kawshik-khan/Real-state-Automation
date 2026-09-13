import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

export const CustomDropdown = ({
  value,
  onChange,
  options = [],
  placeholder = 'Select option...',
  icon = null,
  minWidth = '160px',
  style = {},
  buttonStyle = {},
  menuStyle = {},
  ariaLabel = 'Dropdown'
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on Esc key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen]);

  const selectedOption = options.find((opt) => opt.value === value);

  return (
    <div
      ref={dropdownRef}
      style={{
        position: 'relative',
        display: 'inline-block',
        minWidth: minWidth,
        zIndex: isOpen ? 60 : 1,
        ...style
      }}
    >
      {/* Trigger Button */}
      <button
        type="button"
        aria-label={ariaLabel}
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          padding: '6px 12px',
          borderRadius: '8px',
          background: 'var(--bg-card)',
          border: isOpen ? '1px solid var(--accent-coral)' : '1px solid var(--border-glass)',
          boxShadow: isOpen ? '0 0 0 2px rgba(232, 101, 74, 0.15)' : 'none',
          color: 'var(--text-main)',
          fontSize: '0.76rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px',
          cursor: 'pointer',
          transition: 'all 0.15s ease',
          outline: 'none',
          whiteSpace: 'nowrap',
          ...buttonStyle
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden' }}>
          {selectedOption?.icon ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', flexShrink: 0 }}>
              {selectedOption.icon}
            </span>
          ) : icon ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', flexShrink: 0 }}>
              {icon}
            </span>
          ) : null}
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {selectedOption?.label || placeholder}
          </span>
        </div>

        <ChevronDown
          size={14}
          color="var(--text-muted)"
          style={{
            flexShrink: 0,
            transition: 'transform 0.2s ease',
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)'
          }}
        />
      </button>

      {/* Floating Dropdown Menu Panel */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 4px)',
            left: 0,
            minWidth: '100%',
            width: 'max-content',
            maxWidth: '300px',
            background: 'var(--bg-dropdown, var(--bg-card))',
            backdropFilter: 'blur(16px)',
            border: '1px solid var(--border-glass)',
            borderRadius: '10px',
            boxShadow: 'var(--shadow-dropdown)',
            padding: '4px',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            gap: '2px',
            maxHeight: '260px',
            overflowY: 'auto',
            animation: 'fadeIn 0.12s ease',
            ...menuStyle
          }}
        >
          {options.map((opt) => {
            const isSelected = opt.value === value;
            return (
              <div
                key={opt.value}
                onClick={() => {
                  onChange(opt.value);
                  setIsOpen(false);
                }}
                style={{
                  padding: '7px 10px',
                  borderRadius: '6px',
                  fontSize: '0.76rem',
                  fontWeight: isSelected ? 700 : 500,
                  color: isSelected ? 'var(--accent-coral)' : 'var(--text-main)',
                  background: isSelected ? 'rgba(232, 101, 74, 0.12)' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '8px',
                  cursor: 'pointer',
                  transition: 'background 0.12s ease, color 0.12s ease',
                  userSelect: 'none'
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = 'var(--bg-card-hover)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {opt.icon && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', flexShrink: 0 }}>
                      {opt.icon}
                    </span>
                  )}
                  <span>{opt.label}</span>
                </div>

                {isSelected && (
                  <Check size={13} color="var(--accent-coral)" style={{ flexShrink: 0 }} />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default CustomDropdown;
