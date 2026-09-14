import React, { useState, useEffect, useMemo } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';

import DashboardHome from './pages/DashboardHome';
import ConversationsPage from './pages/ConversationsPage';
import KnowledgePage from './pages/KnowledgePage';
import ContentGeneratorPage from './pages/ContentGeneratorPage';
import PropertiesPage from './pages/PropertiesPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SocialAnalyticsPage from './pages/SocialAnalyticsPage';
import N8nMonitoringPage from './pages/N8nMonitoringPage';
import DeveloperConsolePage from './pages/DeveloperConsolePage';
import AgentCustomizationPage from './pages/AgentCustomizationPage';
import RoleReportsPage from './pages/RoleReportsPage';
import ManagerDashboardPage from './pages/ManagerDashboardPage';
import EmailInboxPage from './pages/EmailInboxPage';

import EditModulesModal from './components/dashboard/EditModulesModal';
import QuickChatDrawer from './components/dashboard/QuickChatDrawer';
import HexagonBackground from './components/layout/HexagonBackground';

const DEFAULT_MODULE_CONFIG = {
  kpis: true,
  chart: true,
  map: true,
  criticalDates: true,
  valuableProps: true,
  financialSummary: true
};

export const getDefaultTabForRole = (role) => {
  switch (role) {
    case 'developer':
      return 'developer_console';
    case 'agent':
      return 'conversations';
    case 'viewer':
      return 'properties';
    case 'manager':
      return 'overview';
    case 'admin':
    default:
      return 'overview';
  }
};

export const TAB_TO_PATH = {
  overview: '/overview',
  developer_console: '/developer',
  ai_customization: '/ai-studio',
  analytics: '/analytics',
  social_analytics: '/social-analytics',
  role_reports: '/reports',
  conversations: '/conversations',
  knowledge: '/knowledge',
  content: '/content',
  properties: '/properties',
  n8n_monitoring: '/n8n',
  inbox: '/inbox',
};

export const PATH_TO_TAB = {
  '/': 'overview',
  '/overview': 'overview',
  '/dashboard': 'overview',
  '/developer': 'developer_console',
  '/developer-console': 'developer_console',
  '/ai-studio': 'ai_customization',
  '/agent-customization': 'ai_customization',
  '/analytics': 'analytics',
  '/social-analytics': 'social_analytics',
  '/reports': 'role_reports',
  '/role-reports': 'role_reports',
  '/conversations': 'conversations',
  '/knowledge': 'knowledge',
  '/content': 'content',
  '/properties': 'properties',
  '/n8n': 'n8n_monitoring',
  '/n8n-monitoring': 'n8n_monitoring',
  '/inbox': 'inbox',
};

