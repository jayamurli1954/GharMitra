export type FeatureIconPreset = {
  icon: string;
  tint: string;
  background: string;
};

export const defaultFeatureIcon: FeatureIconPreset = {
  icon: 'apps',
  tint: '#0A84FF',
  background: '#E8F0FF',
};

export const featureIcons: Record<string, FeatureIconPreset> = {
  billing: {
    icon: 'file-document-edit-outline',
    tint: '#4A90E2',
    background: '#E8F1FF',
  },
  flats: {
    icon: 'home-city-outline',
    tint: '#7B61FF',
    background: '#F0EBFF',
  },
  transaction: {
    icon: 'cash-plus',
    tint: '#34C759',
    background: '#E7F8EE',
  },
  reports: {
    icon: 'chart-box-outline',
    tint: '#FF6B6B',
    background: '#FFECEC',
  },
  resources: {
    icon: 'book-open-page-variant',
    tint: '#FF8B5E',
    background: '#FFF1EA',
  },
  settings: {
    icon: 'cog-outline',
    tint: '#5AC8FA',
    background: '#E7F7FF',
  },
  messages: {
    icon: 'message-text-outline',
    tint: '#FFB72B',
    background: '#FFF5E1',
  },
  payments: {
    icon: 'credit-card-sync-outline',
    tint: '#6A53FF',
    background: '#EFEBFF',
  },
  complaints: {
    icon: 'headset',
    tint: '#F06292',
    background: '#FFE7F0',
  },
};

export type FeatureIconKey = keyof typeof featureIcons;

export const getFeatureIcon = (
  key: FeatureIconKey | string,
  fallback?: FeatureIconPreset,
): FeatureIconPreset => {
  if (featureIcons[key as FeatureIconKey]) {
    return featureIcons[key as FeatureIconKey];
  }

  if (fallback) {
    return fallback;
  }

  return defaultFeatureIcon;
};







