export interface User {
  id: number;
  username: string;
  language: string;
  currency: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Category {
  id: number;
  user_id: number;
  name: string;
  created_at: string;
}

export type TransactionType = 'income' | 'expense';
export type TransactionSource = 'manual' | 'import_csv' | 'import_pdf' | 'telegram';

export interface Transaction {
  id: number;
  user_id: number;
  type: TransactionType;
  amount: number;
  category_id: number | null;
  category_name: string;
  description: string | null;
  raw_description: string | null;
  transaction_date: string;
  source: TransactionSource;
  created_at: string;
}

export interface TransactionCreate {
  type: TransactionType;
  amount: number;
  category_name: string;
  transaction_date: string;
  description?: string;
}

export interface TransactionFilter {
  type?: TransactionType;
  date_from?: string;
  date_to?: string;
  category_id?: number;
  limit?: number;
  offset?: number;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

export interface CategoryStat {
  category: string;
  amount: number;
  percentage: number;
}

export interface DashboardStats {
  total_income: number;
  total_expense: number;
  balance: number;
  by_category: CategoryStat[];
  recent_transactions: RecentTransaction[];
}

export interface RecentTransaction {
  id: number;
  type: TransactionType;
  amount: number;
  category_name: string;
  description: string | null;
  transaction_date: string;
}

// Vault types
export interface VaultAccount {
  id: number;
  user_id: number;
  name: string;
  account_type: 'checking' | 'savings' | 'deposit' | 'brokerage' | 'loan';
  balance: number;
  currency: string;
  interest_rate?: number;
  end_date?: string;
  monthly_payment?: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface VaultSummary {
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  checking_balance: number;
  savings_balance: number;
  deposits_balance: number;
  brokerage_balance: number;
  loans_balance: number;
}

export interface VaultProjectionPoint {
  date: string;
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  milestones: Array<{
    type: string;
    name: string;
  }>;
}

export interface VaultProjection {
  projection: VaultProjectionPoint[];
  summary: VaultSummary;
  milestones: Array<{
    date: string;
    type: string;
    name: string;
    amount?: number;
    month: number;
  }>;
}

export interface VaultSettings {
  id?: number;
  user_id?: number;
  estimated_monthly_income?: number;
  estimated_monthly_expenses?: number;
  default_projection_period?: string;
  reinvest_deposits?: string;
  created_at?: string;
  updated_at?: string;
}
