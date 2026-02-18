import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/login', { username, password });
    return response.data;
  },
  
  register: async (username: string, password: string, currency: string) => {
    const response = await apiClient.post('/auth/register', { username, password, currency });
    return response.data;
  },
  
  getMe: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};

// Categories API
export const categoriesApi = {
  search: async (query: string) => {
    const response = await apiClient.get(`/categories?q=${encodeURIComponent(query)}`);
    return response.data;
  },
  
  getAll: async () => {
    const response = await apiClient.get('/categories');
    return response.data;
  },
  
  create: async (name: string) => {
    const response = await apiClient.post('/categories', { name });
    return response.data;
  },
};

// Transactions API
export const transactionsApi = {
  getAll: async (params?: Record<string, string | number | undefined>) => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, String(value));
        }
      });
    }
    const response = await apiClient.get(`/transactions?${queryParams.toString()}`);
    return response.data;
  },
  
  create: async (data: {
    type: 'income' | 'expense';
    amount: number;
    category_name: string;
    transaction_date?: string;
    description?: string;
  }) => {
    const response = await apiClient.post('/transactions', data);
    return response.data;
  },
  
  update: async (id: number, data: {
    transaction_date?: string;
    description?: string;
    amount?: number;
    category_name?: string;
  }) => {
    const response = await apiClient.patch(`/transactions/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await apiClient.delete(`/transactions/${id}`);
    return response.data;
  },
};

// Stats API
export const statsApi = {
  getDashboard: async (params?: { period?: string; date_from?: string; date_to?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.period) queryParams.append('period', params.period);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    
    const response = await apiClient.get(`/stats/dashboard?${queryParams.toString()}`);
    return response.data;
  },
};

// Currency API
export const currencyApi = {
  getRate: async (from: string, to: string) => {
    const response = await apiClient.get(`/currency/rate?from_currency=${from}&to_currency=${to}`);
    return response.data;
  },
  
  getPreview: async (newCurrency: string) => {
    const response = await apiClient.post(`/currency/convert?new_currency=${newCurrency}`);
    return response.data;
  },
  
  applyConversion: async (newCurrency: string) => {
    const response = await apiClient.post(`/currency/apply?new_currency=${newCurrency}&confirm=true`);
    return response.data;
  },
};

// User Settings API
export const userApi = {
  updateSettings: async (data: { language?: string; currency?: string }) => {
    const response = await apiClient.patch('/auth/me', data);
    return response.data;
  },
};

export type ExportFormat = 'csv' | 'tsv' | 'xlsx';

// Export API
export const exportApi = {
  exportData: async (format: ExportFormat = 'csv', params?: { type?: string; date_from?: string; date_to?: string; grouped?: string }) => {
    const queryParams = new URLSearchParams();
    queryParams.append('format', format);
    if (params?.type) queryParams.append('type', params.type);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    if (params?.grouped) queryParams.append('grouped', params.grouped);
    
    const response = await apiClient.get(`/export/csv?${queryParams.toString()}`, {
      responseType: 'blob',
    });
    
    // Determine MIME type and extension
    const mimeTypes: Record<ExportFormat, string> = {
      csv: 'text/csv',
      tsv: 'text/tab-separated-values',
      xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    };
    const extensions: Record<ExportFormat, string> = {
      csv: 'csv',
      tsv: 'tsv',
      xlsx: 'xlsx',
    };
    
    // Create download link
    const blob = new Blob([response.data], { type: mimeTypes[format] });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `transactions_${new Date().toISOString().slice(0, 10)}.${extensions[format]}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

// Types for Vault
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

// Vault API
export const vaultApi = {
  getAccounts: async (): Promise<VaultAccount[]> => {
    const response = await apiClient.get('/vault/accounts');
    return response.data;
  },
  
  createAccount: async (data: Omit<VaultAccount, 'id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<VaultAccount> => {
    const response = await apiClient.post('/vault/accounts', data);
    return response.data;
  },
  
  updateAccount: async (id: number, data: Partial<VaultAccount>): Promise<VaultAccount> => {
    const response = await apiClient.patch(`/vault/accounts/${id}`, data);
    return response.data;
  },
  
  deleteAccount: async (id: number): Promise<void> => {
    await apiClient.delete(`/vault/accounts/${id}`);
  },
  
  getSummary: async (): Promise<VaultSummary> => {
    const response = await apiClient.get('/vault/summary');
    return response.data;
  },
  
  getProjection: async (
    period: string = '1_year', 
    includeReinvestment: boolean = true,
    monthlyIncome: number = 0,
    monthlyExpenses: number = 0
  ): Promise<VaultProjection> => {
    const response = await apiClient.post('/vault/projection', {
      period,
      include_reinvestment: includeReinvestment,
      estimated_monthly_income: monthlyIncome,
      estimated_monthly_expenses: monthlyExpenses,
    });
    return response.data;
  },
  
  getSettings: async (): Promise<VaultSettings> => {
    const response = await apiClient.get('/vault/settings');
    return response.data;
  },
  
  updateSettings: async (data: Partial<VaultSettings>): Promise<VaultSettings> => {
    const response = await apiClient.patch('/vault/settings', data);
    return response.data;
  },
};
