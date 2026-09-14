import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Home,
  BookOpen, 
  MessageSquare, 
  Building2, 
  BarChart3, 
  Terminal, 
  Workflow,
  Share2,
  Sparkles,
  Sun, 
  Moon, 
  HelpCircle, 
  LogOut, 
  Zap,
  SlidersHorizontal,
  ChevronRight,
  ArrowRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { CONTROL_PLANE_SECTIONS } from '../ai-control-plane/ControlPlaneNav';

export default function Sidebar({ activeTab, setActiveTab }) {
  const { user, logout } = useAuth();
  const userRole = user?.role || 'viewer';
  const navigate = useNavigate();
  const [hoveredItem, setHoveredItem] = useState(null);

  // AI Studio Cascading Flyout Menu State
  const [aiFlyoutOpen, setAiFlyoutOpen] = useState(false);
  const [activeFlyoutCategory, setActiveFlyoutCategory] = useState('AGENTS');
  const flyoutTimerRef = useRef(null);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (flyoutTimerRef.current) clearTimeout(flyoutTimerRef.current);
    };
  }, []);

  const handleAiButtonEnter = () => {
    if (flyoutTimerRef.current) {
      clearTimeout(flyoutTimerRef.current);
      flyoutTimerRef.current = null;
    }
    setHoveredItem('ai_customization');
    setAiFlyoutOpen(true);
  };

  const handleAiButtonLeave = () => {
    if (flyoutTimerRef.current) clearTimeout(flyoutTimerRef.current);
    flyoutTimerRef.current = setTimeout(() => {
      setAiFlyoutOpen(false);
      setHoveredItem((prev) => (prev === 'ai_customization' ? null : prev));
    }, 240);
  };

  const handleFlyoutContainerEnter = () => {
    if (flyoutTimerRef.current) {
      clearTimeout(flyoutTimerRef.current);
      flyoutTimerRef.current = null;
    }
    setAiFlyoutOpen(true);
    setHoveredItem('ai_customization');
  };

  const handleFlyoutContainerLeave = () => {
    if (flyoutTimerRef.current) clearTimeout(flyoutTimerRef.current);
    flyoutTimerRef.current = setTimeout(() => {
      setAiFlyoutOpen(false);
      setHoveredItem((prev) => (prev === 'ai_customization' ? null : prev));
    }, 240);
  };

  const handleSelectSubcategory = (viewId) => {
    if (flyoutTimerRef.current) clearTimeout(flyoutTimerRef.current);
    setAiFlyoutOpen(false);
    setHoveredItem(null);
    setActiveTab('ai_customization');
    navigate(`/ai-studio?view=${viewId}`);
  };

  // Theme state
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('glg_theme') || 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('glg_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Dedicated navigation for Manager matching manager command specs
  const managerNavItems = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'properties', label: 'Properties', icon: Building2 },
    { id: 'conversations', label: 'Live Chats', icon: MessageSquare, badge: 'LIVE', badgeColor: '#10B981', dot: true },
    { id: 'analytics', label: 'Analytics & Exec', icon: BarChart3, badge: '✨', badgeColor: '#F59E0B' },
    { id: 'social_analytics', label: 'Social & Ads', icon: Share2, badge: 'META', badgeColor: '#6366F1' },
    { id: 'content', label: 'Content Engine', icon: Sparkles }
  ];

  // Universal navigation items with role-based visibility (chat and social & ads removed from admin)
  const universalNavItems = [
    { id: 'overview', label: 'Dashboard', icon: Home, roles: ['admin', 'viewer'] },
    { id: 'knowledge', label: 'Documents', icon: BookOpen, roles: ['admin', 'developer'] },
    { id: 'properties', label: 'Properties', icon: Building2, roles: ['admin', 'agent', 'viewer'] },
    { id: 'conversations', label: 'Live Chats', icon: MessageSquare, roles: ['agent'], badge: 'LIVE', badgeColor: '#10B981', dot: true },
    { id: 'social_analytics', label: 'Social & Ads', icon: Share2, roles: ['agent'], badge: 'META', badgeColor: '#6366F1' },
    { id: 'content', label: 'Content Engine', icon: Sparkles, roles: ['agent'] },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, roles: ['admin'] },
    { id: 'developer_console', label: 'Developer', icon: Terminal, roles: ['developer'] },
    { id: 'ai_customization', label: 'AI Studio', icon: SlidersHorizontal, roles: ['developer'], badge: 'PRO', badgeColor: '#E8654A' },
    { id: 'n8n_monitoring', label: 'n8n Health', icon: Workflow, roles: ['developer'] },
  ];

  const isDark = theme === 'dark';

  const visibleNavItems = userRole === 'manager' 
    ? managerNavItems 
    : universalNavItems.filter(item => !item.roles || item.roles.includes(userRole));

  return (
    <aside style={{
      width: '78px',
      minWidth: '78px',
      height: '100vh',
      maxHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 0',
      position: 'sticky',
      top: 0,
      left: 0,
      flexShrink: 0,
      zIndex: 50,
      userSelect: 'none',
      background: 'transparent',
      border: 'none',
      overflow: 'visible'
    }}>
      {/* Top: Brand Logo */}
      <div 
        title="GLG Assets Platform"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          cursor: 'pointer',
          paddingTop: '4px'
        }}
        onClick={() => setActiveTab('overview')}
      >
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, var(--primary-coral, #E8654A), #FF8566)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 14px rgba(232, 101, 74, 0.4)',
          transition: 'transform 0.2s ease'
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.08)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          <Zap size={20} color="#FFFFFF" />
        </div>
      </div>

      {/* Middle: Glassmorphic Floating Capsule Dock (Reference Matching) */}
      <div style={{
        margin: 'auto 0',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        position: 'relative'
      }}>
        <nav 
          aria-label="Main Navigation"
          style={{
            width: '54px',
            borderRadius: '36px',
            background: isDark 
              ? 'rgba(30, 32, 48, 0.65)' 
              : 'rgba(255, 255, 255, 0.78)',
            backdropFilter: 'blur(24px) saturate(190%)',
            WebkitBackdropFilter: 'blur(24px) saturate(190%)',
            border: isDark 
              ? '1px solid rgba(255, 255, 255, 0.16)' 
              : '1px solid rgba(255, 255, 255, 0.95)',
            boxShadow: isDark 
              ? '0 16px 40px rgba(0, 0, 0, 0.35), inset 0 1px 1px rgba(255, 255, 255, 0.2)' 
              : '0 12px 32px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04), inset 0 1px 2px #FFFFFF',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 5px',
            transition: 'background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease'
          }}
        >
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            const isHovered = hoveredItem === item.id;
            const isAiStudio = item.id === 'ai_customization';

            // Selected category section in AI Studio flyout
            const selectedFlyoutSection = isAiStudio
              ? (CONTROL_PLANE_SECTIONS.find((s) => (s.category || s.id) === activeFlyoutCategory) ||
                 CONTROL_PLANE_SECTIONS.find((s) => s.category === 'AGENTS') ||
                 CONTROL_PLANE_SECTIONS[1])
              : null;

            return (
              <div 
                key={item.id} 
                style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <button
                  id={`nav-item-${item.id}`}
                  data-testid={`nav-item-${item.id}`}
                  onClick={() => {
                    setActiveTab(item.id);
                    setHoveredItem(null);
                    setAiFlyoutOpen(false);
                  }}
                  onMouseEnter={() => {
                    if (isAiStudio) {
                      handleAiButtonEnter();
                    } else {
                      if (flyoutTimerRef.current) clearTimeout(flyoutTimerRef.current);
                      setAiFlyoutOpen(false);
                      setHoveredItem(item.id);
                    }
                  }}
                  onMouseLeave={() => {
                    if (isAiStudio) {
                      handleAiButtonLeave();
                    } else {
                      setHoveredItem(null);
                    }
                  }}
                  aria-label={item.label}
                  aria-current={isActive ? 'page' : undefined}
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '50%',
                    border: isActive 
                      ? (isDark ? '1px solid rgba(255, 255, 255, 0.35)' : '1px solid rgba(0, 0, 0, 0.08)')
                      : '1px solid transparent',
                    background: isActive 
                      ? (isDark ? 'rgba(255, 255, 255, 0.22)' : '#FFFFFF') 
                      : (isHovered ? (isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)') : 'transparent'),
                    backdropFilter: isActive ? 'blur(10px)' : 'none',
                    WebkitBackdropFilter: isActive ? 'blur(10px)' : 'none',
                    boxShadow: isActive 
                      ? (isDark 
                          ? '0 4px 14px rgba(0, 0, 0, 0.25), inset 0 1px 1px rgba(255, 255, 255, 0.45)' 
                          : '0 4px 14px rgba(0, 0, 0, 0.12), inset 0 1px 1px #FFFFFF')
                      : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    position: 'relative',
                    transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                    transform: isHovered && !isActive ? 'scale(1.08)' : 'scale(1)',
                    outline: 'none',
                    padding: 0
                  }}
                >
                  <Icon 
                    size={19} 
                    color={isActive 
                      ? (isDark ? '#FFFFFF' : 'var(--primary-coral, #E8654A)') 
                      : (isHovered 
                          ? (isDark ? '#FFFFFF' : '#0F172A') 
                          : (isDark ? 'rgba(255, 255, 255, 0.6)' : '#64748B'))
                    } 
                    strokeWidth={isActive ? 2.2 : 1.8}
                    style={{ transition: 'all 0.15s ease' }}
                  />

                  {/* Notification / Status Dot on Icon (matches reference image) */}
                  {(item.dot || item.badge === 'LIVE') && (
                    <span style={{
                      position: 'absolute',
                      top: '7px',
                      right: '7px',
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: item.badgeColor || '#10B981',
                      boxShadow: `0 0 8px ${item.badgeColor || '#10B981'}`,
                      border: isDark ? '1.5px solid rgba(26, 26, 42, 0.9)' : '1.5px solid #FFFFFF'
                    }} />
                  )}
                </button>

                {/* Floating Glass Tooltip for standard items */}
                {isHovered && !isAiStudio && (
                  <div style={{
                    position: 'absolute',
                    left: 'calc(100% + 14px)',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: isDark 
                      ? 'rgba(24, 27, 44, 0.96)' 
                      : 'rgba(255, 255, 255, 0.98)',
                    backdropFilter: 'blur(16px)',
                    WebkitBackdropFilter: 'blur(16px)',
                    border: isDark 
                      ? '1px solid rgba(255, 255, 255, 0.14)' 
                      : '1px solid rgba(0, 0, 0, 0.08)',
                    boxShadow: isDark 
                      ? '0 8px 24px rgba(0, 0, 0, 0.35)' 
                      : '0 8px 24px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04)',
                    color: isDark ? '#FFFFFF' : '#0F172A',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    pointerEvents: 'none',
                    zIndex: 100,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    animation: 'fadeIn 0.15s ease'
                  }}>
                    {/* Small Arrow indicator */}
                    <div style={{
                      position: 'absolute',
                      left: '-4px',
                      top: '50%',
                      transform: 'translateY(-50%) rotate(45deg)',
                      width: '8px',
                      height: '8px',
                      background: isDark ? 'rgba(24, 27, 44, 0.96)' : 'rgba(255, 255, 255, 0.98)',
                      borderLeft: isDark ? '1px solid rgba(255, 255, 255, 0.14)' : '1px solid rgba(0, 0, 0, 0.08)',
                      borderBottom: isDark ? '1px solid rgba(255, 255, 255, 0.14)' : '1px solid rgba(0, 0, 0, 0.08)'
                    }} />
                    <span>{item.label}</span>
                    {item.badge && (
                      <span style={{
                        fontSize: '0.62rem',
                        fontWeight: 800,
                        padding: '1px 5px',
                        borderRadius: '4px',
                        background: item.badgeColor || '#10B981',
                        color: '#FFFFFF'
                      }}>
                        {item.badge}
                      </span>
                    )}
                  </div>
                )}

                {/* Rich Cascading Flyout Menu for AI Studio */}
                {isAiStudio && aiFlyoutOpen && (
                  <div 
                    id="ai-studio-cascading-flyout"
                    onMouseEnter={handleFlyoutContainerEnter}
                    onMouseLeave={handleFlyoutContainerLeave}
                    style={{
                      position: 'absolute',
                      left: '100%',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      paddingLeft: '14px',
                      zIndex: 1000,
                      animation: 'flyoutFadeSlide 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
                      pointerEvents: 'auto'
                    }}
                  >
                    {/* Visual Pointing Indicator */}
                    <div style={{
                      position: 'absolute',
                      left: '9px',
                      top: '50%',
                      transform: 'translateY(-50%) rotate(45deg)',
                      width: '10px',
                      height: '10px',
                      background: isDark ? 'rgba(18, 20, 32, 0.98)' : '#F8FAFC',
                      borderLeft: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid rgba(0, 0, 0, 0.1)',
                      borderBottom: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid rgba(0, 0, 0, 0.1)',
                      zIndex: 3
                    }} />

                    {/* 2-Column Cascading Flyout Container */}
                    <div style={{
                      display: 'flex',
                      flexDirection: 'row',
                      borderRadius: '16px',
                      background: isDark ? 'rgba(18, 20, 32, 0.98)' : 'rgba(255, 255, 255, 0.99)',
                      backdropFilter: 'blur(28px) saturate(190%)',
                      WebkitBackdropFilter: 'blur(28px) saturate(190%)',
                      border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid rgba(0, 0, 0, 0.1)',
                      boxShadow: isDark 
                        ? '0 24px 64px -8px rgba(0, 0, 0, 0.75), 0 4px 18px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.12)' 
                        : '0 24px 64px -8px rgba(15, 23, 42, 0.18), 0 8px 24px rgba(15, 23, 42, 0.08), inset 0 1px 2px #FFFFFF',
                      overflow: 'hidden',
                      position: 'relative',
                      zIndex: 2,
                      minWidth: '465px',
                      maxWidth: '490px'
                    }}>
                      {/* Column 1: Main Categories */}
                      <div style={{
                        width: '185px',
                        minWidth: '185px',
                        padding: '12px 8px',
                        borderRight: isDark ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #F1F5F9',
                        background: isDark ? 'rgba(255, 255, 255, 0.02)' : '#F8FAFC',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '3px'
                      }}>
                        {/* Header */}
                        <div style={{
                          padding: '2px 8px 8px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          borderBottom: isDark ? '1px solid rgba(255, 255, 255, 0.06)' : '1px solid #E2E8F0',
                          marginBottom: '4px'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--primary-coral, #E8654A)' }} />
                            <span style={{
                              fontSize: '0.68rem',
                              fontWeight: 800,
                              textTransform: 'uppercase',
                              letterSpacing: '0.08em',
                              color: isDark ? 'rgba(255, 255, 255, 0.5)' : '#64748B'
                            }}>
                              AI Studio
                            </span>
                          </div>
                          <span style={{
                            fontSize: '0.58rem',
                            fontWeight: 800,
                            padding: '1px 5px',
                            borderRadius: '4px',
                            background: 'rgba(232, 101, 74, 0.12)',
                            color: 'var(--primary-coral, #E8654A)'
                          }}>
                            27 TOOLS
                          </span>
                        </div>

                        {/* Category List */}
                        {CONTROL_PLANE_SECTIONS.map((sec) => {
                          const SecIcon = sec.icon;
                          const catKey = sec.category || sec.id;
                          const isSelected = activeFlyoutCategory === catKey;
                          const isLive = sec.badge === 'LIVE';

                          return (
                            <div
                              key={catKey}
                              onMouseEnter={() => setActiveFlyoutCategory(catKey)}
                              onClick={() => {
                                if (sec.id === 'overview') {
                                  handleSelectSubcategory('overview');
                                } else if (sec.items?.length) {
                                  handleSelectSubcategory(sec.items[0].id);
                                }
                              }}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                padding: '8px 10px',
                                borderRadius: '12px',
                                cursor: 'pointer',
                                transition: 'all 0.14s ease',
                                background: isSelected 
                                  ? (isDark ? 'rgba(232, 101, 74, 0.22)' : 'rgba(232, 101, 74, 0.1)') 
                                  : 'transparent',
                                color: isSelected 
                                  ? 'var(--primary-coral, #E8654A)' 
                                  : (isDark ? 'rgba(255, 255, 255, 0.82)' : '#334155'),
                                fontWeight: isSelected ? 700 : 500,
                                fontSize: '0.78rem'
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <SecIcon 
                                  size={15} 
                                  color={isSelected ? 'var(--primary-coral, #E8654A)' : (isDark ? 'rgba(255, 255, 255, 0.55)' : '#64748B')} 
                                />
                                <span>{sec.label}</span>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                {isLive && (
                                  <span style={{ fontSize: '0.56rem', fontWeight: 800, padding: '1px 6px', borderRadius: '20px', background: '#10B981', color: '#FFF' }}>
                                    LIVE
                                  </span>
                                )}
                                {sec.count && (
                                  <span style={{
                                    fontSize: '0.62rem',
                                    fontWeight: 700,
                                    padding: '2px 7px',
                                    borderRadius: '20px',
                                    background: isSelected ? 'rgba(232, 101, 74, 0.22)' : (isDark ? 'rgba(255, 255, 255, 0.08)' : '#E2E8F0'),
                                    color: isSelected ? 'var(--primary-coral, #E8654A)' : (isDark ? 'rgba(255, 255, 255, 0.6)' : '#64748B')
                                  }}>
                                    {sec.count}
                                  </span>
                                )}
                                <ChevronRight 
                                  size={13} 
                                  style={{ 
                                    opacity: isSelected ? 1 : 0.35, 
                                    transform: isSelected ? 'translateX(2px)' : 'none', 
                                    transition: 'all 0.15s ease' 
                                  }} 
                                />
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Column 2: Subcategories for Active Category */}
                      <div style={{
                        flex: 1,
                        padding: '12px 12px',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        background: isDark ? 'rgba(18, 20, 32, 0.98)' : '#FFFFFF'
                      }}>
                        <div>
                          {/* Subcategory Header */}
                          <div style={{
                            padding: '2px 4px 8px',
                            borderBottom: isDark ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid #F1F5F9',
                            marginBottom: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between'
                          }}>
                            <span style={{ fontSize: '0.74rem', fontWeight: 700, color: isDark ? '#FFFFFF' : '#1E293B' }}>
                              {selectedFlyoutSection?.label} Modules
                            </span>
                            <span style={{ fontSize: '0.64rem', color: isDark ? 'rgba(255, 255, 255, 0.45)' : '#94A3B8' }}>
                              {selectedFlyoutSection?.items?.length ? `${selectedFlyoutSection.items.length} tools available` : 'Live Dashboard'}
                            </span>
                          </div>

                          {/* Render Subcategories or Overview Card */}
                          {(!selectedFlyoutSection?.items || selectedFlyoutSection.id === 'overview' || selectedFlyoutSection.category === 'OVERVIEW') ? (
                            <div style={{
                              padding: '16px 14px',
                              borderRadius: '16px',
                              background: isDark ? 'rgba(255, 255, 255, 0.03)' : '#F8FAFC',
                              border: isDark ? '1px solid rgba(255, 255, 255, 0.07)' : '1px solid #E2E8F0',
                              display: 'flex',
                              flexDirection: 'column',
                              gap: '8px'
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: isDark ? '#FFFFFF' : '#0F172A' }}>
                                  Real-Time AI Telemetry
                                </span>
                                <span style={{ fontSize: '0.6rem', fontWeight: 800, padding: '2px 8px', borderRadius: '20px', background: '#10B981', color: '#FFF' }}>
                                  LIVE
                                </span>
                              </div>
                              <p style={{ margin: 0, fontSize: '0.72rem', color: isDark ? 'rgba(255, 255, 255, 0.6)' : '#64748B', lineHeight: 1.4 }}>
                                Live metrics, token consumption (USD & BDT), P50/P95/P99 latency, provider statuses, and active agent execution runs.
                              </p>
                              <button
                                onClick={() => handleSelectSubcategory('overview')}
                                style={{
                                  marginTop: '8px',
                                  padding: '10px 14px',
                                  borderRadius: '14px',
                                  background: 'var(--primary-coral, #E8654A)',
                                  color: '#FFFFFF',
                                  border: 'none',
                                  fontWeight: 700,
                                  fontSize: '0.75rem',
                                  cursor: 'pointer',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  gap: '6px',
                                  boxShadow: '0 4px 12px rgba(232, 101, 74, 0.3)'
                                }}
                              >
                                <span>Open AI Overview</span>
                                <ArrowRight size={13} />
                              </button>
                            </div>
                          ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                              {selectedFlyoutSection.items.map((sub) => {
                                const SubIcon = sub.icon;
                                return (
                                  <div
                                    key={sub.id}
                                    id={`flyout-sub-${sub.id}`}
                                    onClick={() => handleSelectSubcategory(sub.id)}
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '10px',
                                      padding: '8px 10px',
                                      borderRadius: '12px',
                                      cursor: 'pointer',
                                      transition: 'all 0.15s ease',
                                      background: 'transparent'
                                    }}
                                    onMouseEnter={(e) => {
                                      e.currentTarget.style.background = isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(232, 101, 74, 0.07)';
                                      e.currentTarget.style.transform = 'translateX(2px)';
                                    }}
                                    onMouseLeave={(e) => {
                                      e.currentTarget.style.background = 'transparent';
                                      e.currentTarget.style.transform = 'translateX(0)';
                                    }}
                                  >
                                    <div style={{
                                      width: '28px',
                                      height: '28px',
                                      borderRadius: '10px',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      background: 'rgba(232, 101, 74, 0.1)',
                                      color: 'var(--primary-coral, #E8654A)',
                                      flexShrink: 0
                                    }}>
                                      <SubIcon size={14} />
                                    </div>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <span style={{ fontSize: '0.77rem', fontWeight: 600, color: isDark ? '#FFFFFF' : '#0F172A', whiteSpace: 'nowrap' }}>
                                          {sub.label}
                                        </span>
                                        {sub.badge && (
                                          <span style={{
                                            fontSize: '0.56rem',
                                            fontWeight: 800,
                                            padding: '2px 6px',
                                            borderRadius: '20px',
                                            background: sub.badge === 'SANDBOX' ? '#3B82F6' : '#E8654A',
                                            color: '#FFFFFF'
                                          }}>
                                            {sub.badge}
                                          </span>
                                        )}
                                      </div>
                                      <div style={{
                                        fontSize: '0.66rem',
                                        color: isDark ? 'rgba(255, 255, 255, 0.5)' : '#64748B',
                                        whiteSpace: 'nowrap',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis'
                                      }}>
                                        {sub.desc}
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      {/* Bottom: Glass Utility Capsule (Theme, Support, Logout) */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '4px',
        paddingBottom: '4px'
      }}>
        {/* Theme Toggle */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={toggleTheme}
            onMouseEnter={() => setHoveredItem('theme_toggle')}
            onMouseLeave={() => setHoveredItem(null)}
            aria-label={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              border: 'none',
              background: hoveredItem === 'theme_toggle' ? (isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.06)') : 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            {theme === 'dark' ? <Sun size={17} color="#FBBF24" /> : <Moon size={17} color={isDark ? '#9CA3AF' : '#64748B'} />}
          </button>
          {hoveredItem === 'theme_toggle' && (
            <div style={{
              position: 'absolute',
              left: 'calc(100% + 14px)',
              top: '50%',
              transform: 'translateY(-50%)',
              background: isDark ? 'rgba(24, 27, 44, 0.96)' : 'rgba(255, 255, 255, 0.98)',
              backdropFilter: 'blur(14px)',
              WebkitBackdropFilter: 'blur(14px)',
              border: isDark ? '1px solid rgba(255, 255, 255, 0.14)' : '1px solid rgba(0, 0, 0, 0.08)',
              boxShadow: isDark 
                ? '0 8px 24px rgba(0, 0, 0, 0.35)' 
                : '0 8px 24px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04)',
              color: isDark ? '#FFFFFF' : '#0F172A',
              padding: '5px 10px',
              borderRadius: '8px',
              fontSize: '0.74rem',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
              zIndex: 100
            }}>
              {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            </div>
          )}
        </div>

        {/* Support Help */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => window.open('https://glgassets.com', '_blank')}
            onMouseEnter={() => setHoveredItem('support_help')}
            onMouseLeave={() => setHoveredItem(null)}
            aria-label="Support & Documentation"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              border: 'none',
              background: hoveredItem === 'support_help' ? (isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.06)') : 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <HelpCircle size={17} color={isDark ? '#9CA3AF' : '#64748B'} />
          </button>
          {hoveredItem === 'support_help' && (
            <div style={{
              position: 'absolute',
              left: 'calc(100% + 14px)',
              top: '50%',
              transform: 'translateY(-50%)',
              background: isDark ? 'rgba(24, 27, 44, 0.96)' : 'rgba(255, 255, 255, 0.98)',
              backdropFilter: 'blur(14px)',
              WebkitBackdropFilter: 'blur(14px)',
              border: isDark ? '1px solid rgba(255, 255, 255, 0.14)' : '1px solid rgba(0, 0, 0, 0.08)',
              boxShadow: isDark 
                ? '0 8px 24px rgba(0, 0, 0, 0.35)' 
                : '0 8px 24px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04)',
              color: isDark ? '#FFFFFF' : '#0F172A',
              padding: '5px 10px',
              borderRadius: '8px',
              fontSize: '0.74rem',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
              zIndex: 100
            }}>
              Support
            </div>
          )}
        </div>

        {/* Logout */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={logout}
            onMouseEnter={() => setHoveredItem('logout_btn')}
            onMouseLeave={() => setHoveredItem(null)}
            aria-label="Log Out"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              border: 'none',
              background: hoveredItem === 'logout_btn' ? (isDark ? 'rgba(239, 68, 68, 0.15)' : 'rgba(239, 68, 68, 0.1)') : 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <LogOut size={16} color="#EF4444" />
          </button>
          {hoveredItem === 'logout_btn' && (
            <div style={{
              position: 'absolute',
              left: 'calc(100% + 14px)',
              top: '50%',
              transform: 'translateY(-50%)',
              background: isDark ? 'rgba(24, 27, 44, 0.96)' : 'rgba(255, 255, 255, 0.98)',
              backdropFilter: 'blur(14px)',
              WebkitBackdropFilter: 'blur(14px)',
              border: isDark ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(239, 68, 68, 0.2)',
              boxShadow: isDark 
                ? '0 8px 24px rgba(0, 0, 0, 0.35)' 
                : '0 8px 24px rgba(239, 68, 68, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04)',
              color: '#EF4444',
              padding: '5px 10px',
              borderRadius: '8px',
              fontSize: '0.74rem',
              fontWeight: 600,
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
              zIndex: 100
            }}>
              Log Out
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
