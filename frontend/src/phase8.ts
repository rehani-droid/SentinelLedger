export const assistantExamples = [
  'What are our biggest cyber risks?',
  'Which assets contribute most to financial exposure?',
  'Where should we spend our next ₹10 lakh?',
  'What happens if we enable MFA for privileged users?',
  'What are the highest priority vulnerabilities?',
  'What is our predicted incident likelihood?',
  'Is our cyber risk increasing?',
];

export type AssistantResponse = {
  intent: string;
  provider: string;
  ai_generated: boolean;
  data: Record<string, any>;
  calculation: string;
  recommendation: string;
};

export function formatIntent(intent: string): string {
  return intent.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}
