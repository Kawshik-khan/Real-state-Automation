/**
 * Authentication API Service with automatic multi-endpoint fallback
 */

const BACKEND_CANDIDATES = [
  import.meta.env.VITE_API_BASE_URL ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '') : null,
  'https://real-state-automation.onrender.com',
  'https://glg-realestate-backend.onrender.com',
  'http://localhost:8000'
].filter(Boolean);

export const authService = {
  /**
   * Login user with email and password, testing candidate endpoints if network fails
   */
  async login(email, password) {
    let lastError = null;

    for (const baseUrl of BACKEND_CANDIDATES) {
      try {
        const url = `${baseUrl.replace(/\/$/, '')}/api/v1/auth/login`;
        const response = await fetch(url, {
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
          localStorage.setItem('glg_user', JSON.stringify(data.user));
          localStorage.setItem('glg_working_backend', baseUrl);
        }
        return data;
      } catch (err) {
        lastError = err;
        // If it's an explicit 401/403 credential rejection from backend, don't try fallback backend
        if (err.message && (err.message.includes('Invalid') || err.message.includes('credentials') || err.message.includes('password'))) {
          throw err;
        }
        // Network error / Failed to fetch: try next candidate URL
      }
    }

    throw new Error(
      lastError?.message?.includes('Failed to fetch') || lastError instanceof TypeError
        ? 'Unable to connect to backend server. Render may be performing a cold start (~15s) or Vercel needs deployment. Please retry in a moment.'
        : (lastError?.message || 'Connection to backend failed.')
    );
  },

  /**
   * Get current user profile
   */
  async getMe() {
    const token = localStorage.getItem('glg_token');
    if (!token) return null;

    const savedBackend = localStorage.getItem('glg_working_backend');
    const candidates = savedBackend ? [savedBackend, ...BACKEND_CANDIDATES] : BACKEND_CANDIDATES;

    for (const baseUrl of candidates) {
      try {
        const url = `${baseUrl.replace(/\/$/, '')}/api/v1/auth/me`;
        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const user = await response.json();
          localStorage.setItem('glg_user', JSON.stringify(user));
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
    localStorage.removeItem('glg_token');
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
