import { create } from 'zustand';
import { persist } from 'zustand/middleware';
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
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const data: Token = await authApi.login(username, password);
          set({ 
            token: data.access_token, 
            isAuthenticated: true,
            isLoading: false,
            error: null 
          });
          localStorage.setItem('token', data.access_token);
          // Fetch user data after login
          await get().fetchUser();
        } catch (error) {
          set({ 
            isLoading: false, 
            error: error instanceof Error ? error.message : 'Login failed' 
          });
          throw error;
        }
      },

      register: async (username: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const data: Token = await authApi.register(username, password);
          set({ 
            token: data.access_token, 
            isAuthenticated: true,
            isLoading: false,
            error: null 
          });
          localStorage.setItem('token', data.access_token);
          // Fetch user data after registration
          await get().fetchUser();
        } catch (error) {
          set({ 
            isLoading: false, 
            error: error instanceof Error ? error.message : 'Registration failed' 
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
          // If fetching user fails, logout
          get().logout();
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
);

// Initialize auth state from localStorage
const token = localStorage.getItem('token');
if (token) {
  useAuthStore.setState({ token, isAuthenticated: true });
  useAuthStore.getState().fetchUser();
}
