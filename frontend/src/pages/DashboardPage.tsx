import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { StatsCard } from '@/components/StatsCard';
import { CategoryPieChart } from '@/components/CategoryPieChart';
import { RecentTransactions } from '@/components/RecentTransactions';
import { statsApi } from '@/api/client';
import { DashboardStats } from '@/types';

type Period = 'month' | 'year' | 'all';

export const DashboardPage = () => {
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
    month: 'This Month',
    year: 'This Year',
    all: 'All Time',
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
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        
        <div className="flex items-center gap-4">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as Period)}
            className="input py-2 w-40"
          >
            <option value="month">This Month</option>
            <option value="year">This Year</option>
            <option value="all">All Time</option>
          </select>
          
          <Link to="/add" className="btn-primary whitespace-nowrap">
            + Add Transaction
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatsCard
          title={`Income - ${periodLabels[period]}`}
          amount={stats?.total_income || 0}
          type="income"
        />
        <StatsCard
          title={`Expenses - ${periodLabels[period]}`}
          amount={stats?.total_expense || 0}
          type="expense"
        />
        <StatsCard
          title={`Balance - ${periodLabels[period]}`}
          amount={stats?.balance || 0}
          type="balance"
        />
      </div>

      {/* Charts and Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CategoryPieChart data={stats?.by_category || []} />
        <RecentTransactions transactions={stats?.recent_transactions || []} />
      </div>
    </div>
  );
};
