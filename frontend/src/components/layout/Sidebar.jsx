import { 
  LayoutDashboard, 
  MessageSquare, 
  BookOpen, 
  Share2, 
  Building2, 
  BarChart3, 
  Sparkles,
  Zap,
  Lock,
  Mail
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar({ activeTab, setActiveTab }) {
  const { user } = useAuth();
  const userRole = user?.role || 'viewer';

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard, roles: ['admin', 'manager', 'agent', 'viewer'] },
    { id: 'conversations', label: 'Live Chats', icon: MessageSquare, badge: 'LIVE', roles: ['admin', 'manager', 'agent'] },
    { id: 'email_inbox', label: 'Email Inbox', icon: Mail, badge: 'AI DRAFT', roles: ['admin', 'manager', 'agent'] },
    { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen, roles: ['admin', 'manager'] },
    { id: 'content', label: 'Content Engine', icon: Share2, roles: ['admin', 'manager'] },
    { id: 'properties', label: 'Properties', icon: Building2, roles: ['admin', 'manager', 'agent', 'viewer'] },
    { id: 'analytics', label: 'Analytics & Exec', icon: BarChart3, highlight: true, roles: ['admin', 'manager'] },
  ];

  const visibleNavItems = navItems.filter(item => item.roles.includes(userRole));

  return (
    <aside style={{
      width: '260px',
      background: 'rgba(11, 15, 25, 0.9)',
      borderRight: '1px solid var(--border-glass)',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 16px',
      minHeight: '100vh',
      backdropFilter: 'blur(20px)'
    }}>
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px 24px 8px', borderBottom: '1px solid var(--border-glass)' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'var(--grad-violet)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 16px rgba(139, 92, 246, 0.5)'
        }}>
          <Zap size={22} color="#FFFFFF" />
        </div>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, background: 'linear-gradient(135deg, #FFFFFF, #9CA3AF)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            GLG Assets
          </h2>
          <span style={{ fontSize: '0.7rem', color: '#10B981', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span className="pulse-online" /> Real Estate AI Engine
          </span>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '24px' }}>
        {visibleNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                borderRadius: '12px',
                border: isActive ? '1px solid rgba(139, 92, 246, 0.4)' : '1px solid transparent',
                background: isActive ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
                color: isActive ? '#FFFFFF' : 'var(--text-muted)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.9rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: isActive ? '0 4px 20px rgba(139, 92, 246, 0.2)' : 'none'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Icon size={18} color={isActive ? '#C084FC' : 'var(--text-muted)'} />
                <span>{item.label}</span>
              </div>
              
              {item.badge && (
                <span style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '6px',
                  background: 'rgba(16, 185, 129, 0.2)',
                  color: '#34D399',
                  border: '1px solid rgba(16, 185, 129, 0.3)'
                }}>
                  {item.badge}
                </span>
              )}
              
              {item.highlight && !isActive && (
                <Sparkles size={14} color="#FBBF24" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Role Notice Footer (Admin Only) */}
      {userRole === 'admin' && (
        <div style={{
          marginTop: 'auto',
          padding: '16px',
          background: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '14px',
          border: '1px solid var(--border-glass)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <span>Active Role</span>
            <span style={{ color: '#C084FC', fontWeight: 700, textTransform: 'capitalize' }}>{userRole}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <span>RBAC Guard</span>
            <span style={{ color: '#34D399', fontWeight: 600 }}>Enforced</span>
          </div>
        </div>
      )}
    </aside>
  );
}
