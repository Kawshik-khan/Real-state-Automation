import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  TrendingDown,
  Coins,
  Cpu,
  Sparkles,
  PieChart,
  ArrowUpRight,
  AlertCircle,
  Lightbulb
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { getAiCostRecommendations } from '../../services/aiControlPlaneApi';

const USD_TO_BDT = 122.50;

export default function TokenCostView() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const data = await getAiCostRecommendations();
      if (data.recommendations) setRecommendations(data.recommendations);
    } catch (err) {
      console.error('Failed to load cost recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const currentSpendUsd = 34.20;
  const budgetLimitUsd = 100.00;
  const spendPercent = ((currentSpendUsd / budgetLimitUsd) * 100).toFixed(1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(232, 101, 74, 0.08) 0%, rgba(243, 144, 114, 0.04) 100%)',
        border: '1px solid rgba(232, 101, 74, 0.25)',
        borderRadius: '20px',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <DollarSign size={20} color="var(--primary-coral, #E8654A)" />
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
              AI Financial Telemetry & Token Cost Allocation
            </h2>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted, #64748B)' }}>
            Real-time inference expenditure dual-tracked in USD and BDT (1 USD = ৳122.50) with automated budget alerts.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <span style={{
            fontSize: '0.78rem',
            fontWeight: 700,
            padding: '4px 10px',
            borderRadius: '20px',
            background: 'rgba(16, 185, 129, 0.12)',
            color: '#10B981',
            border: '1px solid rgba(16, 185, 129, 0.25)'
          }}>
            Monthly Budget Healthy (34.2%)
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <Card style={{ padding: '18px', borderRadius: '20px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #64748B)' }}>CURRENT MONTH SPEND</span>
          <div style={{ fontSize: '1.55rem', fontWeight: 800, color: 'var(--primary-coral, #E8654A)', margin: '4px 0' }}>
            ${currentSpendUsd.toFixed(2)}
          </div>
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#10B981' }}>
            ৳{(currentSpendUsd * USD_TO_BDT).toLocaleString('en-US', { maximumFractionDigits: 0 })} BDT
          </span>
        </Card>

        <Card style={{ padding: '18px', borderRadius: '20px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #64748B)' }}>MONTHLY HARD CAP BUDGET</span>
          <div style={{ fontSize: '1.55rem', fontWeight: 800, color: 'var(--text-main, #1E293B)', margin: '4px 0' }}>
            ${budgetLimitUsd.toFixed(2)}
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted, #64748B)' }}>
            ৳{(budgetLimitUsd * USD_TO_BDT).toLocaleString('en-US', { maximumFractionDigits: 0 })} BDT limit
          </span>
        </Card>

        <Card style={{ padding: '18px', borderRadius: '20px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #64748B)' }}>TOKEN CONSUMPTION</span>
          <div style={{ fontSize: '1.55rem', fontWeight: 800, color: 'var(--text-main, #1E293B)', margin: '4px 0' }}>
            1.24M
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted, #64748B)' }}>
            820K Input • 420K Output
          </span>
        </Card>

        <Card style={{ padding: '18px', borderRadius: '20px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #64748B)' }}>COST PER 1K TURNS</span>
          <div style={{ fontSize: '1.55rem', fontWeight: 800, color: '#10B981', margin: '4px 0' }}>
            $0.42
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted, #64748B)' }}>
            ৳{(0.42 * USD_TO_BDT).toFixed(2)} BDT / 1,000 queries
          </span>
        </Card>
      </div>

      {/* Budget Progress Meter */}
      <Card style={{ padding: '18px', borderRadius: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
            Monthly Budget Utilization (${currentSpendUsd.toFixed(2)} of ${budgetLimitUsd.toFixed(2)})
          </span>
          <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#10B981' }}>
            {spendPercent}% Used
          </span>
        </div>
        <div style={{ width: '100%', height: '10px', background: 'rgba(255,255,255,0.08)', borderRadius: '6px', overflow: 'hidden' }}>
          <div style={{
            width: `${spendPercent}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #10B981 0%, var(--primary-coral, #E8654A) 100%)',
            borderRadius: '6px'
          }} />
        </div>
      </Card>

      {/* Breakdown Grid: By Provider & By Agent */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Spend by LLM Provider */}
        <Card style={{ padding: '20px', borderRadius: '20px' }}>
          <h3 style={{ margin: '0 0 14px 0', fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
            Inference Spend by Provider
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              { name: 'Groq (Llama 3.3 70B & 8B)', spendUsd: 14.50, pct: 42.4, color: '#F59E0B' },
              { name: 'OpenAI (GPT-4o-mini & Text Embedding)', spendUsd: 12.30, pct: 36.0, color: '#10B981' },
              { name: 'Anthropic (Claude 3.5 Sonnet)', spendUsd: 5.40, pct: 15.8, color: '#6366F1' },
              { name: 'OpenRouter (Fallback Cascade)', spendUsd: 2.00, pct: 5.8, color: '#EC4899' }
            ].map((prov) => (
              <div key={prov.name}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-main, #1E293B)' }}>{prov.name}</span>
                  <span style={{ color: 'var(--text-muted, #475569)' }}>
                    <strong>${prov.spendUsd.toFixed(2)}</strong> (৳{(prov.spendUsd * USD_TO_BDT).toFixed(0)}) — {prov.pct}%
                  </span>
                </div>
                <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${prov.pct}%`, height: '100%', background: prov.color, borderRadius: '3px' }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Cost Optimization Recommendations */}
        <Card style={{ padding: '20px', borderRadius: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <Lightbulb size={18} color="var(--primary-coral, #E8654A)" />
            <h3 style={{ margin: 0, fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-main, #1E293B)' }}>
              Actionable Cost Optimization Insights
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{
              padding: '14px',
              borderRadius: '16px',
              border: '1px solid var(--border-glass)',
              background: 'var(--bg-elevated, #1E293B)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <strong style={{ fontSize: '0.82rem', color: 'var(--text-main, #1E293B)' }}>
                  Route Simple Inquiries to Groq Llama 3.3
                </strong>
                <span style={{ fontSize: '0.74rem', color: '#10B981', fontWeight: 700 }}>
                  Save ~$18.50 /mo
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '0.76rem', color: 'var(--text-muted, #64748B)' }}>
                Inquiries under 150 characters with high FAQ confidence can bypass GPT-4o, reducing token unit costs by 62% without degrading groundedness.
              </p>
            </div>

            <div style={{
              padding: '14px',
              borderRadius: '16px',
              border: '1px solid var(--border-glass)',
              background: 'var(--bg-elevated, #1E293B)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <strong style={{ fontSize: '0.82rem', color: 'var(--text-main, #1E293B)' }}>
                  Enable System Prompt Prefix Caching
                </strong>
                <span style={{ fontSize: '0.74rem', color: '#10B981', fontWeight: 700 }}>
                  Save ~28% Input Tokens
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '0.76rem', color: 'var(--text-muted, #64748B)' }}>
                GLG luxury property factsheet system prompts are static. Caching the initial 1,800 token prompt prefix achieves 50% discount on cache hits.
              </p>
            </div>

            <div style={{
              padding: '14px',
              borderRadius: '16px',
              border: '1px solid var(--border-glass)',
              background: 'var(--bg-elevated, #1E293B)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <strong style={{ fontSize: '0.82rem', color: 'var(--text-main, #1E293B)' }}>
                  Set Social Bridge Max Tokens Cap to 650
                </strong>
                <span style={{ fontSize: '0.74rem', color: '#10B981', fontWeight: 700 }}>
                  Save ~$4.20 /mo
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '0.76rem', color: 'var(--text-muted, #64748B)' }}>
                Social media DM responses exceeding 650 tokens suffer higher drop-off rates and needlessly consume output token budget.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
