export interface User {
  id: number;
  username: string;
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
