import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getAnalyticsReport } from '../services/api';

// Reusable Dashboard UI Components
import KPICardStrip from '../components/dashboard/KPICardStrip';
import AIEngagementChart from '../components/dashboard/AIEngagementChart';
import ChannelAttributionDonut from '../components/dashboard/ChannelAttributionDonut';
import CriticalDatesTimeline from '../components/dashboard/CriticalDatesTimeline';
import ValuablePropertiesTable from '../components/dashboard/ValuablePropertiesTable';
import FinancialSummaryWidget from '../components/dashboard/FinancialSummaryWidget';

export default function DashboardHome({ 
  setActiveTab,
  moduleConfig = {
    kpis: true,
    chart: true,
    channelDonut: true,
    map: true,
    criticalDates: true,
    valuableProps: true,
    financialSummary: true
  },
  selectedProperty = 'all',
  selectedChannel = 'all',
  dateRange = '30d',
  searchQuery = ''
}) {
  const { user } = useAuth();

  // Live real-time statistics
  const [metrics, setMetrics] = useState({
    totalProperties: 12,
    pipelineValue: '৳14.8 Cr',
    totalLeads: 142,
    aiRate: '94.2%',
    hotLeads: 12,
    avgResponse: '1.2s'
  });

  // Real-time background telemetry polling
  useEffect(() => {
    fetchLiveStats();
    const interval = setInterval(() => {
      fetchLiveStats();
    }, 6000);

    return () => clearInterval(interval);
  }, []);

  const fetchLiveStats = async () => {
    try {
      const [analyticsRes] = await Promise.allSettled([
        getAnalyticsReport()
      ]);

      if (analyticsRes.status === 'fulfilled' && analyticsRes.value?.metrics) {
        const m = analyticsRes.value.metrics;
        setMetrics(prev => ({
          ...prev,
          totalLeads: m.total_incoming_leads || prev.totalLeads,
          aiRate: m.ai_resolution_rate_percent ? `${m.ai_resolution_rate_percent}%` : prev.aiRate,
          hotLeads: m.hot_leads_scored_above_80 || prev.hotLeads,
          avgResponse: m.avg_response_time_seconds ? `${m.avg_response_time_seconds}s` : prev.avgResponse
        }));
      }
    } catch (err) {
      console.warn('[DashboardHome] Live stats sync:', err);
    }
  };

  return (
    <div className="dashboard-container">
      {/* Row 1: 5-Card Operational KPI Strip */}
      {moduleConfig.kpis !== false && (
        <KPICardStrip metrics={metrics} />
      )}

      {/* Row 2: Middle Visuals Grid (Engagement Chart 60% + Channel Attribution Donut 40%) */}
      {(moduleConfig.chart !== false || (moduleConfig.channelDonut !== false && moduleConfig.map !== false)) && (
        <section className="visuals-grid">
          {moduleConfig.chart !== false && (
            <AIEngagementChart />
          )}
          {(moduleConfig.channelDonut !== false && moduleConfig.map !== false) && (
            <ChannelAttributionDonut 
              onNavigateSocial={user?.role === 'manager' ? () => setActiveTab && setActiveTab('social_analytics') : undefined} 
            />
          )}
        </section>
      )}

      {/* Row 3: Bottom 3-Column Detailed Operational Panels */}
      {(moduleConfig.criticalDates !== false || moduleConfig.valuableProps !== false || moduleConfig.financialSummary !== false) && (
        <section className="detail-grid-3">
          {moduleConfig.criticalDates !== false && (
            <CriticalDatesTimeline />
          )}
          {moduleConfig.valuableProps !== false && (
            <ValuablePropertiesTable 
              onNavigateProperties={() => setActiveTab && setActiveTab('properties')} 
              searchQuery={searchQuery}
              selectedProperty={selectedProperty}
            />
          )}
          {moduleConfig.financialSummary !== false && (
            <FinancialSummaryWidget />
          )}
        </section>
      )}
    </div>
  );
}
