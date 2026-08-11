/**
 * Authentication API Service
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const authService = {
  /**
   * Login user with email and password
   */
  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Login failed. Please check credentials.');
    }

    const data = await response.json();
    if (data.access_token) {
      localStorage.setItem('glg_token', data.access_token);
      localStorage.setItem('glg_user', JSON.stringify(data.user));
    }
    return data;
  },

  /**
   * Get current user profile
   */
  async getMe() {
    const token = localStorage.getItem('glg_token');
    if (!token) return null;

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      this.logout();
      return null;
    }

    const user = await response.json();
    localStorage.setItem('glg_user', JSON.stringify(user));
    return user;
  },

  /**
   * Logout user and clear tokens
   */
  logout() {
    localStorage.removeItem('glg_token');
    localStorage.removeItem('glg_user');
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