function DashboardApp() {
  const { user, isAuthenticated } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Resolve current active tab from browser URL path
  const getTabFromPath = (pathname) => {
    if (pathname.startsWith('/conversations')) return 'conversations';
    if (pathname.startsWith('/properties')) return 'properties';
    if (pathname.startsWith('/ai-studio') || pathname.startsWith('/agent-customization')) return 'ai_customization';
    if (pathname.startsWith('/developer')) return 'developer_console';
    if (pathname.startsWith('/social')) return 'social_analytics';
    if (pathname.startsWith('/n8n')) return 'n8n_monitoring';
    if (pathname.startsWith('/report')) return 'role_reports';
    return PATH_TO_TAB[pathname] || 'overview';
  };

  const activeTab = useMemo(() => getTabFromPath(location.pathname), [location.pathname]);

  // Navigate when a tab is selected (via Sidebar, Header, or quick actions)
  const handleSetActiveTab = (tabId) => {
    const targetPath = TAB_TO_PATH[tabId] || '/overview';
    if (location.pathname !== targetPath) {
      navigate(targetPath);
    }
  };

  // Dashboard Filters State
  const [selectedProperty, setSelectedProperty] = useState('all');
  const [selectedChannel, setSelectedChannel] = useState('all');
  const [dateRange, setDateRange] = useState('30d');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals & Drawer State
  const [isEditModulesOpen, setIsEditModulesOpen] = useState(false);
  const [isQuickChatOpen, setIsQuickChatOpen] = useState(false);

  // Module configuration with localStorage persistence
  const [moduleConfig, setModuleConfig] = useState(() => {
    try {
      const saved = localStorage.getItem('glg_dashboard_modules');
      return saved ? JSON.parse(saved) : DEFAULT_MODULE_CONFIG;
    } catch {
      return DEFAULT_MODULE_CONFIG;
    }
  });

  const handleSaveModuleConfig = (newConfig) => {
    setModuleConfig(newConfig);
    try {
      localStorage.setItem('glg_dashboard_modules', JSON.stringify(newConfig));
    } catch (err) {
      console.error('Failed to save dashboard config:', err);
    }
  };

  const handleResetDefaultModules = () => {
    setModuleConfig(DEFAULT_MODULE_CONFIG);
    try {
      localStorage.removeItem('glg_dashboard_modules');
    } catch (err) {
      console.error('Failed to reset dashboard config:', err);
    }
  };

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const getTabTitle = () => {
    switch (activeTab) {
      case 'overview': return 'Dashboard Overview';
      case 'developer_console': return 'Engineering & Developer Console';
      case 'ai_customization': return 'AI & Agent Customization Studio';
      case 'analytics': return 'Analytics & Executive Command Center';
      case 'social_analytics': return 'Social Media KPI & Campaign Analytics';
      case 'role_reports': return 'Executive Cross-Role Operational Reports';
      case 'conversations': return 'Live Customer Conversations & Takeover';
      case 'knowledge': return 'Knowledge Base & PDF OCR Manager';
      case 'content': return 'Social Content Generator & Approval Engine';
      case 'properties': return 'Property Inventory & Media Catalog';
      case 'n8n_monitoring': return 'n8n Workflow & Node Health Command';
      case 'inbox': return 'Email Inbox & Inbound Inquiries';
      default: return 'Dashboard Overview';
    }
  };

  const isDev = user?.role === 'developer';
  const isAdmin = user?.role === 'admin';
  const isManager = user?.role === 'manager';
  const isAgent = user?.role === 'agent';
  const isViewer = user?.role === 'viewer';

  const defaultRolePath = TAB_TO_PATH[getDefaultTabForRole(user?.role)] || '/overview';

  return (
    <div 
      className="app-shell" 
      style={{ 
        display: 'flex', 
        height: '100vh', 
        width: '100vw', 
        overflow: 'hidden', 
        background: 'var(--bg-dark)', 
        position: 'relative' 
      }}
    >
      {/* Interactive Hexagonal Background */}
      <HexagonBackground />

      {/* Sidebar Navigation (Fixed) */}
      <Sidebar activeTab={activeTab} setActiveTab={handleSetActiveTab} />

      {/* Main Content Area (Fixed Header + Scrollable Dashboard) */}
      <div 
        style={{ 
          flex: 1, 
          minWidth: 0, 
          height: '100vh', 
          display: 'flex', 
          flexDirection: 'column', 
          overflow: 'hidden', 
          position: 'relative', 
          zIndex: 1 
        }}
      >
        <Header 
          activeTab={activeTab}
          setActiveTab={handleSetActiveTab}
          activeTabTitle={getTabTitle()}
          onOpenEditModules={() => setIsEditModulesOpen(true)}
          onOpenQuickChat={() => setIsQuickChatOpen(true)}
          selectedProperty={selectedProperty}
          onChangeProperty={setSelectedProperty}
          selectedChannel={selectedChannel}
          onChangeChannel={setSelectedChannel}
          dateRange={dateRange}
          onChangeDateRange={setDateRange}
          searchQuery={searchQuery}
          onChangeSearchQuery={setSearchQuery}
        />
        <main 
          id="main-dashboard-scrollable" 
          style={{ 
            flex: 1, 
            minHeight: 0, 
            overflowY: 'auto', 
            overflowX: 'hidden' 
          }}
        >
          <Routes>
            <Route path="/" element={<Navigate to={defaultRolePath} replace />} />
            <Route 
              path="/overview" 
              element={
                isAgent ? <Navigate to="/conversations" replace /> :
                isManager ? <ManagerDashboardPage setActiveTab={handleSetActiveTab} /> :
                isDev ? <Navigate to="/developer" replace /> :
                <DashboardHome 
                  setActiveTab={handleSetActiveTab} 
                  moduleConfig={moduleConfig}
                  selectedProperty={selectedProperty}
                  selectedChannel={selectedChannel}
                  dateRange={dateRange}
                  searchQuery={searchQuery}
                />
              } 
            />
            <Route path="/dashboard" element={<Navigate to="/overview" replace />} />
            <Route path="/properties" element={<PropertiesPage searchQuery={searchQuery} />} />
            <Route path="/conversations" element={<ConversationsPage />} />
            <Route path="/conversations/:convId" element={<ConversationsPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="/content" element={<ContentGeneratorPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/social-analytics" element={<SocialAnalyticsPage />} />
            <Route path="/developer" element={<DeveloperConsolePage setActiveParentTab={handleSetActiveTab} />} />
            <Route path="/developer-console" element={<Navigate to="/developer" replace />} />
            <Route path="/ai-studio" element={<AgentCustomizationPage setActiveParentTab={handleSetActiveTab} />} />
            <Route path="/agent-customization" element={<Navigate to="/ai-studio" replace />} />
            <Route path="/n8n" element={<N8nMonitoringPage />} />
            <Route path="/n8n-monitoring" element={<Navigate to="/n8n" replace />} />
            <Route path="/reports" element={<RoleReportsPage />} />
            <Route path="/role-reports" element={<Navigate to="/reports" replace />} />
            <Route path="/inbox" element={<EmailInboxPage />} />
            <Route path="*" element={<Navigate to={defaultRolePath} replace />} />
          </Routes>
        </main>
      </div>

      {/* Global Modals & Drawers */}
      <EditModulesModal
        isOpen={isEditModulesOpen}
        onClose={() => setIsEditModulesOpen(false)}
        moduleConfig={moduleConfig}
        onSaveConfig={handleSaveModuleConfig}
        onResetDefault={handleResetDefaultModules}
      />

      <QuickChatDrawer
        isOpen={isQuickChatOpen}
        onClose={() => setIsQuickChatOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <DashboardApp />
    </AuthProvider>
  );
}
