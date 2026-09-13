import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { DollarSign, TrendingUp, ShieldCheck, Zap } from 'lucide-react';
import { getSocialKPIs } from '../../services/api';

export default function FinancialSummaryWidget() {
  const [pipelineVal, setPipelineVal] = useState('৳4.2 Cr');
  const [targetPercent, setTargetPercent] = useState(78);
  const [savingsBDT, setSavingsBDT] = useState('৳18.5 Lakhs');

  useEffect(() => {
    let isMounted = true;
    async function loadFinances() {
      try {
        const res = await getSocialKPIs('30d');
        if (res && res.totals && isMounted) {
          const pipe = res.totals.pipeline_value_bdt || 42000000;
          const cr = (pipe / 10000000).toFixed(1);
          setPipelineVal(`৳${cr} Cr`);
          const spend = res.totals.ad_spend_bdt || 220000;
          const savedLakhs = ((spend * 4.5) / 100000).toFixed(1);
          setSavingsBDT(`৳${savedLakhs} Lakhs`);
          setTargetPercent(Math.min(Math.max(Math.round((pipe / 50000000) * 100), 40), 95));
        }
      } catch (err) {
        // Retain default values
      }
    }
    loadFinances();
    return () => { isMounted = false; };
  }, []);

  return (
    <Card
      title="Financial & Deal Velocity"
      subtitle="Revenue realization, operational savings & yield"
      action={
        <Badge variant="emerald" pulse>
          Live P&L
        </Badge>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Metric 1: Annual Rental Yield Target */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Annual Rental Target (FY 2026)
            </span>
            <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-main)' }}>
              {pipelineVal} <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 500 }}>({targetPercent}%)</span>
            </span>
          </div>
          <div style={{
            width: '100%',
            height: '7px',
            borderRadius: '10px',
            background: 'var(--border-glass)',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${targetPercent}%`,
              height: '100%',
              borderRadius: '10px',
              background: 'var(--primary-coral)',
              transition: 'width 0.6s ease'
            }} />
          </div>
        </div>

        {/* Metric 2: AI Operational Cost Savings */}
        <div style={{
          padding: '12px 14px',
          borderRadius: '10px',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <span style={{ fontSize: '0.72rem', color: 'var(--accent-emerald)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Automation Efficiency
            </span>
            <h5 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '2px', fontFamily: 'Outfit' }}>
              {savingsBDT} Saved
            </h5>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              82% reduction in manual call-center inquiries
            </p>
          </div>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'var(--accent-emerald)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            <Zap size={20} />
          </div>
        </div>

        {/* Summary Stats Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <div style={{
            padding: '10px',
            borderRadius: '8px',
            background: 'var(--bg-card-hover)',
            border: '1px solid var(--border-glass)'
          }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              Avg Deal Cycle
            </span>
            <h6 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              14.2 Days
            </h6>
            <span style={{ fontSize: '0.66rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
              ↘ 4 days faster
            </span>
          </div>

          <div style={{
            padding: '10px',
            borderRadius: '8px',
            background: 'var(--bg-card-hover)',
            border: '1px solid var(--border-glass)'
          }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              Commission Payouts
            </span>
            <h6 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--primary-coral)', marginTop: '2px' }}>
              ৳28.4 Lakhs
            </h6>
            <span style={{ fontSize: '0.66rem', color: 'var(--text-dim)' }}>
              Q3 Projected
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}
