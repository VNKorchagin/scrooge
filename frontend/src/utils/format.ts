import i18n from '@/i18n';

export const formatCurrency = (amount: number, currency?: string): string => {
  const userCurrency = currency || 'USD';
  return new Intl.NumberFormat(i18n.language, {
    style: 'currency',
    currency: userCurrency,
  }).format(amount);
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat(i18n.language, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date);
};

export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat(i18n.language, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};
