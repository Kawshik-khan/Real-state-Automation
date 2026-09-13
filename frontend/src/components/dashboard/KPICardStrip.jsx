import React from 'react';
import { 
  Building2, 
  DollarSign, 
  Users, 
  Sparkles, 
  AlertCircle, 
  ArrowUpRight, 
  ArrowDownRight 
} from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';

export default function KPICardStrip({ metrics = {} }) {
  const cards = [
    {
      id: 'properties',
      label: 'Total Properties',
      value: metrics.totalProperties || 12,
      suffix: '',
      trend: '+1.2%',
      trendDirection: 'up',
      subtitle: 'This Month',
      icon: Building2,
      accent: 'coral'
    },
    {
      id: 'pipeline',
      label: 'Annual Pipeline Value',
      value: metrics.pipelineValue || '৳14.8 Cr',
      suffix: '',
      trend: '+18.4%',
      trendDirection: 'up',
      subtitle: 'This Quarter',
      icon: DollarSign,
      accent: 'emerald'
    },
    {
      id: 'leads',
      label: 'Total Leads Captured',
      value: metrics.totalLeads || 142,
      suffix: '',
      trend: '+5.2%',
      trendDirection: 'up',
      subtitle: 'This Month',
      icon: Users,
      accent: 'blue'
    },
    {
      id: 'ai_rate',
      label: 'AI Resolution Rate',
      value: metrics.aiRate || '94.2%',
      suffix: '',
      trend: '+1.2%',
      trendDirection: 'up',
      subtitle: 'Avg 1.2s latency',
      icon: Sparkles,
      accent: 'coral'
    },
    {
      id: 'hot_leads',
      label: 'Hot Leads Pending',
      value: metrics.hotLeads || 12,
      suffix: '',
      trend: '-6.8%',
      trendDirection: 'down', // Good: fewer unprocessed hot leads
      subtitle: 'Score > 80/100',
      icon: AlertCircle,
      accent: 'amber'
    }
  ];

  return (
    <section className="kpi-grid-5">
      {cards.map((card) => {
        const Icon = card.icon;
        const isUp = card.trendDirection === 'up';
        return (
          <Card 
            key={card.id}
            style={{ 
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              minHeight: '130px'
            }}
          >
            {/* Top row: Label & Icon */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ 
                fontSize: '0.82rem', 
                fontWeight: 600, 
                color: 'var(--text-muted)',
                letterSpacing: '-0.01em'
              }}>
                {card.label}
              </span>
              <div style={{
                width: '30px',
                height: '30px',
                borderRadius: '8px',
                background: 'var(--bg-card-hover)',
                border: '1px solid var(--border-glass)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Icon size={16} color="var(--primary-coral)" />
              </div>
            </div>

            {/* Middle row: Large Stat */}
            <div style={{ marginTop: '10px' }}>
              <span style={{ 
                fontSize: '1.75rem', 
                fontWeight: 800, 
                color: 'var(--text-main)',
                fontFamily: 'Outfit, sans-serif',
                letterSpacing: '-0.03em',
                lineHeight: 1
              }}>
                {card.value}
              </span>
            </div>

            {/* Bottom row: Trend badge & subtitle */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px', 
              marginTop: '12px' 
            }}>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '2px',
                fontSize: '0.74rem',
                fontWeight: 700,
                color: isUp ? '#10B981' : '#E8654A'
              }}>
                {isUp ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
                {card.trend}
              </span>
              <span style={{ 
                fontSize: '0.72rem', 
                color: 'var(--text-dim)',
                whiteSpace: 'nowrap'
              }}>
                {card.subtitle}
              </span>
            </div>
          </Card>
        );
      })}
    </section>
  );
}
