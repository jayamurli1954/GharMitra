/**
 * Consistent spacing system
 * Based on 4px grid system (4px, 8px, 12px, 16px, 24px multiples)
 */
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
} as const;

export type Spacing = typeof spacing[keyof typeof spacing];

