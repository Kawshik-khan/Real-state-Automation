/**
 * Which roles may open each dashboard area. The server enforces authorization on every
 * API call; this keeps users out of consoles they cannot use (menu hiding alone is
 * bypassed by typing the URL). Mirrors Sidebar navigation plus backend permissions.
 */
export const ROUTE_ROLES = {
  overview: ['admin', 'manager', 'agent', 'developer', 'viewer'],
  properties: ['admin', 'manager', 'agent', 'viewer'],
  conversations: ['admin', 'manager', 'agent'],
  inbox: ['admin', 'manager', 'agent'],
  content: ['admin', 'manager', 'agent'],
  social_analytics: ['admin', 'manager', 'agent'],
  analytics: ['admin', 'manager'],
  role_reports: ['admin', 'manager', 'developer'],
  knowledge: ['admin', 'developer'],
  developer_console: ['admin', 'developer'],
  ai_customization: ['admin', 'developer'],
  n8n_monitoring: ['admin', 'developer'],
};

export function canAccessTab(role, tabId) {
  return (ROUTE_ROLES[tabId] || []).includes(role);
}
