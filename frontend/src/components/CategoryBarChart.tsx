import { useTranslation } from 'react-i18next';
import { CategoryStat } from '@/types';
import { formatCurrency } from '@/utils/format';

interface CategoryBarChartProps {
  data: CategoryStat[];
  currency?: string;
}

// Distinct colors for categories - high contrast palette
const CATEGORY_COLORS = [
  '#ef4444', // red-500
  '#f97316', // orange-500
  '#eab308', // yellow-500
  '#22c55e', // green-500
  '#06b6d4', // cyan-500
  '#3b82f6', // blue-500
  '#8b5cf6', // violet-500
  '#d946ef', // fuchsia-500
  '#f43f5e', // rose-500
  '#14b8a6', // teal-500
  '#6366f1', // indigo-500
  '#84cc16', // lime-500
];

export const CategoryBarChart = ({ data, currency = 'USD' }: CategoryBarChartProps) => {
  const { t } = useTranslation();

  if (!data || data.length === 0) {
    return (
      <div className="card h-80 flex items-center justify-center">
        <p className="text-gray-500">{t('dashboard.noExpenseData')}</p>
      </div>
    );
  }

  // Calculate total for percentage
  const total = data.reduce((sum, item) => sum + Number(item.amount), 0);

  // Sort by amount descending
  const sortedData = [...data].sort((a, b) => Number(b.amount) - Number(a.amount));

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {t('dashboard.expensesByCategory')}
      </h3>
      <div className="space-y-3">
        {sortedData.map((item, index) => {
          const percentage = total > 0 ? (Number(item.amount) / total) * 100 : 0;
          const color = CATEGORY_COLORS[index % CATEGORY_COLORS.length];

          return (
            <div key={item.category} className="flex items-center gap-3">
              {/* Category name */}
              <div className="w-32 flex-shrink-0 text-sm text-gray-700 truncate" title={item.category}>
                {item.category}
              </div>

              {/* Bar container */}
              <div className="flex-1 flex items-center gap-3">
                {/* Progress bar */}
                <div className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden relative">
                  <div
                    className="h-full rounded-full transition-all duration-500 ease-out"
                    style={{
                      width: `${Math.max(percentage, 1)}%`,
                      backgroundColor: color,
                      minWidth: percentage > 0 ? '4px' : '0',
                    }}
                  />
                </div>

                {/* Percentage */}
                <div className="w-12 text-right text-sm font-medium text-gray-600 flex-shrink-0">
                  {percentage.toFixed(0)}%
                </div>
              </div>

              {/* Amount */}
              <div className="w-24 text-right text-sm font-semibold text-gray-900 flex-shrink-0">
                {formatCurrency(Number(item.amount), currency)}
              </div>
            </div>
          );
        })}
      </div>

      {/* Total */}
      <div className="mt-4 pt-3 border-t border-gray-200 flex justify-between items-center">
        <span className="text-sm text-gray-600">{t('dashboard.total')}</span>
        <span className="text-lg font-bold text-gray-900">
          {formatCurrency(total, currency)}
        </span>
      </div>
    </div>
  );
};
