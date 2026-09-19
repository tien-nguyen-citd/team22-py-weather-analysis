export const clamp = (v: number, a: number, b: number): number => Math.max(a, Math.min(b, v));

/**
 * Helpers màu sắc và chiều cao cột
 */
export function getScoreColor(hour: number, score: number): string {
  if (hour < 6 || hour >= 18) return 'var(--night)';
  if (score >= 70) return 'var(--acc)';
  if (score >= 50) return 'var(--mid)';
  return 'var(--dim)';
}

export function getFactorColor(value: number): string {
  if (value >= 70) return 'var(--acc)';
  if (value >= 45) return 'var(--mid)';
  return 'var(--weak)';
}
