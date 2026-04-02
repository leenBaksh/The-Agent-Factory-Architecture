'use client';

import React from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { useAuth } from '@/contexts/AuthContext';
import { Search, Bell, RefreshCw, CheckCircle, AlertCircle, Moon, Sun } from 'lucide-react';
import { cn } from '@/lib/utils';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { refreshMetrics, loading, lastUpdated, error } = useDashboard();
  const { user } = useAuth();

  const formatLastUpdated = (date: Date | null) => {
    if (!date) return '';
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const toggleDarkMode = () => {
    document.documentElement.classList.toggle('dark');
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <header className="header">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Title & Status */}
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">{title}</h1>
            {subtitle && (
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>
            )}

            {/* Status Indicator */}
            <div className="mt-2 flex items-center gap-2">
              {error ? (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-red-600 bg-red-50 px-2.5 py-1 rounded-md dark:text-red-400 dark:bg-red-900/20">
                  <AlertCircle className="w-3.5 h-3.5" />
                  {error}
                </span>
              ) : lastUpdated ? (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-600 bg-green-50 px-2.5 py-1 rounded-md dark:text-green-400 dark:bg-green-900/20">
                  <CheckCircle className="w-3.5 h-3.5" />
                  Updated: {formatLastUpdated(lastUpdated)}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">
                  <span className="w-2 h-2 bg-slate-300 rounded-full animate-pulse dark:bg-slate-600" />
                  Loading...
                </span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search..."
                className="input-field w-64 pl-10 pr-4"
              />
            </div>

            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="btn-icon"
              aria-label="Toggle dark mode"
            >
              <Sun className="w-5 h-5 block dark:hidden" />
              <Moon className="w-5 h-5 hidden dark:block" />
            </button>

            {/* Notifications */}
            <button className="btn-icon relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white dark:ring-slate-800" />
            </button>

            {/* Refresh */}
            <button
              onClick={refreshMetrics}
              disabled={loading}
              className={cn(
                'btn-secondary',
                loading && 'opacity-50 cursor-not-allowed'
              )}
            >
              <RefreshCw className={cn('w-4 h-4 mr-2', loading && 'animate-spin')} />
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>

            {/* Divider */}
            <div className="w-px h-8 bg-slate-200 mx-2 dark:bg-slate-700" />

            {/* User */}
            <button className="flex items-center gap-3 pl-2">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-600 to-indigo-700 flex items-center justify-center text-white text-sm font-semibold shadow-md">
                {user?.name ? getInitials(user.name) : 'JD'}
              </div>
              <div className="text-left hidden lg:block">
                <p className="text-sm font-medium text-slate-900 dark:text-white">{user?.name || 'John Doe'}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{user?.role || 'Admin'}</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
