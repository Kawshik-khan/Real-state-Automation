/**
 * Authentication API service.
 *
 * - Credentials are sent to exactly one origin: the configured API base (no fan-out
 *   across candidate hosts).
 * - The access token and user profile are kept in memory (./session.js). The refresh
 *   token stays in the httpOnly cookie set by the backend and is never readable by JS.
 */
import { apiFetch, buildApiUrl, refreshSession } from './api';
import { clearSession, getAccessToken, getSessionUser, purgeLegacyStoredCredentials, setSession } from './session';

const CLIENT_HEADER = { 'X-GLG-Client': 'dashboard' };

/** fetch with a per-request timeout (default 8 s) */
async function fetchWithTimeout(url, options = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export const authService = {
  async login(email, password) {
    let response;
    try {
      response = await fetchWithTimeout(buildApiUrl('/api/v1/auth/login'), {
        method: 'POST',
        credentials: 'include', // receive the httpOnly refresh cookie
        headers: { 'Content-Type': 'application/json', ...CLIENT_HEADER },
        body: JSON.stringify({ email, password }),
      });
    } catch (err) {
      throw new Error(
        err?.name === 'AbortError' || err instanceof TypeError
          ? 'Unable to connect to backend server. Please verify backend is running and reachable.'
          : err?.message || 'Connection to backend failed.'
      );
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Login failed. Please check your credentials.');
    }

    const data = await response.json();
    purgeLegacyStoredCredentials();
    setSession(data.access_token, data.user);
    return data;
  },

  /**
   * Restore a session after a page reload using the refresh cookie.
   * Resolves to the user profile, or null if there is no valid session.
   */
  async restoreSession() {
    purgeLegacyStoredCredentials();
    const data = await refreshSession();
    if (!data) return null;
    if (data.user) return data.user;
    return this.getMe();
  },

  /** Rotate the refresh cookie for a fresh access token. Resolves to the token or null. */
  async refreshToken() {
    const data = await refreshSession();
    return data?.access_token || null;
  },

  async getMe() {
    if (!getAccessToken()) return null;
    try {
      const response = await apiFetch(buildApiUrl('/api/v1/auth/me'));
      if (!response.ok) return null;
      const user = await response.json();
      setSession(getAccessToken(), user);
      return user;
    } catch {
      return null;
    }
  },

  logout() {
    fetch(buildApiUrl('/api/v1/auth/logout'), {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...CLIENT_HEADER },
      body: '{}',
    }).catch(() => {});
    clearSession();
    purgeLegacyStoredCredentials();
  },

  getToken() {
    return getAccessToken();
  },

  getUser() {
    return getSessionUser();
  },
};
