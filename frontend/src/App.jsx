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
    switch (activeTab) {
      case 'overview': return <DashboardHome setActiveTab={setActiveTab} />;
      case 'developer_console': 
        return user?.role === 'developer' 
          ? <DeveloperConsolePage setActiveParentTab={setActiveTab} /> 
          : <DashboardHome setActiveTab={setActiveTab} />;
      case 'conversations': return <ConversationsPage />;
      case 'email_inbox': return <EmailInboxPage />;
      case 'knowledge': return <KnowledgePage />;
      case 'content': return <ContentGeneratorPage />;
      case 'properties': return <PropertiesPage />;
      case 'analytics': return <AnalyticsPage />;
      case 'n8n_monitoring': return <N8nMonitoringPage />;
      default: return <DashboardHome setActiveTab={setActiveTab} />;
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
