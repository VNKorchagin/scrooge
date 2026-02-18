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

// Export API
export const exportApi = {
  exportCSV: async (params?: { type?: string; date_from?: string; date_to?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.type) queryParams.append('type', params.type);
    if (params?.date_from) queryParams.append('date_from', params.date_from);
    if (params?.date_to) queryParams.append('date_to', params.date_to);
    
    const response = await apiClient.get(`/export/csv?${queryParams.toString()}`, {
      responseType: 'blob',
    });
    
    // Create download link
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `transactions_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
