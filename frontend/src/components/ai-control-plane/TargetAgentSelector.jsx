import React from 'react';
import { Bot, CheckCircle2, AlertTriangle, Sparkles, Layers } from 'lucide-react';
import Badge from '../ui/Badge';

export default function TargetAgentSelector({
  agents = [],
  selectedAgentSlug,
  onSelectAgent,
  hasUnsavedChanges = false,
  onDiscardChanges,
}) {
  const handleAgentClick = (slug) => {
    if (slug === selectedAgentSlug) return;
    if (hasUnsavedChanges) {
      const confirmSwitch = window.confirm(
        'You have unsaved configuration changes for the active agent. Discard changes and switch target agent?'
      );
      if (!confirmSwitch) return;
      if (onDiscardChanges) onDiscardChanges();
    }
    onSelectAgent(slug);
  };

  const getAgentEmoji = (slug) => {
    switch (slug) {
      case 'property_agent': return '🏢';
      case 'faq_agent': return '❓';
      case 'supervisor': return '🧭';
      case 'email_agent': return '✉️';
      case 'social_bridge': return '💬';
      default: return '🤖';
    }
  };

  return (
    <div style={{
      background: 'var(--bg-card, #FFFFFF)',
      border: '1px solid var(--border-glass, rgba(0,0,0,0.08))',
      borderRadius: '20px',
      padding: '16px 20px',
      marginBottom: '20px',
      boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
      display: 'flex',
      flexDirection: 'column',
      gap: '14px'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '10px',
            background: 'rgba(232, 101, 74, 0.12)',
            color: 'var(--primary-coral, #E8654A)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Bot size={18} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--text-muted, #64748B)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Active Target Agent Context
              </span>
              {hasUnsavedChanges && (
                <span style={{
                  fontSize: '0.72rem',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: '#FEF3C7',
                  color: '#92400E',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <AlertTriangle size={12} />
                  Unsaved Changes
                </span>
              )}
            </div>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted, #64748B)' }}>
              Controls prompts, active model tiers, tool assignments, RAG vector retrieval, and live trace debugging.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            fontSize: '0.75rem',
            padding: '4px 12px',
            borderRadius: '20px',
            background: 'rgba(16, 185, 129, 0.12)',
            color: '#10B981',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10B981', animation: 'pulse 2s infinite' }} />
            HOT-RELOAD SYNC ACTIVE
          </span>
        </div>
      </div>

      {/* Agent Pills */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        overflowX: 'auto',
        paddingBottom: '4px'
      }}>
        {agents.map((ag) => {
          const isSelected = ag.slug === selectedAgentSlug;
          return (
            <button
              key={ag.slug}
              onClick={() => handleAgentClick(ag.slug)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 16px',
                borderRadius: '24px',
                background: isSelected 
                  ? 'linear-gradient(135deg, var(--primary-coral, #E8654A), #F07E65)' 
                  : 'var(--bg-elevated, rgba(255,255,255,0.06))',
                border: isSelected 
                  ? '1px solid var(--primary-coral, #E8654A)' 
                  : '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                color: isSelected ? '#FFFFFF' : 'var(--text-main, #F1F5F9)',
                cursor: 'pointer',
                fontSize: '0.84rem',
                fontWeight: isSelected ? 700 : 500,
                transition: 'all 0.15s ease',
                whiteSpace: 'nowrap',
                boxShadow: isSelected ? '0 4px 14px rgba(232, 101, 74, 0.3)' : 'none'
              }}
            >
              <span style={{ fontSize: '1.05rem' }}>{getAgentEmoji(ag.slug)}</span>
              <span>{ag.name || ag.slug}</span>
              <span style={{
                fontSize: '0.7rem',
                padding: '2px 8px',
                borderRadius: '12px',
                background: isSelected ? 'rgba(255,255,255,0.25)' : 'var(--border-glass, rgba(255,255,255,0.12))',
                color: isSelected ? '#FFFFFF' : 'var(--text-muted, #94A3B8)',
                fontWeight: 600
              }}>
                {ag.current_prompt_version || 'v1.0'}
              </span>
              {isSelected && (
                <CheckCircle2 size={14} color="#FFFFFF" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
