'use client';

import React from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { Activity, Zap, AlertCircle, CheckCircle, Server, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export function FTEInstancesPanel() {
  const { fteInstances, loading } = useDashboard();

  if (loading) {
    return <FTESkeleton />;
  }

  // Ensure fteInstances is an array
  const instances = Array.isArray(fteInstances) ? fteInstances : [];

  if (!instances || instances.length === 0) {
    return (
      <div className="card p-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-700">
          <Server className="h-6 w-6 text-slate-400" />
        </div>
        <h3 className="text-base font-semibold text-slate-900 dark:text-white">No FTE Instances</h3>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          No Digital FTE instances are currently configured
        </p>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          FTEs will appear here once deployed
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="bg-indigo-50 dark:bg-indigo-900/20 px-6 py-4 border-b border-indigo-100 dark:border-indigo-900/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 shadow-md">
              <Server className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">FTE Instances</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {instances.length} active instance{instances.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Instances List */}
      <div className="divide-y divide-slate-100 dark:divide-slate-700">
        {instances.map((fte) => (
          <div
            key={fte.id}
            className="group px-6 py-4 transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/50"
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <StatusIndicator status={fte.status} />
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-medium text-slate-900 dark:text-white">
                      {fte.name}
                    </h4>
                    <span className="rounded-md bg-indigo-600 px-2 py-0.5 text-[10px] font-semibold text-white">
                      v{fte.version}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    {fte.type} • <span className="font-medium text-slate-600 dark:text-slate-300">{formatUptime(fte.uptime_seconds)}</span>
                  </p>

                  {/* Metrics */}
                  <div className="mt-3 flex items-center gap-2">
                    <MetricItem
                      icon={Zap}
                      value={fte.metrics.messages_per_minute.toFixed(1)}
                      label="msg/min"
                    />
                    <MetricItem
                      icon={Activity}
                      value={`${Math.round(fte.metrics.avg_latency_ms)}ms`}
                      label="latency"
                    />
                    <MetricItem
                      icon={AlertCircle}
                      value={`${(fte.metrics.error_rate * 100).toFixed(1)}%`}
                      label="errors"
                      valueColor={
                        fte.metrics.error_rate > 0.05 ? 'text-red-600 dark:text-red-400' : 'text-slate-500 dark:text-slate-400'
                      }
                    />
                  </div>
                </div>
              </div>

              {/* Active Conversations */}
              <div className="text-right">
                <div className="flex items-center justify-end gap-2">
                  <div className="flex h-2.5 w-2.5 items-center justify-center">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-green-500" />
                  </div>
                  <div className="text-base font-semibold text-slate-900 dark:text-white">
                    {fte.metrics.active_conversations}
                  </div>
                </div>
                <div className="text-[10px] font-medium text-slate-500 dark:text-slate-400 mt-0.5">
                  conversations
                </div>
                <button className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-700 transition-colors dark:text-indigo-400 dark:hover:text-indigo-300">
                  Details
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusIndicator({ status }: { status: string }) {
  const configs: Record<string, { icon: React.ReactNode; color: string }> = {
    running: {
      icon: <CheckCircle className="h-4 w-4" />,
      color: 'bg-green-600',
    },
    stopped: {
      icon: <AlertCircle className="h-4 w-4" />,
      color: 'bg-slate-400',
    },
    error: {
      icon: <AlertCircle className="h-4 w-4" />,
      color: 'bg-red-600',
    },
    scaling: {
      icon: <Server className="h-4 w-4" />,
      color: 'bg-indigo-600',
    },
  };

  const config = configs[status] || configs.stopped;

  return (
    <div className={cn(
      'flex h-10 w-10 items-center justify-center rounded-lg shadow-md',
      config.color
    )}>
      {config.icon}
    </div>
  );
}

function MetricItem({
  icon,
  value,
  label,
  valueColor = 'text-slate-600',
}: {
  icon: React.ElementType;
  value: string;
  label: string;
  valueColor?: string;
}) {
  const Icon = icon;
  return (
    <div className="flex items-center gap-1.5 rounded-md bg-slate-50 dark:bg-slate-700 px-2 py-1.5">
      <Icon className="h-3.5 w-3.5 text-slate-400" />
      <div>
        <span className={cn('text-xs font-semibold', valueColor)}>{value}</span>
        <span className="text-[10px] text-slate-400 dark:text-slate-500 ml-0.5">{label}</span>
      </div>
    </div>
  );
}

function formatUptime(seconds: number) {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);

  if (days > 0) {
    return `${days}d ${hours}h`;
  }

  const mins = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${mins}m`;
  }

  return `${mins}m`;
}

function FTESkeleton() {
  return (
    <div className="card p-6">
      <div className="mb-4 h-5 w-28 skeleton" />
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex gap-3">
            <div className="h-10 w-10 skeleton rounded-lg" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-36 skeleton" />
              <div className="h-2.5 w-28 skeleton" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
