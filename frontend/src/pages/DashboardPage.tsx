import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { StatsCard } from '@/components/StatsCard';
import { CategoryPieChart } from '@/components/CategoryPieChart';
import { RecentTransactions } from '@/components/RecentTransactions';
import { statsApi } from '@/api/client';
import { useAuthStore } from '@/stores/authStore';
import { DashboardStats } from '@/types';

type Period = 'month' | 'year' | 'all';

export const DashboardPage = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState<Period>('month');

  useEffect(() => {
    fetchStats();
  }, [period]);

  const fetchStats = async () => {
    setIsLoading(true);
    try {
      const data = await statsApi.getDashboard({ period });
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const periodLabels: Record<Period, string> = {
    month: t('dashboard.thisMonth'),
    year: t('dashboard.thisYear'),
    all: t('dashboard.allTime'),
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with period selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.title')}</h1>
        
        <div className="flex items-center gap-4">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as Period)}
            className="input py-2 w-40"
          >
            <option value="month">{t('dashboard.thisMonth')}</option>
            <option value="year">{t('dashboard.thisYear')}</option>
            <option value="all">{t('dashboard.allTime')}</option>
          </select>
          
          <Link to="/add" className="btn-primary whitespace-nowrap">
            + {t('dashboard.addTransaction')}
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatsCard
          title={`${t('dashboard.income')} - ${periodLabels[period]}`}
          amount={stats?.total_income || 0}
          type="income"
          currency={user?.currency}
        />
        <StatsCard
          title={`${t('dashboard.expense')} - ${periodLabels[period]}`}
          amount={stats?.total_expense || 0}
          type="expense"
          currency={user?.currency}
        />
        <StatsCard
          title={`${t('dashboard.balance')} - ${periodLabels[period]}`}
          amount={stats?.balance || 0}
          type="balance"
          currency={user?.currency}
        />
      </div>

      {/* Charts and Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CategoryPieChart data={stats?.by_category || []} />
        <RecentTransactions 
          transactions={stats?.recent_transactions || []} 
          currency={user?.currency}
        />
      </div>
    </div>
  );
};
