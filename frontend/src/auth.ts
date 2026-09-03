export type Role = 'ciso' | 'analyst' | 'auditor';
export type AuthSession = { token: string; role: Role; expiresAt: number };
const storageKey = 'sentinelledger.auth';
function claims(token: string): Record<string, unknown> | null { try { const encoded = token.split('.')[1]; return encoded ? JSON.parse(atob(encoded.replace(/-/g, '+').replace(/_/g, '/'))) : null; } catch { return null; } }
export function createSession(token: string, role: string): AuthSession | null { const payload = claims(token); const expiresAt = typeof payload?.exp === 'number' ? payload.exp * 1000 : 0; return ['ciso', 'analyst', 'auditor'].includes(role) && expiresAt > Date.now() ? { token, role: role as Role, expiresAt } : null; }
export function loadSession(): AuthSession | null { try { const raw = sessionStorage.getItem(storageKey); if (!raw) return null; const session = JSON.parse(raw) as AuthSession; return createSession(session.token, session.role); } catch { return null; } }
export function saveSession(session: AuthSession): void { sessionStorage.setItem(storageKey, JSON.stringify(session)); }
export function clearSession(): void { sessionStorage.removeItem(storageKey); }
export const roleLabel: Record<Role, string> = { ciso: 'CISO', analyst: 'ANALYST', auditor: 'AUDITOR' };
export const canManageRisk = (role: Role) => role === 'ciso' || role === 'analyst';
export const canViewAssurance = (role: Role) => role === 'ciso' || role === 'auditor';
