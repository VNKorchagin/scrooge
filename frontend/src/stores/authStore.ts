import { create } from 'zustand';
import { User, Token } from '@/types';
import { authApi } from '@/api/client';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  init: () => void;
}

// Helper to get token from storage
const getStoredToken = (): string | null => {
  return localStorage.getItem('token');
};

export const useAuthStore = create<AuthState>((set, get) => ({
  token: getStoredToken(),
  user: null,
  isAuthenticated: !!getStoredToken(),
  isLoading: false,
  error: null,

  init: () => {
    const token = getStoredToken();
    if (token) {
      set({ token, isAuthenticated: true });
      get().fetchUser();
    }
  },

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const data: Token = await authApi.login(username, password);
      localStorage.setItem('token', data.access_token);
      set({ 
        token: data.access_token, 
        isAuthenticated: true,
        isLoading: false,
        error: null 
      });
      await get().fetchUser();
    } catch (error: any) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Login failed'
      });
      throw error;
    }
  },

  register: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const data: Token = await authApi.register(username, password);
      localStorage.setItem('token', data.access_token);
      set({ 
        token: data.access_token, 
        isAuthenticated: true,
        isLoading: false,
        error: null 
      });
      await get().fetchUser();
    } catch (error: any) {
      set({ 
        isLoading: false, 
        error: error.response?.data?.detail || 'Registration failed'
      });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ 
      token: null, 
      user: null, 
      isAuthenticated: false,
      error: null 
    });
  },

  fetchUser: async () => {
    try {
      const user = await authApi.getMe();
      set({ user });
    } catch (error) {
      get().logout();
    }
  },

  clearError: () => set({ error: null }),
}));

// Initialize auth state on load
if (typeof window !== 'undefined') {
  useAuthStore.getState().init();
}
