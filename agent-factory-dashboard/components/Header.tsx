'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { useAuth } from '@/contexts/AuthContext';
import { Search, RefreshCw, CheckCircle, AlertCircle, Moon, Sun } from 'lucide-react';
import { cn } from '@/lib/utils';
import { NotificationPanel, NotificationBell } from '@/components/NotificationPanel';
import { getNotifications } from '@/lib/api';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { refreshMetrics, loading, lastUpdated, error } = useDashboard();
  const { user } = useAuth();
  const [isDark, setIsDark] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Fetch unread notification count
  useEffect(() => {
    const fetchUnreadCount = async () => {
      const data = await getNotifications();
      if (data) {
        setUnreadCount(data.unread_count);
      }
    };

    fetchUnreadCount();
    // Poll every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle notification refresh
  const handleNotificationRefresh = useCallback(async () => {
    const data = await getNotifications();
    if (data) setUnreadCount(data.unread_count);
  }, []);

  // Handle notification panel close
  const handleNotificationClose = useCallback(() => {
    setShowNotifications(false);
    handleNotificationRefresh();
  }, [handleNotificationRefresh]);

  // Initialize dark mode from localStorage or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      document.documentElement.classList.add('dark');
      setIsDark(true);
    }
  }, []);

  const toggleDarkMode = () => {
    const newIsDark = !isDark;
    setIsDark(newIsDark);
    
    if (newIsDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  const formatLastUpdated = (date: Date | null) => {
    if (!date) return '';
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
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
      <div className="px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          {/* Title & Status */}
          <div className="flex-1 min-w-0">
            <h1 className="text-responsive-title bg-gradient-to-r from-fuchsia-600 via-cyan-600 to-teal-600 bg-clip-text text-transparent truncate">{title}</h1>
            {subtitle && (
              <p className="text-responsive-small text-slate-500 dark:text-slate-400 mt-0.5 truncate">{subtitle}</p>
            )}

            {/* Status Indicator */}
            <div className="mt-2 flex items-center gap-2 flex-wrap">
              {error ? (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-red-600 bg-gradient-to-r from-red-50 to-pink-50 px-2.5 sm:px-3 py-1.5 rounded-full border border-red-200 dark:text-red-400 dark:from-red-900/20 dark:to-pink-900/20 dark:border-red-800">
                  <AlertCircle className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                  <span className="text-xs">{error}</span>
                </span>
              ) : lastUpdated ? (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-600 bg-gradient-to-r from-green-50 to-emerald-50 px-2.5 sm:px-3 py-1.5 rounded-full border border-green-200 dark:text-green-400 dark:from-green-900/20 dark:to-emerald-900/20 dark:border-green-800">
                  <CheckCircle className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                  <span className="text-xs hidden sm:inline">Updated:</span> {formatLastUpdated(lastUpdated)}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">
                  <span className="w-2 h-2 bg-gradient-to-r from-fuchsia-500 to-cyan-500 rounded-full animate-pulse" />
                  <span className="text-xs">Loading...</span>
                </span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1.5 sm:gap-2">
            {/* Search - Hidden on small mobile */}
            <div className="hidden sm:block relative group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
              <input
                type="text"
                placeholder="Search..."
                className="input-field w-48 lg:w-64 pl-10 pr-4 text-sm bg-gradient-to-r from-slate-50 to-white focus:from-indigo-50 focus:to-white dark:from-slate-800 dark:to-slate-800 dark:focus:from-indigo-900/20 dark:focus:to-indigo-900/20 transition-all"
              />
            </div>

            {/* Dark Mode Toggle - Always Visible */}
            <button
              onClick={toggleDarkMode}
              className={cn(
                'p-2 rounded-lg transition-all border',
                isDark 
                  ? 'bg-gradient-to-r from-fuchsia-500 to-cyan-500 text-white border-fuchsia-500/30 shadow-lg shadow-fuchsia-500/30' 
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 dark:bg-slate-800 dark:border-slate-700 dark:hover:bg-slate-700 dark:hover:text-slate-300'
              )}
              aria-label="Toggle dark mode"
              title={isDark ? 'Dark Mode On' : 'Dark Mode Off'}
            >
              {isDark ? (
                <Moon className="w-4 h-4 sm:w-5 sm:h-5" />
              ) : (
                <Sun className="w-4 h-4 sm:w-5 sm:h-5" />
              )}
            </button>

            {/* Notifications */}
            <NotificationBell
              unreadCount={unreadCount}
              onClick={() => setShowNotifications(!showNotifications)}
              isOpen={showNotifications}
              onRefresh={handleNotificationRefresh}
            />
            <NotificationPanel
              isOpen={showNotifications}
              onClose={handleNotificationClose}
            />

            {/* Refresh - Hidden on mobile */}
            <button
              onClick={refreshMetrics}
              disabled={loading}
              className={cn(
                'hidden sm:inline-flex items-center px-3 py-2 rounded-lg text-sm font-medium bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700 transition-all',
                loading && 'opacity-50 cursor-not-allowed'
              )}
            >
              <RefreshCw className={cn('w-4 h-4 mr-1.5', loading && 'animate-spin')} />
              <span className="hidden lg:inline">{loading ? 'Refreshing...' : 'Refresh'}</span>
            </button>

            {/* Divider */}
            <div className="w-px h-6 bg-gradient-to-b from-transparent via-slate-200 to-transparent dark:via-slate-700" />

            {/* User */}
            <button className="flex items-center gap-2 sm:gap-3 pl-1.5 group">
              <div className="relative">
                <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-gradient-to-br from-fuchsia-500 via-cyan-500 to-teal-500 flex items-center justify-center text-white text-xs sm:text-sm font-bold shadow-lg shadow-fuchsia-500/30 group-hover:shadow-xl group-hover:shadow-fuchsia-500/40 transition-all">
                  {user?.name ? getInitials(user.name) : 'AU'}
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 sm:w-3 sm:h-3 bg-green-500 rounded-full border-2 border-white dark:border-slate-800"></div>
              </div>
              <div className="text-left hidden lg:block">
                <p className="text-xs sm:text-sm font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors truncate max-w-[120px]">{user?.name || 'Admin User'}</p>
                <p className="text-[10px] sm:text-xs text-slate-500 dark:text-slate-400 truncate">{user?.role || 'Admin'}</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
