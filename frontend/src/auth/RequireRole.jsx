import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { canAccessTab } from './routeAccess';

/** Renders children only for roles allowed on `tab`; otherwise redirects to `fallbackPath`. */
export default function RequireRole({ tab, fallbackPath, children }) {
  const { user } = useAuth();
  if (canAccessTab(user?.role, tab)) return children;
  return <Navigate to={fallbackPath || '/overview'} replace />;
}
