'use client';

import React from 'react';
import { AlertCircle, XCircle, Wifi, WifiOff } from 'lucide-react';

interface ErrorBannerProps {
  error: string;
  onRetry?: () => void;
  type?: 'error' | 'warning' | 'disconnected';
}

export function ErrorBanner({ error, onRetry, type = 'disconnected' }: ErrorBannerProps) {
  const configs = {
    error: {
      icon: <XCircle className="h-5 w-5" />,
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-800',
      title: 'Error',
    },
    warning: {
      icon: <AlertCircle className="h-5 w-5" />,
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-800',
      title: 'Warning',
    },
    disconnected: {
      icon: <WifiOff className="h-5 w-5" />,
      bgColor: 'bg-slate-50',
      borderColor: 'border-slate-200',
      textColor: 'text-slate-800',
      title: 'Connection Lost',
    },
  };

  const config = configs[type];

  return (
    <div className={`mx-6 mt-6 rounded-xl border ${config.borderColor} ${config.bgColor} p-5 animate-slide-up`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className={config.textColor}>{config.icon}</div>
          <div>
            <h3 className={`text-sm font-semibold ${config.textColor}`}>{config.title}</h3>
            <p className="mt-1 text-sm text-slate-600">{error}</p>
            {type === 'disconnected' && (
              <p className="mt-2 text-xs text-slate-500">
                Make sure the backend server is running at{' '}
                <code className="rounded bg-slate-200 px-2 py-0.5 text-xs">http://localhost:8003</code>
              </p>
            )}
          </div>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-all hover:bg-blue-700 hover:shadow-sm"
          >
            <Wifi className="h-4 w-4" />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
