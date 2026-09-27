import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/auth';
import { getAccessToken, getSessionUser, onSessionChange } from '../services/session';
import { useIdleTimer } from '../hooks/useIdleTimer';
import IdleSessionModal from '../components/common/IdleSessionModal';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getSessionUser());
  const [token, setToken] = useState(() => getAccessToken());
  const [loading, setLoading] = useState(false);
  // Nothing is treated as authenticated until the server confirms the session.
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    // Keep React state in sync with the in-memory session (e.g. background refresh failure).
    const unsubscribe = onSessionChange(({ token: t, user: u }) => {
      setToken(t);
      setUser(u);
    });

    let cancelled = false;
    authService
      .restoreSession()
      .catch(() => null)
      .finally(() => {
        if (!cancelled) setInitializing(false);
      });

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);

  const logout = useCallback((reason = 'user') => {
    try {
      if (reason === 'inactivity') {
        sessionStorage.setItem('session_logout_reason', 'inactivity');
      } else {
        sessionStorage.removeItem('session_logout_reason');
      }
    } catch {
      // Ignore storage errors
    }
    authService.logout();
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const data = await authService.login(email, password);
      try {
        sessionStorage.removeItem('session_logout_reason');
      } catch {
        // Ignore storage errors
      }
      return data;
    } finally {
      setLoading(false);
    }
  };

  const hasRole = useCallback(
    (allowedRoles) => {
      if (!user) return false;
      return Array.isArray(allowedRoles) ? allowedRoles.includes(user.role) : user.role === allowedRoles;
    },
    [user]
  );

  // Idle Session Inactivity Timer & Grace Warning Hook (15m idle / 60s warning)
  const handleIdleLogout = useCallback((reason) => {
    logout(reason || 'inactivity');
  }, [logout]);

  const isAuthenticated = !initializing && !!token && !!user;

  const {
    isWarningOpen,
    remainingSeconds,
    resetIdleTimer,
    confirmLogout,
  } = useIdleTimer({
    onIdle: handleIdleLogout,
    idleTimeoutMs: 15 * 60 * 1000, // 15 minutes
    promptBeforeMs: 60 * 1000,      // 60-second grace warning
    enabled: isAuthenticated,
  });

  const value = {
    user,
    token,
    loading,
    initializing,
    login,
    logout,
    hasRole,
    isAuthenticated,
    role: user?.role || 'guest',
    resetIdleTimer,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
      <IdleSessionModal
        isOpen={isWarningOpen && isAuthenticated}
        remainingSeconds={remainingSeconds}
        onStayLoggedIn={resetIdleTimer}
        onLogout={confirmLogout}
      />
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
