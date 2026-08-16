import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';

import DashboardHome from './pages/DashboardHome';
import ConversationsPage from './pages/ConversationsPage';
import EmailInboxPage from './pages/EmailInboxPage';
import KnowledgePage from './pages/KnowledgePage';
import ContentGeneratorPage from './pages/ContentGeneratorPage';
import PropertiesPage from './pages/PropertiesPage';
import AnalyticsPage from './pages/AnalyticsPage';
import N8nMonitoringPage from './pages/N8nMonitoringPage';
import DeveloperConsolePage from './pages/DeveloperConsolePage';
import RoleReportsPage from './pages/RoleReportsPage';

const getDefaultTabForRole = (role) => {
  switch (role) {
    case 'developer':
      return 'developer_console'; // Forward Developer directly to Developer Console
    case 'agent':
      return 'conversations'; // Forward Agents directly to Live Conversations
    case 'viewer':
      return 'properties'; // Forward Viewers directly to Properties
    case 'manager':
      return 'overview'; // Forward Managers to Overview
    case 'admin':
    default:
      return 'overview'; // Forward Admins to Overview
  }
};

function DashboardApp() {
  const { user, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState(() => getDefaultTabForRole(user?.role));

  // Automatically verify role on login and forward user to their role location
  useEffect(() => {
    if (user?.role) {
      setActiveTab(getDefaultTabForRole(user.role));
    }
  }, [user?.role]);

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const getTabTitle = () => {
    switch (activeTab) {
      case 'overview': return 'Dashboard Overview';
      case 'developer_console': return 'Engineering & Developer Console';
      case 'role_reports': return 'Executive Cross-Role Operational Reports';
      case 'conversations': return 'Live Customer Conversations & Takeover';
      case 'email_inbox': return 'AI Email Inbox & n8n Reply Approval Center';
      case 'knowledge': return 'Knowledge Base & PDF OCR Manager';
      case 'content': return 'Social Content Generator & Approval Engine';
      case 'properties': return 'Property Inventory & Media Catalog';
      case 'analytics': return 'Analytics & Executive Command Center';
      case 'n8n_monitoring': return 'n8n Workflow & Node Health Command';
      default: return 'Dashboard Overview';
    }
  };

  const renderActivePage = () => {
    const isDev = user?.role === 'developer';
    const isAdmin = user?.role === 'admin';

    switch (activeTab) {
      case 'overview': 
        return <DashboardHome setActiveTab={setActiveTab} />;
      case 'developer_console': 
        return isDev 
          ? <DeveloperConsolePage setActiveParentTab={setActiveTab} /> 
          : <DashboardHome setActiveTab={setActiveTab} />;
      case 'role_reports': 
        return isAdmin 
          ? <RoleReportsPage /> 
          : <DashboardHome setActiveTab={setActiveTab} />;
      case 'analytics': 
        return isDev 
          ? <DeveloperConsolePage setActiveParentTab={setActiveTab} /> 
          : <AnalyticsPage />;
      case 'conversations': 
        return (isDev || isAdmin) 
          ? (isDev ? <DeveloperConsolePage setActiveParentTab={setActiveTab} /> : <DashboardHome setActiveTab={setActiveTab} />) 
          : <ConversationsPage />;
      case 'email_inbox': 
        return (isDev || isAdmin) 
          ? (isDev ? <DeveloperConsolePage setActiveParentTab={setActiveTab} /> : <DashboardHome setActiveTab={setActiveTab} />) 
          : <EmailInboxPage />;
      case 'knowledge': 
        return isAdmin 
          ? <DashboardHome setActiveTab={setActiveTab} /> 
          : <KnowledgePage />;
      case 'content': 
        return (isDev || isAdmin) 
          ? (isDev ? <DeveloperConsolePage setActiveParentTab={setActiveTab} /> : <DashboardHome setActiveTab={setActiveTab} />) 
          : <ContentGeneratorPage />;
      case 'properties': 
        return isDev 
          ? <DeveloperConsolePage setActiveParentTab={setActiveTab} /> 
          : <PropertiesPage />;
      case 'n8n_monitoring': 
        return isAdmin 
          ? <DashboardHome setActiveTab={setActiveTab} /> 
          : <N8nMonitoringPage />;
      default: 
        return <DashboardHome setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-dark)' }}>
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowX: 'hidden' }}>
        <Header activeTabTitle={getTabTitle()} />
        <main style={{ flex: 1, overflowY: 'auto' }}>
          {renderActivePage()}
        </main>
      </div>
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
