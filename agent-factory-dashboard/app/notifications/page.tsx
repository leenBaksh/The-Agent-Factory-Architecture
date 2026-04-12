'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Bell,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Info,
  Clock,
  Trash2,
  CheckCheck,
  ArrowLeft,
  Filter,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

// Mock data - will be replaced with API calls
const MOCK_NOTIFICATIONS: Notification[] = [
  {
    id: '1',
    type: 'info',
    title: 'New Ticket Assigned',
    message: 'Ticket #1234 has been assigned to your queue. Priority: High. Customer: Acme Corp.',
    timestamp: new Date(Date.now() - 120000),
    read: false,
  },
  {
    id: '2',
    type: 'warning',
    title: 'SLA Breach Warning',
    message: 'Ticket #1230 is approaching SLA breach threshold (15 min remaining). Response time SLA: 95%.',
    timestamp: new Date(Date.now() - 900000),
    read: false,
  },
  {
    id: '3',
    type: 'success',
    title: 'Ticket Resolved',
    message: 'Ticket #1225 has been resolved successfully by Customer Success FTE. Resolution time: 45 minutes.',
    timestamp: new Date(Date.now() - 3600000),
    read: false,
  },
  {
    id: '4',
    type: 'error',
    title: 'FTE Health Check Failed',
    message: 'Technical Support FTE failed health check. Automatic restart initiated. Expected downtime: 2 minutes.',
    timestamp: new Date(Date.now() - 7200000),
    read: true,
  },
  {
    id: '5',
    type: 'success',
    title: 'New FTE Deployed',
    message: 'Sales Support FTE v1.2.0 deployed successfully. All skills updated and A2A protocol active.',
    timestamp: new Date(Date.now() - 86400000),
    read: true,
  },
  {
    id: '6',
    type: 'info',
    title: 'Dashboard Metrics Updated',
    message: 'Real-time metrics aggregation pipeline updated. New SLA thresholds applied to all FTE instances.',
    timestamp: new Date(Date.now() - 172800000),
    read: true,
  },
  {
    id: '7',
    type: 'warning',
    title: 'High Conversation Volume',
    message: 'Customer Success FTE handling 15 active conversations (threshold: 12). Auto-scaling recommended.',
    timestamp: new Date(Date.now() - 259200000),
    read: true,
  },
  {
    id: '8',
    type: 'success',
    title: 'A2A Protocol Sync Complete',
    message: 'All 3 FTE instances successfully synchronized via A2A protocol. Last sync: 5 minutes ago.',
    timestamp: new Date(Date.now() - 345600000),
    read: true,
  },
];

export default function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread' | 'success' | 'warning' | 'error' | 'info'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch notifications from API
    setTimeout(() => {
      setNotifications(MOCK_NOTIFICATIONS);
      setLoading(false);
    }, 300);
  }, []);

  const markAsRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const clearNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const clearAllRead = () => {
    setNotifications((prev) => prev.filter((n) => !n.read));
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getBorderColor = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return 'border-l-green-500';
      case 'warning':
        return 'border-l-amber-500';
      case 'error':
        return 'border-l-red-500';
      case 'info':
        return 'border-l-blue-500';
    }
  };

  const filteredNotifications = notifications.filter((n) => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !n.read;
    return n.type === filter;
  });

  const unreadCount = notifications.filter((n) => !n.read).length;
  const readCount = notifications.filter((n) => n.read).length;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-fuchsia-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">Loading notifications...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            </button>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Bell className="w-6 h-6 text-slate-700 dark:text-slate-300" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-r from-fuchsia-500 to-cyan-500 rounded-full text-white text-[10px] font-bold flex items-center justify-center shadow-lg">
                    {unreadCount}
                  </span>
                )}
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Notifications</h1>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">
                  {unreadCount} unread, {readCount} read
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {readCount > 0 && (
              <button
                onClick={clearAllRead}
                className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                <span className="hidden sm:inline">Clear read</span>
              </button>
            )}
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-gradient-to-r from-fuchsia-500 to-cyan-500 rounded-lg hover:from-fuchsia-600 hover:to-cyan-600 transition-all shadow-lg shadow-fuchsia-500/30"
              >
                <CheckCheck className="w-4 h-4" />
                <span className="hidden sm:inline">Mark all read</span>
              </button>
            )}
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
          <div className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
            <Filter className="w-4 h-4" />
          </div>
          {[
            { key: 'all', label: 'All', count: notifications.length },
            { key: 'unread', label: 'Unread', count: unreadCount },
            { key: 'success', label: 'Success', count: notifications.filter((n) => n.type === 'success').length },
            { key: 'warning', label: 'Warnings', count: notifications.filter((n) => n.type === 'warning').length },
            { key: 'error', label: 'Errors', count: notifications.filter((n) => n.type === 'error').length },
            { key: 'info', label: 'Info', count: notifications.filter((n) => n.type === 'info').length },
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key as typeof filter)}
              className={cn(
                'inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg whitespace-nowrap transition-colors',
                filter === f.key
                  ? 'bg-gradient-to-r from-fuchsia-500 to-cyan-500 text-white shadow-lg shadow-fuchsia-500/30'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
              )}
            >
              {f.label}
              {f.count > 0 && (
                <span
                  className={cn(
                    'px-1.5 py-0.5 text-xs rounded',
                    filter === f.key
                      ? 'bg-white/20 text-white'
                      : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                  )}
                >
                  {f.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Notifications List */}
        <div className="space-y-3">
          {filteredNotifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
              <Bell className="w-16 h-16 text-slate-300 dark:text-slate-600 mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">No notifications</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 text-center">
                {filter === 'all'
                  ? "You're all caught up!"
                  : `No ${filter} notifications to display`}
              </p>
            </div>
          ) : (
            filteredNotifications.map((notification) => (
              <div
                key={notification.id}
                className={cn(
                  'group relative bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 border-l-4 p-5 transition-all hover:shadow-lg',
                  getBorderColor(notification.type),
                  notification.read ? 'opacity-70' : 'opacity-100 shadow-md'
                )}
              >
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div className="flex-shrink-0 mt-1 p-2 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    {getIcon(notification.type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                          {notification.title}
                        </h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                          {notification.message}
                        </p>
                      </div>
                      {!notification.read && (
                        <span className="w-2.5 h-2.5 bg-gradient-to-r from-fuchsia-500 to-cyan-500 rounded-full flex-shrink-0 mt-2" />
                      )}
                    </div>
                    <div className="flex items-center gap-1 mt-3 text-slate-500 dark:text-slate-500">
                      <Clock className="w-3.5 h-3.5" />
                      <span className="text-xs">{formatTimestamp(notification.timestamp)}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex-shrink-0 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    {!notification.read && (
                      <button
                        onClick={() => markAsRead(notification.id)}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-600 rounded-lg transition-colors"
                        title="Mark as read"
                      >
                        <CheckCircle className="w-4 h-4 text-slate-500" />
                      </button>
                    )}
                    <button
                      onClick={() => clearNotification(notification.id)}
                      className="p-2 hover:bg-slate-100 dark:hover:bg-slate-600 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4 text-slate-500" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
