export type FrameworkMapping = {
  reference: string;
  control: { id: number; name: string; category: string; coverage: number } | null;
  status: 'mapped' | 'reference_only';
  risk_relevance: string;
  evidence: string | null;
};

export type Framework = { name: string; mappings: FrameworkMapping[] };
export type AuditEvent = {
  sequence: number;
  timestamp: string;
  actor: string | null;
  action: string;
  resource: string | null;
  hash: string;
  previous_hash: string;
  payload: Record<string, unknown>;
};

export function mappingStatus(mapping: FrameworkMapping): string {
  return mapping.status === 'mapped' ? 'Mapped' : 'Reference only';
}

export function verificationLabel(result: { valid: boolean }, hasEvents: boolean): string {
  if (!hasEvents) return 'No events';
  return result.valid ? 'Verified' : 'Verification failed';
}
