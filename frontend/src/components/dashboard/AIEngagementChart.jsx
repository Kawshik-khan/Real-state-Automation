import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid 
} from 'recharts';
import Card from '../ui/Card';
import CustomDropdown from '../ui/CustomDropdown';
import { ArrowUpRight, TrendingUp } from 'lucide-react';
import { getTimeSeriesAnalytics } from '../../services/api';

const DEFAULT_MONTHLY_DATA = [
  { month: 'Jan', messages: 2450, leads: 82, rate: '92%' },
  { month: 'Feb', messages: 3120, leads: 114, rate: '94%' },
  { month: 'Mar', messages: 2890, leads: 96, rate: '93%' },
  { month: 'Apr', messages: 3950, leads: 138, rate: '95%' },
  { month: 'May', messages: 4620, leads: 168, rate: '96%' },
  { month: 'Jun', messages: 4390, leads: 142, rate: '95%' }
];

export default function AIEngagementChart() {
  const [timeRange, setTimeRange] = useState('6m');
  const [chartData, setChartData] = useState(DEFAULT_MONTHLY_DATA);
  const [totalInteractions, setTotalInteractions] = useState(21420);
  const [peakThroughput, setPeakThroughput] = useState(4620);
  const [peakMonth, setPeakMonth] = useState('May');

  useEffect(() => {
    let isMounted = true;
    async function loadTimeSeries() {
      try {
        const res = await getTimeSeriesAnalytics({ period: timeRange });
        if (res && res.data && res.data.length > 0 && isMounted) {
          setChartData(res.data);
          const total = res.data.reduce((acc, cur) => acc + (cur.messages || 0), 0);
          setTotalInteractions(total > 0 ? total : 21420);

          let peak = res.data[0];
          for (const d of res.data) {
            if ((d.messages || 0) > (peak.messages || 0)) {
              peak = d;
            }
          }
          if (peak) {
            setPeakThroughput(peak.messages || 4620);
            setPeakMonth(peak.month || 'May');
          }
        }
      } catch (err) {
        // Retain default data on error
      }
    }
    loadTimeSeries();
    return () => { isMounted = false; };
  }, [timeRange]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-glass)',
          boxShadow: 'var(--shadow-dropdown)',
          borderRadius: '10px',
          padding: '10px 14px',
          fontFamily: 'Inter, sans-serif'
        }}>
          <p style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-main)', marginBottom: '4px' }}>
            {label} 2026
          </p>
          <p style={{ fontSize: '0.8rem', color: 'var(--primary-coral)', fontWeight: 600 }}>
            Volume: {Number(data.messages).toLocaleString()} msgs
          </p>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Leads: {data.leads} | AI Handled: {data.rate}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card 
      title="Monthly AI Engagement & Inquiries"
      subtitle="Processed customer interactions across WhatsApp, Web & Social channels"
      action={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            color: 'var(--accent-emerald)',
            display: 'flex',
            alignItems: 'center',
            gap: '2px',
            background: 'rgba(16, 185, 129, 0.1)',
            padding: '3px 8px',
            borderRadius: '6px'
          }}>
            <ArrowUpRight size={13} /> +28.4%
          </span>
          <CustomDropdown
            value={timeRange}
            onChange={setTimeRange}
            options={[
              { value: '6m', label: 'Last 6 Months' },
              { value: '12m', label: 'This Year' }
            ]}
            minWidth="125px"
            buttonStyle={{ padding: '4px 8px', height: '28px', fontSize: '0.75rem' }}
          />
        </div>
      }
      style={{ minHeight: '380px' }}
    >
      <div style={{ display: 'flex', gap: '20px', height: '100%', alignItems: 'center' }}>
        {/* Left: Summary Metrics Callout */}
        <div style={{ 
          width: '160px', 
          display: 'flex', 
          flexDirection: 'column', 
          justifyContent: 'center',
          gap: '16px',
          borderRight: '1px solid var(--border-glass)',
          paddingRight: '16px',
          flexShrink: 0
        }}>
          <div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>
              Total Interactions
            </span>
            <h4 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '2px', fontFamily: 'Outfit' }}>
              {totalInteractions.toLocaleString()}
            </h4>
            <span style={{ fontSize: '0.7rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
              ↗ 18.2% vs prev period
            </span>
          </div>

          <div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>
              Peak Throughput
            </span>
            <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--primary-coral)', marginTop: '2px' }}>
              {peakThroughput.toLocaleString()} msgs
            </h4>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
              Recorded in {peakMonth} 2026
            </span>
          </div>

          <div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>
              Avg Cost / Lead
            </span>
            <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-emerald)', marginTop: '2px' }}>
              ৳42 BDT
            </h4>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
              82% call center savings
            </span>
          </div>
        </div>

        {/* Right: Recharts Bar Chart */}
        <div style={{ flex: 1, height: '270px', width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-glass)" vertical={false} />
              <XAxis 
                dataKey="month" 
                tickLine={false} 
                axisLine={{ stroke: 'var(--border-glass)' }} 
                tick={{ fill: 'var(--text-muted)', fontSize: 12, fontWeight: 500 }}
              />
              <YAxis 
                tickLine={false} 
                axisLine={false} 
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                tickFormatter={(val) => `${val / 1000}k`}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--bg-card-hover)', opacity: 0.8 }} />
              <Bar 
                dataKey="messages" 
                fill="var(--primary-coral)" 
                radius={[6, 6, 0, 0]} 
                maxBarSize={48}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  );
}
