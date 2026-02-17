import { formatCurrency } from '@/utils/format';

interface StatsCardProps {
  title: string;
  amount: number;
  type: 'income' | 'expense' | 'balance';
}

export const StatsCard = ({ title, amount, type }: StatsCardProps) => {
  const colorClasses = {
    income: 'text-primary-600',
    expense: 'text-danger-600',
    balance: amount >= 0 ? 'text-primary-600' : 'text-danger-600',
  };

  return (
    <div className="stat-card">
      <span className="stat-label">{title}</span>
      <span className={`stat-value ${colorClasses[type]}`}>
        {formatCurrency(amount)}
      </span>
    </div>
  );
};
