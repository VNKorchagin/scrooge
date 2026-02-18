import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import ru from './locales/ru.json';

// Helper to normalize language: ru -> ru, everything else -> en
const normalizeLanguage = (lang: string): string => {
  return lang.startsWith('ru') ? 'ru' : 'en';
};

// Custom language detector that only supports ru/en
const customLanguageDetector = {
  type: 'languageDetector' as const,
  async: false,
  init: () => {},
  detect: () => {
    // Get browser language
    const browserLang = navigator.language || (navigator as any).userLanguage || 'en';
    return normalizeLanguage(browserLang);
  },
  cacheUserLanguage: () => {},
};

i18n
  .use(customLanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ru: { translation: ru },
    },
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
