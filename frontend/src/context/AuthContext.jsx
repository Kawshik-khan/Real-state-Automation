import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/auth';
import { useIdleTimer } from '../hooks/useIdleTimer';
import IdleSessionModal from '../components/common/IdleSessionModal';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => authService.getUser());
  const [token, setToken] = useState(() => authService.getToken());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Validate session against backend on app launch
    if (token) {
      setLoading(true);
      authService.getMe()
        .then((userData) => {
          if (userData) {
            setUser(userData);
          } else {
            setToken(null);
            setUser(null);
          }
        })
        .catch(() => {
          setToken(null);
          setUser(null);
        })
        .finally(() => setLoading(false));
    }
  }, []);

  const logout = useCallback((reason = 'user') => {
    if (reason === 'inactivity') {
      try {
        sessionStorage.setItem('session_logout_reason', 'inactivity');
      } catch {
        // Ignore storage errors
      }
    } else {
      try {
        sessionStorage.removeItem('session_logout_reason');
      } catch {
        // Ignore storage errors
      }
    }

    authService.logout();
    setToken(null);
    setUser(null);
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
      setToken(data.access_token);
      setUser(data.user);
      return data;
    } finally {
      setLoading(false);
    }
  };

  const hasRole = (allowedRoles) => {
    if (!user) return false;
    if (Array.isArray(allowedRoles)) {
      return allowedRoles.includes(user.role);
    }
    return user.role === allowedRoles;
  };

  // Idle Session Inactivity Timer & Grace Warning Hook (15m idle / 60s warning)
  const handleIdleLogout = useCallback((reason) => {
    logout(reason || 'inactivity');
  }, [logout]);

  const {
    isWarningOpen,
    remainingSeconds,
    resetIdleTimer,
    confirmLogout,
  } = useIdleTimer({
    onIdle: handleIdleLogout,
    idleTimeoutMs: 15 * 60 * 1000, // 15 minutes
    promptBeforeMs: 60 * 1000,      // 60-second grace warning
    enabled: !!token && !!user,
  });

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    hasRole,
    isAuthenticated: !!token && !!user,
    role: user?.role || 'guest',
    resetIdleTimer,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
      <IdleSessionModal
        isOpen={isWarningOpen && !!token && !!user}
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

