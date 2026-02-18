import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { transactionsApi } from '@/api/client';
import { CategoryAutocomplete } from '@/components/CategoryAutocomplete';
import { useAuthStore } from '@/stores/authStore';
import { TransactionType } from '@/types';

// Currency symbols mapping
const currencySymbols: Record<string, string> = {
  USD: '$',
  RUB: '₽',
};

export const AddTransactionPage = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [type, setType] = useState<TransactionType>('expense');
  const [amount, setAmount] = useState('');
  const [categoryName, setCategoryName] = useState('');
  // Empty by default - user can fill if needed
  const [transactionDate, setTransactionDate] = useState('');
  const [description, setDescription] = useState('');

  // Get currency symbol from user settings
  const currencySymbol = currencySymbols[user?.currency || 'USD'];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!amount || parseFloat(amount) <= 0) {
      setError(t('errors.invalidAmount'));
      return;
    }
    if (!categoryName.trim()) {
      setError(t('errors.required'));
      return;
    }
    // Note: transaction_date is optional - if not provided, backend uses current datetime

    setIsLoading(true);
    try {
      const data: {
        type: TransactionType;
        amount: number;
        category_name: string;
        description?: string;
        transaction_date?: string;
      } = {
        type,
        amount: parseFloat(amount),
        category_name: categoryName.trim(),
        description: description.trim() || undefined,
      };

      // Only include transaction_date if user provided it
      if (transactionDate) {
        data.transaction_date = new Date(transactionDate).toISOString();
      }

      await transactionsApi.create(data);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || t('errors.serverError'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4 sm:mb-6">{t('transaction.add')}</h1>

      <div className="card p-4 sm:p-6">
        {error && (
          <div className="mb-4 rounded-lg bg-danger-50 p-4 text-sm text-danger-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {t('transaction.type')}
            </label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="type"
                  value="income"
                  checked={type === 'income'}
                  onChange={(e) => setType(e.target.value as TransactionType)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-700">{t('transaction.income')}</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="type"
                  value="expense"
                  checked={type === 'expense'}
                  onChange={(e) => setType(e.target.value as TransactionType)}
                  className="h-4 w-4 text-danger-600 focus:ring-danger-500"
                />
                <span className="ml-2 text-sm text-gray-700">{t('transaction.expense')}</span>
              </label>
            </div>
          </div>

          {/* Amount */}
          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-1">
              {t('transaction.amount')} <span className="text-danger-500">*</span>
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">{currencySymbol}</span>
              <input
                id="amount"
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="input pl-8"
                placeholder="0.00"
                required
              />
            </div>
          </div>

          {/* Category */}
          <CategoryAutocomplete
            value={categoryName}
            onChange={setCategoryName}
            required
          />

          {/* Date - Optional */}
          <div>
            <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-1">
              {t('transaction.date')}
            </label>
            <input
              id="date"
              type="datetime-local"
              value={transactionDate}
              onChange={(e) => setTransactionDate(e.target.value)}
              className="input"
            />
            <p className="text-xs text-gray-500 mt-1">
              {t('transaction.dateOptional') || 'Optional - current time will be used if not specified'}
            </p>
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              {t('transaction.description')}
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input"
              rows={3}
              placeholder={t('transaction.description')}
            />
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="flex-1 btn-secondary"
            >
              {t('transaction.cancel')}
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 btn-primary disabled:opacity-50"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {t('transaction.save')}...
                </span>
              ) : (
                t('transaction.save')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
