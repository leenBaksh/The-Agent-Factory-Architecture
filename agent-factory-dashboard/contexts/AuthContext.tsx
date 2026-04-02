'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
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
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

// Create context with default value to avoid undefined
const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
  error: null,
  clearError: () => {},
});

// Public paths that don't require authentication
const PUBLIC_PATHS = ['/login'];

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
        const token = localStorage.getItem('token');

        if (storedUser && token) {
          const parsedUser = JSON.parse(storedUser);
          if (parsedUser && typeof parsedUser === 'object') {
            setUser(parsedUser);
          }
        }
      } catch (err) {
        console.error('Error checking auth:', err);
        // Clear corrupted data
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Redirect to login if not authenticated (except for public paths)
  useEffect(() => {
    if (!isLoading && !user && !PUBLIC_PATHS.includes(pathname)) {
      router.replace('/login');
    }
  }, [isLoading, user, pathname, router]);

  const login = async (email: string, password: string) => {
    setError(null);
    try {
      // TODO: Replace with actual API call
      // For demo, accept any non-empty credentials
      if (!email || !password) {
        throw new Error('Please enter email and password');
      }

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500));

      // Create mock user
      const mockUser: User = {
        id: '1',
        email: email,
        name: email.split('@')[0],
        role: 'admin',
      };

      // Store auth data
      localStorage.setItem('user', JSON.stringify(mockUser));
      localStorage.setItem('token', 'mock-jwt-token');

      setUser(mockUser);
      router.replace('/');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    setUser(null);
    router.replace('/login');
  };

  const clearError = () => {
    setError(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
