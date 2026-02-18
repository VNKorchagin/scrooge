import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { transactionsApi, exportApi } from '@/api/client';
import { useAuthStore } from '@/stores/authStore';
import { Transaction, TransactionType } from '@/types';
import { formatCurrency, formatDateTime } from '@/utils/format';

// Quick filter period types
type QuickFilter = 'current_month' | '30_days' | 'quarter' | 'half_year' | 'year' | 'custom';

// Trash icon component
const TrashIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

// Edit icon component
const EditIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
  </svg>
);

// Info/Description icon component
const InfoIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

// Check icon component
const CheckIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

// X icon component
const XIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

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

  // Edit state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDate, setEditDate] = useState('');

  // Get user's currency
  const userCurrency = user?.currency || 'USD';

  // Initialize with current month dates
  useEffect(() => {
    applyQuickFilter('current_month');
  }, []);

  useEffect(() => {
    fetchTransactions();
  }, [offset, filterType, dateFrom, dateTo]);

  // Format date for input (YYYY-MM-DDTHH:mm)
  const formatDateTimeForInput = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  // Format date for input (YYYY-MM-DD) in local timezone
  const formatDateForInput = (date: Date): string => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Get start of day in UTC for API requests
  const getStartOfDayUTC = (dateStr: string): string => {
    // Create date at start of day (00:00:00) in local timezone, then convert to UTC ISO
    const date = new Date(dateStr + 'T00:00:00');
    return date.toISOString();
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
      // date_from: start of day (00:00:00) - inclusive
      if (dateFrom) params.date_from = getStartOfDayUTC(dateFrom);
      // date_to: end of day (23:59:59) - inclusive
      if (dateTo) {
        const endOfDay = new Date(dateTo + 'T23:59:59');
        params.date_to = endOfDay.toISOString();
      }

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

  const startEditing = (transaction: Transaction) => {
    setEditingId(transaction.id);
    const date = transaction.transaction_date 
      ? new Date(transaction.transaction_date)
      : new Date();
    setEditDate(formatDateTimeForInput(date));
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditDate('');
  };

  const saveEdit = async (id: number) => {
    try {
      await transactionsApi.update(id, {
        transaction_date: new Date(editDate).toISOString(),
      });
      setEditingId(null);
      fetchTransactions();
    } catch (error) {
      console.error('Failed to update transaction:', error);
      alert(t('errors.serverError'));
    }
  };

  const handleExport = async () => {
    try {
      const params: { type?: string; date_from?: string; date_to?: string } = {};
      if (filterType) params.type = filterType;
      // date_from: start of day (00:00:00) - inclusive
      if (dateFrom) params.date_from = getStartOfDayUTC(dateFrom);
      // date_to: end of day (23:59:59) - inclusive
      if (dateTo) {
        const endOfDay = new Date(dateTo + 'T23:59:59');
        params.date_to = endOfDay.toISOString();
      }
      
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
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.type')}</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.category')}</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.amount')}</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.created')}</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">{t('transaction.date')}</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-500 w-20"></th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr key={transaction.id} className="border-b border-gray-100 hover:bg-gray-50">
                  {/* Type */}
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

                  {/* Category with description preview */}
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-900">{transaction.category_name}</span>
                      {transaction.description && (
                        <div className="group relative">
                          <button className="text-gray-400 hover:text-gray-600 transition-colors">
                            <InfoIcon />
                          </button>
                          <div className="absolute left-0 bottom-full mb-2 w-64 p-3 bg-gray-800 text-white text-sm rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 shadow-lg">
                            <p className="font-medium mb-1">{t('transaction.description')}:</p>
                            <p className="text-gray-300">{transaction.description}</p>
                            <div className="absolute top-full left-4 w-2 h-2 bg-gray-800 rotate-45"></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </td>

                  {/* Amount */}
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

                  {/* Created At */}
                  <td className="py-3 px-4 text-sm text-gray-500">
                    {transaction.created_at 
                      ? formatDateTime(transaction.created_at)
                      : '-'}
                  </td>

                  {/* Transaction Date - Editable */}
                  <td className="py-3 px-4">
                    {editingId === transaction.id ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="datetime-local"
                          value={editDate}
                          onChange={(e) => setEditDate(e.target.value)}
                          className="input text-sm py-1"
                        />
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">
                          {transaction.transaction_date 
                            ? formatDateTime(transaction.transaction_date)
                            : '-'}
                        </span>
                        <button
                          onClick={() => startEditing(transaction)}
                          className="text-gray-400 hover:text-primary-600 transition-colors"
                          title={t('transaction.edit')}
                        >
                          <EditIcon />
                        </button>
                      </div>
                    )}
                  </td>

                  {/* Actions: Edit/Save and Delete */}
                  <td className="py-3 px-4 text-center">
                    {editingId === transaction.id ? (
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => saveEdit(transaction.id)}
                          className="text-green-600 hover:text-green-700 transition-colors p-1"
                          title={t('transaction.save')}
                        >
                          <CheckIcon />
                        </button>
                        <button
                          onClick={cancelEditing}
                          className="text-gray-400 hover:text-gray-600 transition-colors p-1"
                          title={t('transaction.cancel')}
                        >
                          <XIcon />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleDelete(transaction.id)}
                        className="text-gray-400 hover:text-danger-600 transition-colors p-1"
                        title={t('transaction.delete')}
                      >
                        <TrashIcon />
                      </button>
                    )}
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
