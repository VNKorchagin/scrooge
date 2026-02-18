import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/stores/authStore';

type Tab = 'login' | 'register';

export const LoginPage = () => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { login, register, isLoading, error, clearError } = useAuthStore();
  
  const [activeTab, setActiveTab] = useState<Tab>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [currency, setCurrency] = useState<'USD' | 'RUB'>('USD');
  const [localError, setLocalError] = useState<string | null>(null);

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab);
    clearError();
    setLocalError(null);
  };

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!username.trim() || !password.trim()) {
      setLocalError(t('errors.required'));
      return;
    }

    if (activeTab === 'register') {
      if (password !== confirmPassword) {
        setLocalError('Passwords do not match');
        return;
      }
      if (password.length < 4) {
        setLocalError('Password must be at least 4 characters');
        return;
      }
    }

    try {
      if (activeTab === 'login') {
        await login(username, password);
      } else {
        await register(username, password, currency);
      }
      navigate('/dashboard');
    } catch (err: any) {
      // Error is handled in store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo */}
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-primary-600 rounded-xl flex items-center justify-center mb-4">
            <span className="text-white font-bold text-3xl">S</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">{t('app.name')}</h1>
          <p className="mt-2 text-gray-600">{t('app.tagline')}</p>
        </div>

        {/* Language Selector */}
        <div className="flex justify-center">
          <div className="inline-flex rounded-lg bg-gray-100 p-1">
            <button
              onClick={() => handleLanguageChange('en')}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-all ${
                i18n.language === 'en'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              EN
            </button>
            <button
              onClick={() => handleLanguageChange('ru')}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-all ${
                i18n.language === 'ru'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              RU
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex rounded-lg bg-gray-100 p-1">
          <button
            onClick={() => handleTabChange('login')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-all ${
              activeTab === 'login'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t('auth.signIn')}
          </button>
          <button
            onClick={() => handleTabChange('register')}
            className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-all ${
              activeTab === 'register'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t('auth.signUp')}
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          {(error || localError) && (
            <div className="rounded-lg bg-danger-50 p-4 text-sm text-danger-700">
              {error || localError}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                {t('auth.username')}
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input mt-1"
                placeholder={t('auth.username')}
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                {t('auth.password')}
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input mt-1"
                placeholder={t('auth.password')}
                required
              />
            </div>

            {activeTab === 'register' && (
              <>
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                    {t('auth.confirmPassword')}
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="input mt-1"
                    placeholder={t('auth.confirmPassword')}
                    required
                  />
                </div>

                <div>
                  <label htmlFor="currency" className="block text-sm font-medium text-gray-700">
                    {t('auth.selectCurrency')}
                  </label>
                  <select
                    id="currency"
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value as 'USD' | 'RUB')}
                    className="input mt-1"
                  >
                    <option value="USD">{t('currency.USD')}</option>
                    <option value="RUB">{t('currency.RUB')}</option>
                  </select>
                </div>
              </>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </span>
            ) : (
              activeTab === 'login' ? t('auth.signIn') : t('auth.createAccount')
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
