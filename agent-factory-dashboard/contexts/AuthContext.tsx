'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{requires2FA?: boolean; tempToken?: string}>;
  verify2FA: (email: string, code: string, tempToken: string) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
  refreshToken: () => Promise<boolean>;
}

// Create context with default value to avoid undefined
const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  login: async () => ({}),
  verify2FA: async () => {},
  logout: () => {},
  error: null,
  clearError: () => {},
  refreshToken: async () => false,
});

// Public paths that don't require authentication
const PUBLIC_PATHS = ['/login'];

// Backend API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const storedUser = localStorage.getItem('user');
        const accessToken = localStorage.getItem('accessToken');

        if (storedUser && accessToken) {
          const parsedUser = JSON.parse(storedUser);
          if (parsedUser && typeof parsedUser === 'object') {
            // Verify token is still valid by trying to refresh it
            const tokenValid = await refreshTokenSilent();
            if (tokenValid) {
              setUser(parsedUser);
            } else {
              // Token invalid, clear storage
              localStorage.removeItem('user');
              localStorage.removeItem('accessToken');
              localStorage.removeItem('refreshToken');
            }
          }
        }
      } catch (err) {
        console.error('Error checking auth:', err);
        // Clear corrupted data
        localStorage.removeItem('user');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Silent token refresh
  const refreshTokenSilent = async (): Promise<boolean> => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) return false;

      const response = await fetch(`${API_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return false;

      const data = await response.json();
      localStorage.setItem('accessToken', data.access_token);
      return true;
    } catch (err) {
      console.error('Token refresh failed:', err);
      return false;
    }
  };

  // Redirect to login if not authenticated (except for public paths)
  useEffect(() => {
    if (!isLoading && !user && !PUBLIC_PATHS.includes(pathname)) {
      router.replace('/login');
    }
  }, [isLoading, user, pathname, router]);

  const login = async (email: string, password: string) => {
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle rate limiting
        if (response.status === 429) {
          const retryAfter = data.detail?.retry_after || 300;
          const minutes = Math.ceil(retryAfter / 60);
          throw new Error(`Too many attempts. Please try again in ${minutes} minute${minutes > 1 ? 's' : ''}.`);
        }
        
        throw new Error(data.detail || 'Login failed. Please check your credentials.');
      }

      // Check if 2FA is required
      if (data.requires_2fa) {
        return { requires2FA: true, tempToken: data.temp_token };
      }

      // Store auth data
      if (data.tokens) {
        localStorage.setItem('user', JSON.stringify({
          id: data.tokens.user_id,
          email: email,
          name: data.tokens.name || email.split('@')[0],
          role: data.tokens.role || 'User',
        }));
        localStorage.setItem('accessToken', data.tokens.access_token);
        localStorage.setItem('refreshToken', data.tokens.refresh_token);

        setUser({
          id: data.tokens.user_id || '1',
          email: email,
          name: data.tokens.name || email.split('@')[0],
          role: data.tokens.role || 'User',
        });

        router.replace('/');
      }

      return {};
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      throw err;
    }
  };

  const verify2FA = async (email: string, code: string, tempToken: string) => {
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/auth/verify-2fa`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, code, temp_token: tempToken }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle rate limiting
        if (response.status === 429) {
          const retryAfter = data.detail?.retry_after || 300;
          const minutes = Math.ceil(retryAfter / 60);
          throw new Error(`Too many attempts. Please try again in ${minutes} minute${minutes > 1 ? 's' : ''}.`);
        }
        
        throw new Error(data.detail || 'Invalid 2FA code. Please try again.');
      }

      // Store auth data
      if (data.tokens) {
        localStorage.setItem('user', JSON.stringify({
          id: data.tokens.user_id || '1',
          email: email,
          name: data.tokens.name || email.split('@')[0],
          role: data.tokens.role || 'User',
        }));
        localStorage.setItem('accessToken', data.tokens.access_token);
        localStorage.setItem('refreshToken', data.tokens.refresh_token);

        setUser({
          id: data.tokens.user_id || '1',
          email: email,
          name: data.tokens.name || email.split('@')[0],
          role: data.tokens.role || 'User',
        });

        router.replace('/');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '2FA verification failed';
      setError(errorMessage);
      throw err;
    }
  };

  const logout = useCallback(() => {
    localStorage.removeItem('user');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setUser(null);
    router.replace('/login');
  }, [router]);

  const clearError = () => {
    setError(null);
  };

  const refreshToken = async (): Promise<boolean> => {
    return await refreshTokenSilent();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        verify2FA,
        logout,
        error,
        clearError,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
