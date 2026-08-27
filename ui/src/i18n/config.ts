import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { zhCN } from './translations';

const zhTranslation = Object.fromEntries(Object.entries(zhCN));

void i18n.use(initReactI18next).init({
  resources: { 'zh-CN': { translation: zhTranslation }, en: { translation: {} } },
  lng: 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
  returnNull: false,
});

export default i18n;
