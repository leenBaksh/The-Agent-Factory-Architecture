'use client';

import React from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { AlertTriangle, Clock, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export function SLABreachesPanel() {
  const { slaBreaches, loading } = useDashboard();

  if (loading) {
    return <SLASkeleton />;
  }

  if (!slaBreaches || slaBreaches.length === 0) {
    return (
      <div className="card p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-600 shadow-md">
            <CheckCircle className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-green-900 dark:text-green-400">
              No Active SLA Breaches
            </h3>
            <p className="text-sm text-green-700 dark:text-green-300 mt-0.5">
              All tickets are within SLA thresholds
            </p>
          </div>
        </div>
      </div>
    );
  }

  const activeBreaches = slaBreaches.filter((b) => b.status === 'active').length;
  const acknowledgedBreaches = slaBreaches.filter((b) => b.status === 'acknowledged').length;

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="bg-red-50 dark:bg-red-900/20 px-6 py-4 border-b border-red-100 dark:border-red-900/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-600 shadow-md">
              <AlertTriangle className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">SLA Breaches</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {activeBreaches} active, {acknowledgedBreaches} acknowledged
              </p>
            </div>
          </div>
          <span className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-red-600 text-sm font-bold text-white shadow-md">
            {slaBreaches.length}
          </span>
        </div>
      </div>

      {/* Breaches List */}
      <div className="divide-y divide-slate-100 dark:divide-slate-700">
        {slaBreaches.map((breach) => (
          <div
            key={breach.id}
            className="group flex items-center justify-between px-6 py-4 transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/50"
          >
            <div className="flex items-start gap-3">
              <div
                className={cn(
                  'flex h-10 w-10 items-center justify-center rounded-lg shadow-md',
                  breach.status === 'active'
                    ? 'bg-red-600'
                    : 'bg-yellow-600'
                )}
              >
                {breach.status === 'active' ? (
                  <AlertCircle className="h-4 w-4 text-white" />
                ) : (
                  <Clock className="h-4 w-4 text-white" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-900 dark:text-white">
                    {breach.ticket_id}
                  </span>
                  <StatusBadge status={breach.status} />
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {breach.customer_name} • {breach.sla_type.replace('_', ' ')}
                </p>
                <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                  {formatTimeAgo(breach.breached_at)} • {formatDuration(breach.breach_duration_minutes)}
                </p>
              </div>
            </div>
            <button className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 dark:border-slate-600 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-300 transition-all hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-600 dark:hover:bg-indigo-900/20 dark:hover:text-indigo-400">
              {breach.status === 'active' ? 'Acknowledge' : 'View'}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: 'bg-red-600 text-white',
    acknowledged: 'bg-yellow-600 text-white',
    resolved: 'bg-green-600 text-white',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
        colors[status] || colors.active
      )}
    >
      {status}
    </span>
  );
}

function formatTimeAgo(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 60) {
    return `${diffMins}m ago`;
  }

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

function formatDuration(minutes: number) {
  if (minutes < 60) {
    return `${minutes}m`;
  }

  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
}

function SLASkeleton() {
  return (
    <div className="card p-6">
      <div className="flex items-center gap-3">
        <div className="h-12 w-12 skeleton rounded-lg" />
        <div className="space-y-2">
          <div className="h-4 w-32 skeleton" />
          <div className="h-3 w-24 skeleton" />
        </div>
      </div>
    </div>
  );
}
