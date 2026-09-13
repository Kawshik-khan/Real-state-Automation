import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

/**
 * Standardized Pagination Component
 * 
 * Props:
 * - currentPage: number (1-based)
 * - totalItems: number
 * - pageSize: number
 * - onPageChange: (newPage: number) => void
 * - onPageSizeChange?: (newSize: number) => void
 * - pageSizeOptions?: number[]
 * - itemLabel?: string (e.g. 'properties', 'conversations', 'documents')
 */
export default function Pagination({
  currentPage = 1,
  totalItems = 0,
  pageSize = 10,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [6, 12, 24],
  itemLabel = 'items',
  compact = false,
  style = {},
  className = ''
}) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(Math.max(1, currentPage), totalPages);

  const startItem = totalItems === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const endItem = Math.min(safePage * pageSize, totalItems);

  // Generate page numbers with ellipsis
  const getPageNumbers = () => {
    const pages = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (safePage > 3) {
        pages.push('...');
      }
      const start = Math.max(2, safePage - 1);
      const end = Math.min(totalPages - 1, safePage + 1);
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      if (safePage < totalPages - 2) {
        pages.push('...');
      }
      pages.push(totalPages);
    }
    return pages;
  };

  if (totalItems <= 0) {
    return null;
  }

  if (compact) {
    return (
      <div
        className={`pagination-compact ${className}`}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 12px',
          background: 'var(--bg-card, rgba(255, 255, 255, 0.75))',
          borderTop: '1px solid var(--border-glass, rgba(0, 0, 0, 0.08))',
          fontSize: '0.75rem',
          color: 'var(--text-muted, #6B7280)',
          ...style
        }}
      >
        <span>
          <strong>{startItem}–{endItem}</strong> of <strong>{totalItems}</strong>
        </span>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            type="button"
            onClick={() => onPageChange(safePage - 1)}
            disabled={safePage <= 1}
            title="Previous page"
            style={{
              padding: '4px 6px',
              borderRadius: '6px',
              border: '1px solid var(--border-glass, rgba(0,0,0,0.1))',
              background: safePage <= 1 ? 'transparent' : 'var(--bg-card, #FFFFFF)',
              color: safePage <= 1 ? 'var(--text-dim, #9CA3AF)' : 'var(--text-main, #111827)',
              cursor: safePage <= 1 ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: safePage <= 1 ? 0.4 : 1
            }}
          >
            <ChevronLeft size={14} />
          </button>

          <span style={{ padding: '0 6px', fontWeight: 700, color: 'var(--text-main, #111827)' }}>
            {safePage} / {totalPages}
          </span>

          <button
            type="button"
            onClick={() => onPageChange(safePage + 1)}
            disabled={safePage >= totalPages}
            title="Next page"
            style={{
              padding: '4px 6px',
              borderRadius: '6px',
              border: '1px solid var(--border-glass, rgba(0,0,0,0.1))',
              background: safePage >= totalPages ? 'transparent' : 'var(--bg-card, #FFFFFF)',
              color: safePage >= totalPages ? 'var(--text-dim, #9CA3AF)' : 'var(--text-main, #111827)',
              cursor: safePage >= totalPages ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              opacity: safePage >= totalPages ? 0.4 : 1
            }}
          >
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`pagination-container ${className}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        padding: '14px 20px',
        marginTop: '16px',
        background: 'var(--bg-card, rgba(255, 255, 255, 0.75))',
        backdropFilter: 'blur(16px)',
        border: '1px solid var(--border-color, rgba(0, 0, 0, 0.08))',
        borderRadius: '16px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)',
        fontSize: '0.85rem',
        color: 'var(--text-secondary, #6B7280)',
        ...style
      }}
    >
      {/* Left: Range and Count */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span>
          Showing <strong style={{ color: 'var(--text-primary, #111827)' }}>{startItem}–{endItem}</strong> of{' '}
          <strong style={{ color: 'var(--text-primary, #111827)' }}>{totalItems}</strong> {itemLabel}
        </span>

        {onPageSizeChange && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: '8px' }}>
            <span style={{ fontSize: '0.8rem' }}>Per page:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              style={{
                padding: '4px 8px',
                borderRadius: '8px',
                border: '1px solid var(--border-color, rgba(0, 0, 0, 0.15))',
                background: 'var(--bg-dark, #FFFFFF)',
                color: 'var(--text-primary, #111827)',
                fontSize: '0.82rem',
                cursor: 'pointer',
                outline: 'none'
              }}
            >
              {pageSizeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Right: Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        {/* First Page */}
        <button
          type="button"
          onClick={() => onPageChange(1)}
          disabled={safePage <= 1}
          title="First page"
          style={{
            padding: '6px',
            borderRadius: '8px',
            border: '1px solid var(--border-color, rgba(0,0,0,0.1))',
            background: safePage <= 1 ? 'transparent' : 'var(--bg-card, #FFFFFF)',
            color: safePage <= 1 ? 'var(--text-tertiary, #9CA3AF)' : 'var(--text-primary, #111827)',
            cursor: safePage <= 1 ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: safePage <= 1 ? 0.4 : 1,
            transition: 'all 0.15s ease'
          }}
        >
          <ChevronsLeft size={16} />
        </button>

        {/* Previous Page */}
        <button
          type="button"
          onClick={() => onPageChange(safePage - 1)}
          disabled={safePage <= 1}
          title="Previous page"
          style={{
            padding: '6px',
            borderRadius: '8px',
            border: '1px solid var(--border-color, rgba(0,0,0,0.1))',
            background: safePage <= 1 ? 'transparent' : 'var(--bg-card, #FFFFFF)',
            color: safePage <= 1 ? 'var(--text-tertiary, #9CA3AF)' : 'var(--text-primary, #111827)',
            cursor: safePage <= 1 ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: safePage <= 1 ? 0.4 : 1,
            transition: 'all 0.15s ease'
          }}
        >
          <ChevronLeft size={16} />
        </button>

        {/* Numbered Page Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {getPageNumbers().map((p, idx) => {
            if (p === '...') {
              return (
                <span
                  key={`ellipsis-${idx}`}
                  style={{
                    padding: '0 6px',
                    color: 'var(--text-tertiary, #9CA3AF)',
                    userSelect: 'none'
                  }}
                >
                  •••
                </span>
              );
            }

            const isActive = p === safePage;
            return (
              <button
                key={`page-${p}`}
                type="button"
                onClick={() => onPageChange(p)}
                style={{
                  minWidth: '32px',
                  height: '32px',
                  padding: '0 8px',
                  borderRadius: '8px',
                  border: isActive
                    ? '1px solid #E8654A'
                    : '1px solid var(--border-color, rgba(0,0,0,0.08))',
                  background: isActive
                    ? 'linear-gradient(135deg, #E8654A, #F97316)'
                    : 'var(--bg-card, #FFFFFF)',
                  color: isActive ? '#FFFFFF' : 'var(--text-primary, #111827)',
                  fontWeight: isActive ? '700' : '500',
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: isActive ? '0 4px 12px rgba(232, 101, 74, 0.3)' : 'none',
                  transition: 'all 0.15s ease'
                }}
              >
                {p}
              </button>
            );
          })}
        </div>

        {/* Next Page */}
        <button
          type="button"
          onClick={() => onPageChange(safePage + 1)}
          disabled={safePage >= totalPages}
          title="Next page"
          style={{
            padding: '6px',
            borderRadius: '8px',
            border: '1px solid var(--border-color, rgba(0,0,0,0.1))',
            background: safePage >= totalPages ? 'transparent' : 'var(--bg-card, #FFFFFF)',
            color: safePage >= totalPages ? 'var(--text-tertiary, #9CA3AF)' : 'var(--text-primary, #111827)',
            cursor: safePage >= totalPages ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: safePage >= totalPages ? 0.4 : 1,
            transition: 'all 0.15s ease'
          }}
        >
          <ChevronRight size={16} />
        </button>

        {/* Last Page */}
        <button
          type="button"
          onClick={() => onPageChange(totalPages)}
          disabled={safePage >= totalPages}
          title="Last page"
          style={{
            padding: '6px',
            borderRadius: '8px',
            border: '1px solid var(--border-color, rgba(0,0,0,0.1))',
            background: safePage >= totalPages ? 'transparent' : 'var(--bg-card, #FFFFFF)',
            color: safePage >= totalPages ? 'var(--text-tertiary, #9CA3AF)' : 'var(--text-primary, #111827)',
            cursor: safePage >= totalPages ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: safePage >= totalPages ? 0.4 : 1,
            transition: 'all 0.15s ease'
          }}
        >
          <ChevronsRight size={16} />
        </button>
      </div>
    </div>
  );
}
