import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Bell, 
  RotateCw, 
  LogOut, 
  Sun, 
  Moon, 
  User, 
  X,
  Sparkles
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import CustomDropdown from '../ui/CustomDropdown';
import { getProjects } from '../../services/api';

export default function Header({ 
  activeTab = "overview",
  setActiveTab,
  activeTabTitle = "Dashboard",
  selectedProperty = "all",
  onChangeProperty,
  selectedChannel = "all",
  onChangeChannel,
  dateRange = "30d",
  onChangeDateRange,
  searchQuery = "",
  onChangeSearchQuery
}) {
  const { user, logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('glg_theme') || 'light');
  const [dynamicPropertyOptions, setDynamicPropertyOptions] = useState([
    { value: 'all', label: 'All Properties' },
    { value: 'gulshan_heights', label: 'GLG Gulshan Heights' },
    { value: 'luxe_baridhara', label: 'Baridhara Diplomatic Luxe' },
    { value: 'banani_crest', label: 'Banani Crest Towers' },
    { value: 'dhanmondi_oasis', label: 'Dhanmondi Lake Oasis' },
    { value: 'uttara_sector3', label: 'Uttara Heights Sector 3' }
  ]);

  useEffect(() => {
    const handleStorage = () => {
      setTheme(localStorage.getItem('glg_theme') || 'light');
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen(prev => !prev);
      }
      if (e.key === 'Escape') {
        setIsSearchOpen(false);
        setShowNotifications(false);
        setShowProfileMenu(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const isDark = theme === 'dark';

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('glg_theme', next);
  };

  useEffect(() => {
    let isMounted = true;
    async function loadProperties() {
      try {
        const res = await getProjects();
        const list = Array.isArray(res) ? res : (res?.projects || []);
        if (list.length > 0 && isMounted) {
          const opts = [{ value: 'all', label: 'All Properties' }];
          list.forEach((p) => {
            const val = (p.project_id || p.id || p.name).toLowerCase().replace(/[^a-z0-9]/g, '_');
            const name = p.project_name || p.title || p.name;
            if (!opts.find(o => o.value === val)) {
              opts.push({ value: val, label: name });
            }
          });
          setDynamicPropertyOptions(opts);
        }
      } catch (err) {
        // Fallback to initial defaults
      }
    }
    loadProperties();
    return () => { isMounted = false; };
  }, []);

  const channelOptions = [
    { value: 'all', label: 'All Channels' },
    { value: 'whatsapp', label: 'WhatsApp Business' },
    { value: 'website', label: 'Website LiveChat' },
    { value: 'facebook', label: 'Facebook Messenger' },
    { value: 'instagram', label: 'Instagram Direct' }
  ];

  const dateRangeOptions = [
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'This Quarter' },
    { value: '1y', label: 'This Year' },
    { value: 'all', label: 'All Time' }
  ];

  const hasActiveFilters = searchQuery.trim() !== '' || selectedProperty !== 'all' || selectedChannel !== 'all' || dateRange !== '30d';

  return (
    <header style={{
      height: '64px',
      flexShrink: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 28px',
      background: 'transparent',
      backdropFilter: 'none',
      WebkitBackdropFilter: 'none',
      borderBottom: 'none',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }}>
      {/* ── Left: Connected Node Brand Mark (Matches Reference Image) ── */}
      <div 
        onClick={() => setActiveTab && setActiveTab('overview')}
        style={{
          display: 'flex',
          alignItems: 'center',
          cursor: 'pointer',
          color: isDark ? '#FFFFFF' : '#0F172A',
          transition: 'transform 0.2s ease'
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.08)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        title="GLG Assets Home"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="5" cy="12" r="3.5" fill="currentColor" />
          <circle cx="16" cy="5.5" r="3" fill="currentColor" />
          <circle cx="16" cy="18.5" r="3" fill="currentColor" />
          <path d="M8 10.5L13.5 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M8 13.5L13.5 17" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        </svg>
      </div>

      {/* ── Middle: Search Bar & Filters (Replaces Capsule Nav Bar per User Request) ── */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        flex: 1,
        maxWidth: '820px',
        justifyContent: 'center'
      }}>
        {/* Search Input Box */}
        <div style={{ position: 'relative', width: '310px' }}>
          <Search 
            size={15} 
            color="var(--text-muted, #94A3B8)" 
            style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} 
          />
          <input
            type="text"
            placeholder="Search leads, projects, documents..."
            value={searchQuery}
            onChange={(e) => onChangeSearchQuery && onChangeSearchQuery(e.target.value)}
            className="glass-input"
            id="header-global-search"
            style={{ 
              paddingLeft: '34px', 
              paddingRight: searchQuery ? '30px' : '10px',
              width: '100%', 
              height: '38px',
              borderRadius: '10px',
              fontSize: '0.82rem'
            }}
          />
          {searchQuery && (
            <button
              onClick={() => onChangeSearchQuery && onChangeSearchQuery('')}
              style={{
                position: 'absolute',
                right: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                padding: '2px'
              }}
              title="Clear search"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Filter 1: Properties */}
        <CustomDropdown
          value={selectedProperty}
          onChange={(val) => onChangeProperty && onChangeProperty(val)}
          options={dynamicPropertyOptions}
          minWidth="150px"
          buttonStyle={{ height: '38px', borderRadius: '10px' }}
          ariaLabel="Select Property"
        />

        {/* Filter 2: Channels */}
        <CustomDropdown
          value={selectedChannel}
          onChange={(val) => onChangeChannel && onChangeChannel(val)}
          options={channelOptions}
          minWidth="140px"
          buttonStyle={{ height: '38px', borderRadius: '10px' }}
          ariaLabel="Select Channel"
        />

        {/* Filter 3: Date Range */}
        <CustomDropdown
          value={dateRange}
          onChange={(val) => onChangeDateRange && onChangeDateRange(val)}
          options={dateRangeOptions}
          minWidth="125px"
          buttonStyle={{ height: '38px', borderRadius: '10px' }}
          ariaLabel="Select Date Range"
        />

        {/* Clear Filters / Dismiss Button */}
        {hasActiveFilters && (
          <button
            onClick={() => {
              onChangeSearchQuery && onChangeSearchQuery('');
              onChangeProperty && onChangeProperty('all');
              onChangeChannel && onChangeChannel('all');
              onChangeDateRange && onChangeDateRange('30d');
            }}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '6px',
              borderRadius: '50%',
              transition: 'color 0.15s ease'
            }}
            title="Reset all filters"
            onMouseEnter={(e) => e.currentTarget.style.color = 'var(--primary-coral, #E8654A)'}
            onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* ── Right: Circular Actions (Refresh, Notifications, Avatar) ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Circle 1: Refresh Action Button */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => {
              setIsRefreshing(true);
              setTimeout(() => setIsRefreshing(false), 800);
            }}
            title="Refresh Data & KPIs"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid rgba(0, 0, 0, 0.08)',
              background: isDark ? 'rgba(255, 255, 255, 0.1)' : '#E5E7EB',
              color: isDark ? '#FFFFFF' : '#1E293B',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              position: 'relative',
              transition: 'all 0.15s ease'
            }}
          >
            <RotateCw 
              size={15} 
              style={{
                animation: isRefreshing ? 'spin 0.8s linear infinite' : 'none',
                transition: 'transform 0.2s ease'
              }} 
            />
          </button>
        </div>

        {/* Circle 2: Notifications Button */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowNotifications(prev => !prev)}
            title="Notifications & Alerts"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              border: isDark ? '1px solid rgba(255, 255, 255, 0.15)' : '1px solid rgba(0, 0, 0, 0.08)',
              background: isDark 
                ? (showNotifications ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)') 
                : (showNotifications ? '#D1D5DB' : '#E5E7EB'),
              color: isDark ? '#FFFFFF' : '#1E293B',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              position: 'relative',
              transition: 'all 0.15s ease'
            }}
          >
            <Bell size={15} />
            <span style={{
              position: 'absolute',
              top: '8px',
              right: '8px',
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              background: '#EF4444',
              boxShadow: '0 0 6px #EF4444'
            }} />
          </button>

          {/* Notifications Dropdown */}
          {showNotifications && (
            <div style={{
              position: 'absolute',
              top: '46px',
              right: '0',
              width: '320px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-glass)',
              boxShadow: 'var(--shadow-dropdown)',
              borderRadius: '12px',
              padding: '14px',
              zIndex: 100,
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-glass)', paddingBottom: '8px' }}>
                <span style={{ fontWeight: 800, fontSize: '0.85rem', color: 'var(--text-main)' }}>Notifications & Alerts</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>3 Unread</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ padding: '8px 10px', borderRadius: '8px', background: 'rgba(232, 101, 74, 0.08)', border: '1px solid rgba(232, 101, 74, 0.2)' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)' }}>🔥 New High-Priority Lead</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Tanvir Ahmed requested tour of Gulshan Heights via WhatsApp.</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '2px' }}>12 mins ago</div>
                </div>
                <div style={{ padding: '8px 10px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)' }}>✅ Site Tour Confirmed</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Booking BK-2026-8812 assigned to Sarah Connor.</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '2px' }}>45 mins ago</div>
                </div>
                <div style={{ padding: '8px 10px', borderRadius: '8px', background: 'var(--bg-card-hover)', border: '1px solid var(--border-glass)' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)' }}>⚡ Multi-Agent Sync</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>All 6 n8n workflows operational with 18ms latency.</div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '2px' }}>2 hrs ago</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Circle 3: Profile Avatar Button */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowProfileMenu(prev => !prev)}
            title="User Profile & Settings"
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              border: isDark ? '1.5px solid rgba(255, 255, 255, 0.3)' : '1.5px solid rgba(0, 0, 0, 0.12)',
              background: '#E5E7EB',
              padding: 0,
              overflow: 'hidden',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
              transition: 'transform 0.15s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = 'scale(1.06)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <img 
              src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=120&auto=format&fit=crop&q=80" 
              alt={user?.full_name || 'Sarah Connor'}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              onError={(e) => {
                e.target.style.display = 'none';
                if (e.target.parentElement) {
                  e.target.parentElement.innerHTML = '<span style="font-size:0.75rem;font-weight:700;color:#0F172A">SC</span>';
                }
              }}
            />
          </button>

          {/* Profile Menu Popover */}
          {showProfileMenu && (
            <div style={{
              position: 'absolute',
              top: '46px',
              right: '0',
              width: '230px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-glass)',
              boxShadow: 'var(--shadow-dropdown)',
              borderRadius: '12px',
              padding: '12px',
              zIndex: 100,
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingBottom: '8px', borderBottom: '1px solid var(--border-glass)' }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  overflow: 'hidden',
                  background: '#E5E7EB'
                }}>
                  <img 
                    src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=120&auto=format&fit=crop&q=80" 
                    alt="Profile" 
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    {user?.full_name || 'Sarah Connor'}
                  </span>
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                    {user?.role ? user.role.toUpperCase() : 'MANAGER'}
                  </span>
                </div>
              </div>

              {/* Theme Toggle in Menu */}
              <button
                onClick={toggleTheme}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '7px 10px',
                  borderRadius: '8px',
                  border: 'none',
                  background: 'transparent',
                  color: 'var(--text-main)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  width: '100%',
                  textAlign: 'left',
                  transition: 'background 0.15s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-card-hover)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                {isDark ? <Sun size={15} color="#FBBF24" /> : <Moon size={15} color="#64748B" />}
                <span>{isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}</span>
              </button>

              {/* Logout button */}
              <button
                onClick={logout}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '7px 10px',
                  borderRadius: '8px',
                  border: 'none',
                  background: 'rgba(239, 68, 68, 0.08)',
                  color: '#EF4444',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  width: '100%',
                  textAlign: 'left',
                  transition: 'background 0.15s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.08)'}
              >
                <LogOut size={15} color="#EF4444" />
                <span>Log Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
