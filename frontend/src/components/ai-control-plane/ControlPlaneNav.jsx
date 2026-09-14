import React, { useMemo } from 'react';
import {
  LayoutDashboard,
  SlidersHorizontal,
  FileCode,
  Wrench,
  Workflow,
  Layers,
  Cpu,
  Route,
  Flame,
  Database,
  Play,
  CheckSquare,
  Award,
  Split,
  DollarSign,
  Activity,
  AlertOctagon,
  ShieldCheck,
  UserCheck,
  Scale,
  ScrollText,
  Rocket,
  ChevronRight,
  Sparkles
} from 'lucide-react';

export const CONTROL_PLANE_SECTIONS = [
  {
    id: 'overview',
    label: 'AI Overview',
    icon: LayoutDashboard,
    badge: 'LIVE',
    category: 'OVERVIEW',
    description: 'Real-time telemetry, model latencies, and token budget'
  },
  {
    category: 'AGENTS',
    label: 'Agents',
    icon: SlidersHorizontal,
    count: 5,
    items: [
      { id: 'agent_architect', label: 'Agent Architect', icon: SlidersHorizontal, desc: 'Tuning, persona presets & parameters' },
      { id: 'prompt_studio', label: 'Prompt Studio', icon: FileCode, desc: 'Variable tags & syntax validation' },
      { id: 'tools_actions', label: 'Tools & Actions', icon: Wrench, desc: 'Registry & execution sandbox' },
      { id: 'workflow_builder', label: 'Workflow Builder', icon: Workflow, desc: 'LangGraph visual node machine' },
      { id: 'memory_rag', label: 'Memory & RAG', icon: Layers, desc: 'Hybrid search & grounding' },
    ]
  },
  {
    category: 'MODELS',
    label: 'Models',
    icon: Cpu,
    count: 4,
    items: [
      { id: 'llm_config', label: 'LLM Configuration', icon: Cpu, desc: 'Gateway & connection settings' },
      { id: 'model_routing', label: 'Model Routing', icon: Route, desc: 'Intelligent routing rules' },
      { id: 'fine_tuning', label: 'Fine-Tuning', icon: Flame, desc: 'LoRA training board' },
      { id: 'model_registry', label: 'Model Registry', icon: Database, desc: 'Central inventory & pings' },
    ]
  },
  {
    category: 'TESTING',
    label: 'Testing',
    icon: Play,
    count: 4,
    items: [
      { id: 'playground', label: 'AI Playground', icon: Play, badge: 'SANDBOX', desc: 'Interactive chat & span traces' },
      { id: 'evaluation_lab', label: 'Evaluation Lab', icon: CheckSquare, desc: 'Quantitative benchmark suite' },
      { id: 'benchmarking', label: 'Benchmarking', icon: Award, desc: '8-dimension model arena' },
      { id: 'ab_testing', label: 'A/B Testing', icon: Split, desc: 'Live traffic split studio' },
    ]
  },
  {
    category: 'OBSERVABILITY',
    label: 'Observability',
    icon: Activity,
    count: 3,
    items: [
      { id: 'token_cost', label: 'Token & Cost', icon: DollarSign, desc: 'USD & BDT token accounting' },
      { id: 'traces', label: 'AI Logs / Traces', icon: Activity, desc: 'Span trees & waterfall latency' },
      { id: 'incidents', label: 'Incidents', icon: AlertOctagon, desc: 'Circuit breakers & emergency stop' },
    ]
  },
  {
    category: 'GOVERNANCE',
    label: 'Governance',
    icon: ShieldCheck,
    count: 4,
    items: [
      { id: 'guardrails', label: 'Guardrails', icon: ShieldCheck, desc: 'Prompt injection & PII masking' },
      { id: 'human_approval', label: 'Human Approval', icon: UserCheck, badge: '2', desc: 'Supervisor approval queue' },
      { id: 'policy_engine', label: 'Policy Engine', icon: Scale, desc: 'Condition rules & simulation' },
      { id: 'audit_log', label: 'Audit Log', icon: ScrollText, desc: 'Immutable security log' },
    ]
  },
  {
    category: 'RELEASES & DATA',
    label: 'Releases & Data',
    icon: Rocket,
    count: 3,
    items: [
      { id: 'datasets', label: 'Golden Datasets', icon: Database, desc: 'Grounding corpus & golden cases' },
      { id: 'ai_versioning', label: 'AI Versioning', icon: Layers, desc: 'Manifest snapshots & rollback' },
      { id: 'release_management', label: 'Release Pipeline', icon: Rocket, desc: 'Deployment gates' },
    ]
  }
];

export function getCategoryForView(viewId) {
  if (viewId === 'overview') return 'OVERVIEW';
  for (const sec of CONTROL_PLANE_SECTIONS) {
    if (sec.items && sec.items.some((it) => it.id === viewId)) {
      return sec.category;
    }
  }
  return 'AGENTS';
}

