import React, { useState, useEffect } from 'react';
import { 
  Home,
  LayoutDashboard, 
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
  Zap 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar({ activeTab, setActiveTab }) {
  const { user, logout } = useAuth();
  const userRole = user?.role || 'viewer';
  const [hoveredItem, setHoveredItem] = useState(null);

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
      overflowY: 'auto',
      scrollbarWidth: 'none',
      msOverflowStyle: 'none'
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

            return (
              <div 
                key={item.id} 
                style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <button
                  id={`nav-item-${item.id}`}
                  data-testid={`nav-item-${item.id}`}
                  onClick={() => setActiveTab(item.id)}
                  onMouseEnter={() => setHoveredItem(item.id)}
                  onMouseLeave={() => setHoveredItem(null)}
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

                {/* Floating Glass Tooltip to the Right */}
                {isHovered && (
                  <div style={{
                    position: 'absolute',
                    left: 'calc(100% + 14px)',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'rgba(18, 20, 32, 0.92)',
                    backdropFilter: 'blur(14px)',
                    WebkitBackdropFilter: 'blur(14px)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.45)',
                    color: '#FFFFFF',
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
                      left: '-5px',
                      top: '50%',
                      transform: 'translateY(-50%) rotate(45deg)',
                      width: '8px',
                      height: '8px',
                      background: 'rgba(18, 20, 32, 0.92)',
                      borderLeft: '1px solid rgba(255, 255, 255, 0.15)',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.15)'
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
              background: 'rgba(18, 20, 32, 0.92)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#FFFFFF',
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
              background: 'rgba(18, 20, 32, 0.92)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#FFFFFF',
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
              background: 'rgba(18, 20, 32, 0.92)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
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
