import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { RecentTransaction } from '@/types';
import { formatCurrency, formatDate } from '@/utils/format';

interface RecentTransactionsProps {
  transactions: RecentTransaction[];
  currency?: string;
}

export const RecentTransactions = ({ transactions, currency }: RecentTransactionsProps) => {
  const { t } = useTranslation();

  if (!transactions || transactions.length === 0) {
    return (
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{t('dashboard.recentTransactions')}</h3>
          <Link to="/history" className="text-sm text-primary-600 hover:text-primary-700">
            {t('dashboard.viewAll')}
          </Link>
        </div>
        <p className="text-gray-500 text-center py-8">{t('transaction.noTransactions')}</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{t('dashboard.recentTransactions')}</h3>
        <Link to="/history" className="text-sm text-primary-600 hover:text-primary-700">
          {t('dashboard.viewAll')}
        </Link>
      </div>
      <div className="space-y-3">
        {transactions.map((transaction) => (
          <div
            key={transaction.id}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {transaction.category_name}
              </p>
              <p className="text-xs text-gray-500">
                {formatDate(transaction.transaction_date)}
              </p>
              {transaction.description && (
                <p className="text-xs text-gray-400 truncate">
                  {transaction.description}
                </p>
              )}
            </div>
            <span
              className={`text-sm font-semibold ml-4 ${
                transaction.type === 'income'
                  ? 'text-primary-600'
                  : 'text-danger-600'
              }`}
            >
              {transaction.type === 'income' ? '+' : '-'}
              {formatCurrency(transaction.amount, currency)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
