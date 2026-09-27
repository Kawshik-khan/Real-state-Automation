import { describe, it, expect } from 'vitest';
import { getDefaultTabForRole, TAB_TO_PATH } from '../App';

describe('getDefaultTabForRole', () => {
  describe('Standard 5-Tier RBAC Roles', () => {
    it('returns developer_console for developer role', () => {
      expect(getDefaultTabForRole('developer')).toBe('developer_console');
    });

    it('returns conversations for agent role', () => {
      expect(getDefaultTabForRole('agent')).toBe('conversations');
    });

    it('returns properties for viewer role', () => {
      expect(getDefaultTabForRole('viewer')).toBe('properties');
    });

    it('returns overview for manager role', () => {
      expect(getDefaultTabForRole('manager')).toBe('overview');
    });

    it('returns overview for admin role', () => {
      expect(getDefaultTabForRole('admin')).toBe('overview');
    });
  });

  describe('Edge Cases & Fallbacks', () => {
    const fallbackCases = [
      { label: 'null', value: null },
      { label: 'undefined', value: undefined },
      { label: 'empty string', value: '' },
      { label: 'guest', value: 'guest' },
      { label: 'superadmin', value: 'superadmin' },
      { label: 'auditor', value: 'auditor' },
      { label: 'anonymous', value: 'anonymous' },
      { label: 'case mismatch DEVELOPER', value: 'DEVELOPER' },
      { label: 'case mismatch Agent', value: 'Agent' },
    ];

    fallbackCases.forEach(({ label, value }) => {
      it(`returns overview for ${label}`, () => {
        expect(getDefaultTabForRole(value)).toBe('overview');
      });
    });
  });

  describe('Routing Contract Assertion', () => {
    const testRoles = [
      'developer',
      'agent',
      'viewer',
      'manager',
      'admin',
      null,
      undefined,
      '',
      'guest'
    ];

    testRoles.forEach((role) => {
      it(`resolves to a valid route for role: ${String(role)}`, () => {
        const tab = getDefaultTabForRole(role);

        // Assert the tab exists in TAB_TO_PATH mapping
        expect(TAB_TO_PATH[tab]).toBeDefined();

        // Assert the mapped path starts with a '/'
        expect(TAB_TO_PATH[tab].startsWith('/')).toBe(true);
      });
    });
  });
});
