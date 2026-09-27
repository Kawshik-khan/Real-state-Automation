/**
 * In-memory session state.
 *
 * The access token lives only in this module (never localStorage/sessionStorage), so a
 * script injected into the page cannot lift a long-lived credential from storage. The
 * refresh token is an httpOnly cookie the browser manages; on reload the session is
 * restored by calling /api/v1/auth/refresh.
 */

let accessToken = null;
let currentUser = null;
const listeners = new Set();

export function getAccessToken() {
  return accessToken;
}

export function getSessionUser() {
  return currentUser;
}

export function setSession(token, user) {
  accessToken = token || null;
  if (user !== undefined) currentUser = user || null;
  listeners.forEach((fn) => fn({ token: accessToken, user: currentUser }));
}

export function clearSession() {
  setSession(null, null);
}

/** Subscribe to session changes (e.g. a background refresh failing). Returns unsubscribe. */
export function onSessionChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

/** Remove credentials persisted by earlier releases of the dashboard. */
export function purgeLegacyStoredCredentials() {
  try {
    ['glg_token', 'glg_refresh_token', 'glg_user', 'glg_working_backend', 'glg_api_base_url'].forEach((k) =>
      localStorage.removeItem(k)
    );
  } catch {
    // Storage may be unavailable (private mode); nothing to purge.
  }
}
