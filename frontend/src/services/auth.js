/**
 * Authentication API Service with automatic dynamic multi-endpoint fallback
 */
import { getApiCandidates, getApiBaseUrl } from './api';

/** Helper: fetch with a per-request timeout (default 5 s) */
async function fetchWithTimeout(url, options = {}, timeoutMs = 5000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    return response;
  } finally {
    clearTimeout(timer);
  }
}

export const authService = {
  /**
   * Helper to retrieve prioritized backend candidate base URLs dynamically
   */
  getCandidateBases() {
    const savedBackend = typeof window !== 'undefined' ? localStorage.getItem('glg_working_backend') : null;
    const dynamicBases = getApiCandidates();
    const primaryBase = getApiBaseUrl();
    const candidates = [
      savedBackend,
      primaryBase,
      ...dynamicBases,
      ''
    ].filter((v, idx, arr) => v !== null && v !== undefined && arr.indexOf(v) === idx);
    return candidates;
  },

  /**
   * Login user with email and password, testing candidate endpoints if network fails
   */
  async login(email, password) {
    let lastError = null;
    const candidates = this.getCandidateBases();

    for (const baseUrl of candidates) {
      try {
        const cleanBase = baseUrl ? baseUrl.replace(/\/+$/, '') : '';
        const url = `${cleanBase}/api/v1/auth/login`;
        const response = await fetchWithTimeout(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Login failed. Please check your credentials.');
        }

        const data = await response.json();
        if (data.access_token) {
          localStorage.setItem('glg_token', data.access_token);
          if (data.refresh_token) {
            localStorage.setItem('glg_refresh_token', data.refresh_token);
          }
          localStorage.setItem('glg_user', JSON.stringify(data.user));
          if (baseUrl) {
            localStorage.setItem('glg_working_backend', baseUrl);
          }
        }
        return data;
      } catch (err) {
        lastError = err;
        // If it's an explicit 401/403 credential rejection from backend, don't try fallback backend
        if (err.message && (err.message.includes('Invalid') || err.message.includes('credentials') || err.message.includes('password'))) {
          throw err;
        }
        // Network error / Failed to fetch / Timeout: try next candidate URL
      }
    }

    throw new Error(
      lastError?.message?.includes('Failed to fetch') || lastError instanceof TypeError || lastError?.name === 'AbortError'
        ? 'Unable to connect to backend server. Please verify backend is running and reachable.'
        : (lastError?.message || 'Connection to backend failed.')
    );
  },

  /**
   * Rotate refresh token to obtain a fresh access token without user prompt
   */
  async refreshToken() {
    const refreshToken = localStorage.getItem('glg_refresh_token');
    const candidates = this.getCandidateBases();

    for (const baseUrl of candidates) {
      try {
        const cleanBase = baseUrl ? baseUrl.replace(/\/+$/, '') : '';
        const url = `${cleanBase}/api/v1/auth/refresh`;
        const response = await fetchWithTimeout(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ refresh_token: refreshToken || undefined }),
        });

        if (response.ok) {
          const data = await response.json();
          if (data.access_token) {
            localStorage.setItem('glg_token', data.access_token);
            if (data.refresh_token) {
              localStorage.setItem('glg_refresh_token', data.refresh_token);
            }
            if (data.user) {
              localStorage.setItem('glg_user', JSON.stringify(data.user));
            }
            if (baseUrl) {
              localStorage.setItem('glg_working_backend', baseUrl);
            }
            return data.access_token;
          }
        }
      } catch {
        // Try next candidate URL
      }
    }

    this.logout();
    return null;
  },

  /**
   * Get current user profile
   */
  async getMe() {
    const token = localStorage.getItem('glg_token');
    if (!token) return null;

    const candidates = this.getCandidateBases();

    for (const baseUrl of candidates) {
      try {
        const cleanBase = baseUrl ? baseUrl.replace(/\/+$/, '') : '';
        const url = `${cleanBase}/api/v1/auth/me`;
        const response = await fetchWithTimeout(url, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const user = await response.json();
          localStorage.setItem('glg_user', JSON.stringify(user));
          if (baseUrl) {
            localStorage.setItem('glg_working_backend', baseUrl);
          }
          return user;
        }
      } catch {
        // Try next backend candidate
      }
    }

    this.logout();
    return null;
  },

  /**
   * Logout user and clear tokens
   */
  logout() {
    const refreshToken = localStorage.getItem('glg_refresh_token');
    const candidates = this.getCandidateBases();
    const primaryBase = candidates[0] || '';
    const cleanBase = primaryBase ? primaryBase.replace(/\/+$/, '') : '';

    if (cleanBase || cleanBase === '') {
      fetch(`${cleanBase}/api/v1/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ refresh_token: refreshToken || undefined }),
      }).catch(() => {});
    }

    localStorage.removeItem('glg_token');
    localStorage.removeItem('glg_refresh_token');
    localStorage.removeItem('glg_user');
    localStorage.removeItem('glg_working_backend');
  },

  /**
   * Get stored token
   */
  getToken() {
    return localStorage.getItem('glg_token');
  },

  /**
   * Get stored refresh token
   */
  getRefreshToken() {
    return localStorage.getItem('glg_refresh_token');
  },

  /**
   * Get stored user
   */
  getUser() {
    const userStr = localStorage.getItem('glg_user');
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  }
};
