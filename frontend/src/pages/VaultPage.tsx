import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { vaultApi } from '@/api/client';
import type { VaultAccount } from '@/types';
import { useAuthStore } from '@/stores/authStore';
import { formatCurrency } from '@/utils/format';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceDot
} from 'recharts';

type AccountType = 'checking' | 'savings' | 'deposit' | 'brokerage' | 'loan';
type PeriodType = 'month' | 'quarter' | 'half_year' | '1_year' | '3_years' | '5_years';

const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  checking: 'vault.accountTypes.checking',
  savings: 'vault.accountTypes.savings',
  deposit: 'vault.accountTypes.deposit',
  brokerage: 'vault.accountTypes.brokerage',
  loan: 'vault.accountTypes.loan',
};

const PERIOD_LABELS: Record<PeriodType, string> = {
  month: 'vault.periods.month',
  quarter: 'vault.periods.quarter',
  half_year: 'vault.periods.halfYear',
  '1_year': 'vault.periods.year',
  '3_years': 'vault.periods.3years',
  '5_years': 'vault.periods.5years',
};

export const VaultPage = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [accounts, setAccounts] = useState<VaultAccount[]>([]);
  const [summary, setSummary] = useState({
    total_assets: 0, total_liabilities: 0, net_worth: 0,
    checking_balance: 0, savings_balance: 0, deposits_balance: 0,
    brokerage_balance: 0, loans_balance: 0,
  });
  const [projection, setProjection] = useState<any[]>([]);
  const [milestones, setMilestones] = useState<any[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>('1_year');
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingAccount, setEditingAccount] = useState<VaultAccount | null>(null);
  const [formData, setFormData] = useState({
    name: '', account_type: 'checking' as AccountType, balance: '',
    interest_rate: '', end_date: '', monthly_payment: '', description: '',
  });
  
  // Monthly cash flow settings
  const [monthlyIncome, setMonthlyIncome] = useState<number>(0);
  const [monthlyExpenses, setMonthlyExpenses] = useState<number>(0);
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  useEffect(() => { fetchData(); }, []);
  useEffect(() => { if (accounts.length > 0 || settingsLoaded) fetchProjection(); }, [accounts, selectedPeriod, monthlyIncome, monthlyExpenses]);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [accountsData, summaryData, settingsData] = await Promise.all([
        vaultApi.getAccounts(),
        vaultApi.getSummary(),
        vaultApi.getSettings().catch(() => null),
      ]);
      setAccounts(accountsData);
      setSummary(summaryData);
      if (settingsData) {
        setMonthlyIncome(settingsData.estimated_monthly_income || 0);
        setMonthlyExpenses(settingsData.estimated_monthly_expenses || 0);
      }
      setSettingsLoaded(true);
    } catch (error) { console.error('Failed to fetch vault data:', error); }
    finally { setIsLoading(false); }
  };

  const fetchProjection = async () => {
    try {
      const data = await vaultApi.getProjection(selectedPeriod, true, monthlyIncome, monthlyExpenses);
      setProjection(data.projection);
      setMilestones(data.milestones);
    } catch (error) { console.error('Failed to fetch projection:', error); }
  };
  
  const saveSettings = async (income: number, expenses: number) => {
    try {
      await vaultApi.updateSettings({
        estimated_monthly_income: income,
        estimated_monthly_expenses: expenses,
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data: any = {
        name: formData.name, account_type: formData.account_type,
        balance: parseFloat(formData.balance) || 0, currency: user?.currency || 'USD',
        description: formData.description || undefined,
      };
      
      if (formData.account_type === 'loan') {
        data.monthly_payment = formData.monthly_payment ? parseFloat(formData.monthly_payment) : undefined;
      } else {
        data.interest_rate = formData.interest_rate ? parseFloat(formData.interest_rate) : undefined;
        if (formData.account_type === 'deposit') {
          data.end_date = formData.end_date || undefined;
        }
      }
      
      if (editingAccount) {
        await vaultApi.updateAccount(editingAccount.id, data);
      } else {
        await vaultApi.createAccount(data);
      }
      setShowAddModal(false);
      setEditingAccount(null);
      resetForm();
      fetchData();
    } catch (error) {
      console.error('Failed to save account:', error);
      alert(t('errors.serverError'));
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm(t('vault.confirmDelete'))) return;
    try {
      await vaultApi.deleteAccount(id);
      fetchData();
    } catch (error) { console.error('Failed to delete account:', error); alert(t('errors.serverError')); }
  };

  const resetForm = () => setFormData({
    name: '', account_type: 'checking', balance: '',
    interest_rate: '', end_date: '', monthly_payment: '', description: '',
  });

  const openEditModal = (account: VaultAccount) => {
    setEditingAccount(account);
    setFormData({
      name: account.name, account_type: account.account_type,
      balance: account.balance.toString(),
      interest_rate: account.interest_rate?.toString() || '',
      end_date: account.end_date || '',
      monthly_payment: account.monthly_payment?.toString() || '',
      description: account.description || '',
    });
    setShowAddModal(true);
  };

  const assetAccounts = accounts.filter(a => a.account_type !== 'loan');
  const loanAccounts = accounts.filter(a => a.account_type === 'loan');

  const chartData = projection.map(p => ({
    date: new Date(p.date).toLocaleDateString('ru-RU', { month: 'short', year: '2-digit' }),
    assets: Number(p.total_assets),
    liabilities: Number(p.total_liabilities),
    netWorth: Number(p.net_worth),
    fullDate: p.date,
    milestones: p.milestones,
  }));

  const milestoneDots = milestones.map((m, idx) => {
    const point = chartData[m.month];
    if (!point) return null;
    return {
      key: idx,
      month: m.month,
      date: point.date,
      type: m.type,
      name: m.name,
      x: point.date,
      y: m.type === 'deposit_maturity' ? point.assets : point.liabilities,
      fill: m.type === 'deposit_maturity' ? '#22c55e' : '#ef4444',
    };
  }).filter(Boolean);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value, user?.currency)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const isLoan = formData.account_type === 'loan';
  const showInterestRate = !isLoan && formData.account_type !== 'checking' && formData.account_type !== 'brokerage';
  const showEndDate = !isLoan && formData.account_type === 'deposit';
  const showMonthlyPayment = isLoan;

  // Calculate loan payoff date based on balance and monthly payment
  const calculateLoanPayoffDate = (balance: number, monthlyPayment?: number): Date | null => {
    if (!monthlyPayment || monthlyPayment <= 0) return null;
    const monthsToPayoff = Math.ceil(balance / monthlyPayment);
    if (monthsToPayoff <= 0 || monthsToPayoff > 1200) return null; // > 100 years is invalid
    const date = new Date();
    date.setMonth(date.getMonth() + monthsToPayoff);
    return date;
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('vault.title')}</h1>
          <p className="text-sm text-gray-500">{t('vault.subtitle')}</p>
        </div>
        <button
          onClick={() => { setEditingAccount(null); resetForm(); setShowAddModal(true); }}
          className="btn-primary"
        >+ {t('vault.addAccount')}</button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-green-50 border-green-200">
          <p className="text-sm font-medium text-green-700">{t('vault.totalAssets')}</p>
          <p className="text-2xl font-bold text-green-800">
            {formatCurrency(summary.total_assets, user?.currency)}
          </p>
        </div>
        <div className="card bg-red-50 border-red-200">
          <p className="text-sm font-medium text-red-700">{t('vault.totalLiabilities')}</p>
          <p className="text-2xl font-bold text-red-800">
            {formatCurrency(summary.total_liabilities, user?.currency)}
          </p>
        </div>
        <div className="card bg-blue-50 border-blue-200">
          <p className="text-sm font-medium text-blue-700">{t('vault.netWorth')}</p>
          <p className="text-2xl font-bold text-blue-800">
            {formatCurrency(summary.net_worth, user?.currency)}
          </p>
        </div>
      </div>

      {/* Monthly Cash Flow */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('vault.cashFlow')}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('vault.monthlyIncome')}</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={monthlyIncome || ''}
                onChange={(e) => {
                  const val = parseFloat(e.target.value) || 0;
                  setMonthlyIncome(val);
                  saveSettings(val, monthlyExpenses);
                }}
                className="input flex-1"
                placeholder="0"
              />
              <span className="flex items-center text-gray-500 text-sm">{user?.currency}</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">{t('vault.monthlyIncomeDesc')}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('vault.monthlyExpenses')}</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={monthlyExpenses || ''}
                onChange={(e) => {
                  const val = parseFloat(e.target.value) || 0;
                  setMonthlyExpenses(val);
                  saveSettings(monthlyIncome, val);
                }}
                className="input flex-1"
                placeholder="0"
              />
              <span className="flex items-center text-gray-500 text-sm">{user?.currency}</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">{t('vault.monthlyExpensesDesc')}</p>
          </div>
        </div>
        {monthlyIncome > 0 || monthlyExpenses > 0 ? (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">{t('vault.monthlySavings')}</span>
              <span className={`font-semibold ${monthlyIncome - monthlyExpenses >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(monthlyIncome - monthlyExpenses, user?.currency)}
              </span>
            </div>
          </div>
        ) : null}
      </div>

      {/* Accounts List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Assets */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {t('vault.assets')}
            <span className="text-sm font-normal text-gray-500 ml-2">
              ({formatCurrency(summary.total_assets, user?.currency)})
            </span>
          </h2>
          <div className="space-y-3">
            {assetAccounts.length === 0 ? (
              <p className="text-gray-500 text-center py-4">{t('vault.noAssets')}</p>
            ) : assetAccounts.map(account => (
              <div key={account.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{account.name}</p>
                  <p className="text-xs text-gray-500">
                    {t(ACCOUNT_TYPE_LABELS[account.account_type])}
                    {account.interest_rate ? ` • ${account.interest_rate}%` : ''}
                    {account.end_date ? ` • ${t('vault.matures')} ${new Date(account.end_date).toLocaleDateString()}` : ''}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-gray-900">
                    {formatCurrency(account.balance, user?.currency)}
                  </span>
                  <button onClick={() => openEditModal(account)} className="text-gray-400 hover:text-primary-600">✏️</button>
                  <button onClick={() => handleDelete(account.id)} className="text-gray-400 hover:text-danger-600">🗑️</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Liabilities */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {t('vault.liabilities')}
            <span className="text-sm font-normal text-gray-500 ml-2">
              ({formatCurrency(summary.total_liabilities, user?.currency)})
            </span>
          </h2>
          <div className="space-y-3">
            {loanAccounts.length === 0 ? (
              <p className="text-gray-500 text-center py-4">{t('vault.noLiabilities')}</p>
            ) : loanAccounts.map(account => {
              const payoffDate = calculateLoanPayoffDate(account.balance, account.monthly_payment);
              return (
                <div key={account.id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{account.name}</p>
                    <p className="text-xs text-gray-500">
                      {account.monthly_payment ? `${formatCurrency(account.monthly_payment, user?.currency)}/${t('vault.month')}` : ''}
                      {payoffDate ? ` • ${t('vault.paidOff')} ${payoffDate.toLocaleDateString()}` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-danger-600">
                      {formatCurrency(account.balance, user?.currency)}
                    </span>
                    <button onClick={() => openEditModal(account)} className="text-gray-400 hover:text-primary-600">✏️</button>
                    <button onClick={() => handleDelete(account.id)} className="text-gray-400 hover:text-danger-600">🗑️</button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Projection Chart */}
      {(accounts.length > 0 || monthlyIncome > 0 || monthlyExpenses > 0) && (
        <div className="card">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <h2 className="text-lg font-semibold text-gray-900">{t('vault.projection')}</h2>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value as PeriodType)}
              className="input py-1.5 text-sm w-40"
            >
              {Object.entries(PERIOD_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{t(label)}</option>
              ))}
            </select>
          </div>

          {projection.length > 0 ? (
            <>
              {/* Chart with horizontal scroll on mobile */}
              <div className="h-80 -mx-4 sm:mx-0 overflow-x-auto overflow-y-hidden">
                <div className="min-w-[600px] sm:w-full h-full px-4 sm:px-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 11 }} 
                        interval="preserveStartEnd"
                        angle={0}
                        height={30}
                      />
                      <YAxis 
                        tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} 
                        tick={{ fontSize: 11 }}
                        width={45}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: '12px' }} />
                      <Line type="monotone" dataKey="assets" name={t('vault.assets')} stroke="#22c55e" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="liabilities" name={t('vault.liabilities')} stroke="#ef4444" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="netWorth" name={t('vault.netWorth')} stroke="#3b82f6" strokeWidth={2} dot={false} />
                      {milestoneDots.map((m: any) => (
                        <ReferenceDot
                          key={m.key}
                          x={m.x}
                          y={m.y}
                          r={5}
                          fill={m.fill}
                          stroke="white"
                          strokeWidth={2}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              
              {/* Mobile scroll hint */}
              <p className="text-xs text-gray-400 text-center mt-2 sm:hidden">← {t('vault.scrollToSee')} →</p>

              {/* Final Values Summary */}
              {projection.length > 0 && (
                <div className="mt-6 pt-4 border-t border-gray-200">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">{t('vault.projectionEnd')}</h3>
                  <div className="grid grid-cols-3 gap-2 sm:gap-4">
                    <div className="text-center p-2 sm:p-3 bg-green-50 rounded-lg">
                      <p className="text-xs text-green-600 mb-1">{t('vault.assets')}</p>
                      <p className="text-sm sm:text-base font-bold text-green-700">
                        {formatCurrency(chartData[chartData.length - 1]?.assets || 0, user?.currency)}
                      </p>
                    </div>
                    <div className="text-center p-2 sm:p-3 bg-red-50 rounded-lg">
                      <p className="text-xs text-red-600 mb-1">{t('vault.liabilities')}</p>
                      <p className="text-sm sm:text-base font-bold text-red-700">
                        {formatCurrency(chartData[chartData.length - 1]?.liabilities || 0, user?.currency)}
                      </p>
                    </div>
                    <div className="text-center p-2 sm:p-3 bg-blue-50 rounded-lg">
                      <p className="text-xs text-blue-600 mb-1">{t('vault.netWorth')}</p>
                      <p className="text-sm sm:text-base font-bold text-blue-700">
                        {formatCurrency(chartData[chartData.length - 1]?.netWorth || 0, user?.currency)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : <p className="text-gray-500 text-center py-8">{t('vault.noProjection')}</p>}

          {milestones.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-4 text-sm">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span className="text-gray-600">{t('vault.maturity')}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span className="text-gray-600">{t('vault.loanEnd')}</span>
              </div>
            </div>
          )}

          {milestones.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-3">{t('vault.upcomingEvents')}</h3>
              <div className="space-y-2">
                {milestones.slice(0, 5).map((milestone, idx) => (
                  <div key={idx} className={`flex items-center gap-3 text-sm ${milestone.type === 'deposit_maturity' ? 'text-green-700' : 'text-red-700'}`}>
                    <span className="w-2 h-2 rounded-full bg-current"></span>
                    <span className="text-gray-500">{new Date(milestone.date).toLocaleDateString()}:</span>
                    <span className="font-medium">
                      {milestone.type === 'deposit_maturity' 
                        ? t('vault.depositMatures', { name: milestone.name })
                        : t('vault.loanPayoff', { name: milestone.name })}
                    </span>
                    {milestone.amount && <span className="text-gray-600">{formatCurrency(milestone.amount, user?.currency)}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {editingAccount ? t('vault.editAccount') : t('vault.addAccount')}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('vault.accountName')}</label>
                <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="input" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('vault.accountType')}</label>
                <select value={formData.account_type} onChange={(e) => setFormData({ ...formData, account_type: e.target.value as AccountType })} className="input" disabled={!!editingAccount}>
                  <option value="checking">{t(ACCOUNT_TYPE_LABELS.checking)}</option>
                  <option value="savings">{t(ACCOUNT_TYPE_LABELS.savings)}</option>
                  <option value="deposit">{t(ACCOUNT_TYPE_LABELS.deposit)}</option>
                  <option value="brokerage">{t(ACCOUNT_TYPE_LABELS.brokerage)}</option>
                  <option value="loan">{t(ACCOUNT_TYPE_LABELS.loan)}</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {isLoan ? t('vault.remainingDebt') : t('vault.balance')}
                </label>
                <input type="number" step="0.01" value={formData.balance} onChange={(e) => setFormData({ ...formData, balance: e.target.value })} className="input" required />
              </div>
              {showInterestRate && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('vault.interestRate')}</label>
                  <input type="number" step="0.01" value={formData.interest_rate} onChange={(e) => setFormData({ ...formData, interest_rate: e.target.value })} className="input" placeholder="%" />
                </div>
              )}
              {showEndDate && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('vault.endDate')}</label>
                  <input type="date" value={formData.end_date} onChange={(e) => setFormData({ ...formData, end_date: e.target.value })} className="input" />
                </div>
              )}
              {showMonthlyPayment && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('vault.monthlyPayment')}</label>
                  <input type="number" step="0.01" value={formData.monthly_payment} onChange={(e) => setFormData({ ...formData, monthly_payment: e.target.value })} className="input" />
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('vault.description')}</label>
                <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} className="input" rows={2} />
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowAddModal(false)} className="flex-1 btn-secondary">{t('common.cancel')}</button>
                <button type="submit" className="flex-1 btn-primary">{editingAccount ? t('common.save') : t('vault.addAccount')}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};