export default function ControlPlaneNav({ activeView, setActiveView }) {
  // Derive current category from active view
  const activeCategory = useMemo(() => getCategoryForView(activeView), [activeView]);

  // Find the items of the active category
  const activeGroup = useMemo(() => {
    return CONTROL_PLANE_SECTIONS.find((s) => s.category === activeCategory);
  }, [activeCategory]);

  const handleSelectCategory = (cat) => {
    if (cat === 'OVERVIEW') {
      setActiveView('overview');
      return;
    }
    const group = CONTROL_PLANE_SECTIONS.find((s) => s.category === cat);
    if (group?.items?.length) {
      // If the current view is already in this category, keep it; otherwise jump to the first item
      const alreadyInCat = group.items.some((it) => it.id === activeView);
      if (!alreadyInCat) {
        setActiveView(group.items[0].id);
      }
    }
  };

  return (
    <div style={{
      background: 'var(--bg-card, #FFFFFF)',
      border: '1px solid var(--border-glass, rgba(0,0,0,0.08))',
      borderRadius: '20px',
      padding: '12px 18px',
      marginBottom: '20px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.03)',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px'
    }}>
      {/* Tier 1: Main Category Tabs (Compact, fits all screens without horizontal overflow) */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        flexWrap: 'wrap',
        borderBottom: '1px solid var(--border-glass, rgba(255,255,255,0.08))',
        paddingBottom: '10px'
      }}>
        {/* Overview Button */}
        <button
          onClick={() => setActiveView('overview')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '7px 14px',
            borderRadius: '20px',
            background: activeCategory === 'OVERVIEW' ? 'var(--primary-coral, #E8654A)' : 'transparent',
            color: activeCategory === 'OVERVIEW' ? '#FFFFFF' : 'var(--text-main, #CBD5E1)',
            border: activeCategory === 'OVERVIEW' ? '1px solid var(--primary-coral, #E8654A)' : '1px solid transparent',
            fontSize: '0.82rem',
            fontWeight: activeCategory === 'OVERVIEW' ? 700 : 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <LayoutDashboard size={15} />
          <span>AI Overview</span>
          <span style={{
            fontSize: '0.62rem',
            padding: '1px 6px',
            borderRadius: '12px',
            background: activeCategory === 'OVERVIEW' ? 'rgba(255,255,255,0.25)' : 'rgba(16, 185, 129, 0.18)',
            color: activeCategory === 'OVERVIEW' ? '#FFFFFF' : '#10B981',
            fontWeight: 800
          }}>
            LIVE
          </span>
        </button>

        <div style={{ width: '1px', height: '22px', background: 'var(--border-glass, rgba(255,255,255,0.1))', margin: '0 4px' }} />

        {/* 6 Category Buttons */}
        {CONTROL_PLANE_SECTIONS.filter((s) => s.category !== 'OVERVIEW').map((group) => {
          const isCatActive = activeCategory === group.category;
          const GroupIcon = group.icon;

          return (
            <button
              key={group.category}
              onClick={() => handleSelectCategory(group.category)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '7px 12px',
                borderRadius: '20px',
                background: isCatActive ? 'rgba(232, 101, 74, 0.16)' : 'transparent',
                color: isCatActive ? 'var(--primary-coral, #E8654A)' : 'var(--text-main, #CBD5E1)',
                border: isCatActive ? '1px solid rgba(232, 101, 74, 0.35)' : '1px solid transparent',
                fontSize: '0.82rem',
                fontWeight: isCatActive ? 700 : 500,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <GroupIcon size={15} color={isCatActive ? 'var(--primary-coral, #E8654A)' : '#94A3B8'} />
              <span>{group.label}</span>
              <span style={{
                fontSize: '0.65rem',
                padding: '1px 6px',
                borderRadius: '12px',
                background: isCatActive ? 'var(--primary-coral, #E8654A)' : 'var(--border-glass, rgba(255,255,255,0.1))',
                color: isCatActive ? '#FFFFFF' : 'var(--text-muted, #94A3B8)',
                fontWeight: 700
              }}>
                {group.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Tier 2: Subcategory Navigation Pills for Active Category */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        flexWrap: 'wrap',
        minHeight: '34px'
      }}>
        {activeCategory === 'OVERVIEW' ? (
          <div style={{
            fontSize: '0.78rem',
            color: 'var(--text-muted, #94A3B8)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 8px'
          }}>
            <Sparkles size={14} color="var(--primary-coral, #E8654A)" />
            <span>
              Real-time executive command center · Multi-model latency budgets, failure rate SLAs, and BDT token billing.
            </span>
          </div>
        ) : (
          activeGroup?.items?.map((item) => {
            const ItemIcon = item.icon;
            const isSubActive = activeView === item.id;

            return (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 14px',
                  borderRadius: '24px',
                  background: isSubActive ? 'var(--primary-coral, #E8654A)' : 'var(--bg-elevated, rgba(255,255,255,0.06))',
                  color: isSubActive ? '#FFFFFF' : 'var(--text-main, #CBD5E1)',
                  border: isSubActive ? '1px solid var(--primary-coral, #E8654A)' : '1px solid var(--border-glass, rgba(255,255,255,0.12))',
                  fontSize: '0.78rem',
                  fontWeight: isSubActive ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  boxShadow: isSubActive ? '0 2px 8px rgba(232, 101, 74, 0.3)' : 'none'
                }}
              >
                <ItemIcon size={14} color={isSubActive ? '#FFFFFF' : '#94A3B8'} />
                <span>{item.label}</span>
                {item.badge && (
                  <span style={{
                    fontSize: '0.6rem',
                    padding: '1px 5px',
                    borderRadius: '10px',
                    background: isSubActive ? 'rgba(255,255,255,0.25)' : 'rgba(232, 101, 74, 0.16)',
                    color: isSubActive ? '#FFFFFF' : 'var(--primary-coral, #E8654A)',
                    fontWeight: 700
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
