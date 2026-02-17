import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/stores/authStore';
import { currencyApi } from '@/api/client';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal = ({ isOpen, onClose }: SettingsModalProps) => {
  const { t, i18n } = useTranslation();
  const { user, updateLanguage, updateCurrency } = useAuthStore();
  
  const [selectedLanguage, setSelectedLanguage] = useState(user?.language || 'en');
  const [selectedCurrency, setSelectedCurrency] = useState(user?.currency || 'USD');
  const [isConverting, setIsConverting] = useState(false);
  const [conversionPreview, setConversionPreview] = useState<any>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleLanguageChange = async (lang: string) => {
    setSelectedLanguage(lang);
    await updateLanguage(lang);
    i18n.changeLanguage(lang);
  };

  const handleCurrencyPreview = async () => {
    if (selectedCurrency === user?.currency) return;
    
    setIsLoading(true);
    try {
      const preview = await currencyApi.getPreview(selectedCurrency);
      setConversionPreview(preview);
      setIsConverting(true);
    } catch (error) {
      console.error('Failed to get conversion preview:', error);
      alert(t('errors.serverError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCurrencyApply = async () => {
    if (!confirmed) return;
    
    setIsLoading(true);
    try {
      await currencyApi.applyConversion(selectedCurrency);
      await updateCurrency(selectedCurrency);
      setIsConverting(false);
      setConversionPreview(null);
      setConfirmed(false);
      onClose();
      window.location.reload(); // Reload to show amounts in new currency
    } catch (error) {
      console.error('Failed to apply conversion:', error);
      alert(t('errors.serverError'));
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat(i18n.language, {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">{t('settings.title')}</h2>
        
        {/* Language Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {t('settings.language')}
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => handleLanguageChange('en')}
              className={`flex-1 py-2 px-4 rounded-lg border ${
                selectedLanguage === 'en'
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              English
            </button>
            <button
              onClick={() => handleLanguageChange('ru')}
              className={`flex-1 py-2 px-4 rounded-lg border ${
                selectedLanguage === 'ru'
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Русский
            </button>
          </div>
        </div>

        {/* Currency Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {t('settings.currency')}
          </label>
          <select
            value={selectedCurrency}
            onChange={(e) => {
              setSelectedCurrency(e.target.value);
              setIsConverting(false);
              setConversionPreview(null);
              setConfirmed(false);
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="USD">{t('currency.USD')} (USD)</option>
            <option value="RUB">{t('currency.RUB')} (RUB)</option>
          </select>
          
          {selectedCurrency !== user?.currency && !isConverting && (
            <button
              onClick={handleCurrencyPreview}
              disabled={isLoading}
              className="mt-2 w-full btn-primary"
            >
              {isLoading ? '...' : t('currency.changeCurrency')}
            </button>
          )}
        </div>

        {/* Conversion Preview */}
        {isConverting && conversionPreview && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium mb-2">{t('currency.preview')}</h3>
            
            <div className="text-sm text-gray-600 mb-3">
              {t('currency.currentRate')}: 1 {conversionPreview.current_currency} = {' '}
              {conversionPreview.rate.toFixed(2)} {conversionPreview.new_currency}
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
              <div>
                <div className="text-gray-500">{t('currency.currentIncome')}</div>
                <div className="font-medium">
                  {formatCurrency(conversionPreview.preview.current_income, conversionPreview.current_currency)}
                </div>
              </div>
              <div>
                <div className="text-gray-500">{t('currency.newIncome')}</div>
                <div className="font-medium text-primary-600">
                  {formatCurrency(conversionPreview.preview.new_income, conversionPreview.new_currency)}
                </div>
              </div>
              <div>
                <div className="text-gray-500">{t('currency.currentExpense')}</div>
                <div className="font-medium">
                  {formatCurrency(conversionPreview.preview.current_expense, conversionPreview.current_currency)}
                </div>
              </div>
              <div>
                <div className="text-gray-500">{t('currency.newExpense')}</div>
                <div className="font-medium text-danger-600">
                  {formatCurrency(conversionPreview.preview.new_expense, conversionPreview.new_currency)}
                </div>
              </div>
            </div>
            
            <div className="text-xs text-gray-500 mb-3">
              {t('currency.transactionCount')}: {conversionPreview.transaction_count}
            </div>
            
            <label className="flex items-center gap-2 text-sm mb-3">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="rounded border-gray-300"
              />
              {t('currency.confirmConversion')}
            </label>
            
            <button
              onClick={handleCurrencyApply}
              disabled={!confirmed || isLoading}
              className="w-full btn-primary disabled:opacity-50"
            >
              {isLoading ? '...' : t('currency.apply')}
            </button>
            
            <p className="text-xs text-gray-500 mt-2">
              {t('currency.conversionNote')}
            </p>
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full btn-secondary"
        >
          {t('transaction.cancel')}
        </button>
      </div>
    </div>
  );
};
