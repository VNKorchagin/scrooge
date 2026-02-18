import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { transactionsApi, exportApi } from '@/api/client';
import { useAuthStore } from '@/stores/authStore';
import { Transaction, TransactionType } from '@/types';
import { formatCurrency, formatDateTime } from '@/utils/format';

// Quick filter period types
type QuickFilter = 'current_month' | '30_days' | 'quarter' | 'half_year' | 'year' | 'custom';

export const HistoryPage = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  // Filters
  const [filterType, setFilterType] = useState<TransactionType | ''>('');
  const [activeQuickFilter, setActiveQuickFilter] = useState<QuickFilter>('current_month');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Get user's currency
  const userCurrency = user?.currency || 'USD';

  // Initialize with current month dates
  useEffect(() => {
    applyQuickFilter('current_month');
  }, []);

  useEffect(() => {
    fetchTransactions();
  }, [offset, filterType, dateFrom, dateTo]);

  // Format date for input (YYYY-MM-DD)
  const formatDateForInput = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  // Apply quick filter
  const applyQuickFilter = (filter: QuickFilter) => {
    setActiveQuickFilter(filter);
    setOffset(0);

    const now = new Date();
    const today = formatDateForInput(now);
    let from = '';

    switch (filter) {
      case 'current_month':
        from = formatDateForInput(new Date(now.getFullYear(), now.getMonth(), 1));
        break;
      case '30_days':
        const thirtyDaysAgo = new Date(now);
        thirtyDaysAgo.setDate(now.getDate() - 30);
        from = formatDateForInput(thirtyDaysAgo);
        break;
      case 'quarter':
        const quarterStart = new Date(now);
        quarterStart.setMonth(now.getMonth() - 3);
        from = formatDateForInput(quarterStart);
        break;
      case 'half_year':
        const halfYearStart = new Date(now);
        halfYearStart.setMonth(now.getMonth() - 6);
        from = formatDateForInput(halfYearStart);
        break;
      case 'year':
        const yearStart = new Date(now);
        yearStart.setFullYear(now.getFullYear() - 1);
        from = formatDateForInput(yearStart);
        break;
      case 'custom':
        // Keep existing dates or clear them
        return;
    }

    setDateFrom(from);
    setDateTo(today);
  };

  const fetchTransactions = async () => {
    setIsLoading(true);
    try {
      const params: Record<string, string | number | undefined> = {
        limit,
        offset,
      };
      if (filterType) params.type = filterType;
      if (dateFrom) params.date_from = new Date(dateFrom).toISOString();
      if (dateTo) params.date_to = new Date(dateTo + 'T23:59:59').toISOString();

      const data = await transactionsApi.getAll(params);
      setTransactions(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm(t('transaction.confirmDelete') || 'Are you sure you want to delete this transaction?')) return;
    
    try {
      await transactionsApi.delete(id);
      fetchTransactions();
    } catch (error) {
      console.error('Failed to delete transaction:', error);
      alert(t('errors.serverError'));
    }
  };

  const handleExport = async () => {
    try {
      const params: { type?: string; date_from?: string; date_to?: string } = {};
      if (filterType) params.type = filterType;
      if (dateFrom) params.date_from = new Date(dateFrom).toISOString();
      if (dateTo) params.date_to = new Date(dateTo + 'T23:59:59').toISOString();
      
      await exportApi.exportCSV(params);
    } catch (error) {
      console.error('Failed to export:', error);
      alert(t('errors.serverError'));
    }
  };

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  // Translate transaction type
  const getTypeLabel = (type: TransactionType) => {
    return type === 'income' ? t('transaction.income') : t('transaction.expense');
  };

  // Quick filter buttons configuration
  const quickFilters: { key: QuickFilter; label: string }[] = [
    { key: 'current_month', label: t('history.currentMonth') },
    { key: '30_days', label: t('history.30days') },
    { key: 'quarter', label: t('history.quarter') },
    { key: 'half_year', label: t('history.halfYear') },
    { key: 'year', label: t('history.year') },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">{t('history.title')}</h1>
        <button
          onClick={handleExport}
          className="btn-secondary text-sm"
        >
          {t('history.exportCSV')}
        </button>
      </div>

      {/* Filters */}
      <div className="card space-y-4">
        {/* Quick Filter Buttons */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">{t('history.quickFilter')}</label>
          <div className="flex flex-wrap gap-2">
            {quickFilters.map((filter) => (
              <button
                key={filter.key}
                onClick={() => applyQuickFilter(filter.key)}
                className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${
                  activeQuickFilter === filter.key
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        {/* Custom Filters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('history.type')}</label>
            <select
              value={filterType}
              onChange={(e) => {
                setFilterType(e.target.value as TransactionType | '');
                setOffset(0);
              }}
              className="input"
            >
              <option value="">{t('history.all')}</option>
              <option value="income">{t('transaction.income')}</option>
              <option value="expense">{t('transaction.expense')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('history.from')}</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setActiveQuickFilter('custom');
                setOffset(0);
              }}
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('history.to')}</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setActiveQuickFilter('custom');
                setOffset(0);
              }}
              className="input"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
          </div>
        ) : transactions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">{t('history.noTransactions')}</p>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.date')}</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.type')}</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.category')}</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.description')}</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.amount')}</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.action')}</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr key={transaction.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm text-gray-900">
                    {transaction.transaction_date 
                      ? formatDateTime(transaction.transaction_date)
                      : '-'}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        transaction.type === 'income'
                          ? 'bg-primary-100 text-primary-700'
                          : 'bg-danger-100 text-danger-700'
                      }`}
                    >
                      {getTypeLabel(transaction.type)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-900">
                    {transaction.category_name}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-500 truncate max-w-xs">
                    {transaction.description || '-'}
                  </td>
                  <td
                    className={`py-3 px-4 text-sm font-medium text-right ${
                      transaction.type === 'income'
                        ? 'text-primary-600'
                        : 'text-danger-600'
                    }`}
                  >
                    {transaction.type === 'income' ? '+' : '-'}
                    {formatCurrency(Number(transaction.amount), userCurrency)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => handleDelete(transaction.id)}
                      className="text-danger-500 hover:text-danger-700 text-sm"
                    >
                      {t('transaction.delete')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              {t('history.showing', { start: offset + 1, end: Math.min(offset + limit, total), total })}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={currentPage === 1}
                className="btn-secondary text-sm disabled:opacity-50"
              >
                {t('history.previous')}
              </button>
              <button
                onClick={() => setOffset(offset + limit)}
                disabled={currentPage >= totalPages}
                className="btn-secondary text-sm disabled:opacity-50"
              >
                {t('history.next')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
