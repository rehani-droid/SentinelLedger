import { describe, expect, it } from 'vitest';
import { canManageRisk, canViewAssurance, createSession } from './auth';
function token(payload: object) { return `header.${btoa(JSON.stringify(payload))}.signature`; }
describe('frontend authentication helpers', () => {
  it('accepts a current token only for a supported role', () => { expect(createSession(token({ exp: Math.floor(Date.now() / 1000) + 60 }), 'ciso')?.role).toBe('ciso'); expect(createSession(token({ exp: Math.floor(Date.now() / 1000) + 60 }), 'admin')).toBeNull(); });
  it('rejects expired tokens and exposes role capabilities', () => { expect(createSession(token({ exp: 1 }), 'auditor')).toBeNull(); expect(canManageRisk('analyst')).toBe(true); expect(canManageRisk('auditor')).toBe(false); expect(canViewAssurance('auditor')).toBe(true); });
});
