import { describe, expect, it } from 'vitest';
import { mappingStatus, verificationLabel } from './phase7';

describe('Phase 7 assurance helpers', () => {
  it('labels linked and unlinked framework mappings', () => {
    expect(mappingStatus({ status: 'mapped' } as never)).toBe('Mapped');
    expect(mappingStatus({ status: 'reference_only' } as never)).toBe('Reference only');
  });
  it('distinguishes verified, failed, and empty audit states', () => {
    expect(verificationLabel({ valid: true }, true)).toBe('Verified');
    expect(verificationLabel({ valid: false }, true)).toBe('Verification failed');
    expect(verificationLabel({ valid: false }, false)).toBe('No events');
  });
});
