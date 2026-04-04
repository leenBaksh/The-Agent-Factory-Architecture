'use client';

import React, { useState } from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { 
  Activity, 
  Zap, 
  AlertCircle, 
  CheckCircle, 
  Server, 
  ArrowRight, 
  TrendingUp, 
  Clock,
  Users,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export function FTEInstancesPanel() {
  const { fteInstances, loading } = useDashboard();
  const [expandedFte, setExpandedFte] = useState<string | null>(null);

  if (loading) {
    return <FTESkeleton />;
  }

  // Mock demo data for demonstration
  const mockData = [
    {
      id: 'cs-fte-001',
      name: 'Customer Success FTE',
      type: 'customer-success',
      status: 'running' as const,
      version: '1.0.0',
      uptime_seconds: 86400,
      last_health_check: new Date().toISOString(),
      metrics: {
        messages_per_minute: 12.5,
        avg_latency_ms: 245,
        error_rate: 0.02,
        active_conversations: 8,
      },
    },
    {
      id: 'sales-fte-001',
      name: 'Sales Support FTE',
      type: 'sales',
      status: 'running' as const,
      version: '1.2.0',
      uptime_seconds: 172800,
      last_health_check: new Date().toISOString(),
      metrics: {
        messages_per_minute: 8.3,
        avg_latency_ms: 180,
        error_rate: 0.01,
        active_conversations: 5,
      },
    },
    {
      id: 'tech-fte-001',
      name: 'Technical Support FTE',
      type: 'technical-support',
      status: 'running' as const,
      version: '0.9.5',
      uptime_seconds: 43200,
      last_health_check: new Date().toISOString(),
      metrics: {
        messages_per_minute: 15.7,
        avg_latency_ms: 320,
        error_rate: 0.08,
        active_conversations: 12,
      },
    },
  ];

  // Ensure fteInstances is an array and normalize data with defaults
  const instances = (Array.isArray(fteInstances) && fteInstances.length > 0 ? fteInstances : mockData).map((fte) => ({
    ...fte,
    status: fte.status ?? 'running',
    version: fte.version ?? '1.0.0',
    uptime_seconds: fte.uptime_seconds ?? 0,
    last_health_check: fte.last_health_check ?? new Date().toISOString(),
    metrics: {
      messages_per_minute: fte.metrics?.messages_per_minute ?? 0,
      avg_latency_ms: fte.metrics?.avg_latency_ms ?? 0,
      error_rate: fte.metrics?.error_rate ?? 0,
      active_conversations: fte.metrics?.active_conversations ?? 0,
    },
  }));

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
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      {/* Header - Gradient */}
      <div className="relative overflow-hidden bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 px-6 py-5">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm shadow-lg">
              <Server className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">FTE Instances</h3>
              <p className="text-xs text-white/80 mt-0.5">
                {instances.length} active instance{instances.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-full bg-white/20 backdrop-blur-sm px-3 py-1.5">
              <div className="h-2 w-2 rounded-full bg-green-400 animate-pulse"></div>
              <span className="text-xs font-semibold text-white">All Systems Operational</span>
            </div>
          </div>
        </div>
      </div>

      {/* Instances List */}
      <div className="divide-y divide-slate-100 dark:divide-slate-700">
        {instances.map((fte, index) => (
          <div
            key={fte.id}
            className="group transition-all hover:bg-gradient-to-r hover:from-indigo-50/50 hover:via-purple-50/30 hover:to-transparent dark:hover:bg-slate-700/30"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="px-6 py-4">
              <div className="flex items-start justify-between">
                {/* Left Side - FTE Info */}
                <div className="flex items-start gap-4 flex-1">
                  <StatusIndicator status={fte.status} />
                  <div className="flex-1">
                    <div className="flex items-center gap-2.5">
                      <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                        {fte.name}
                      </h4>
                      <span className="inline-flex items-center rounded-md bg-gradient-to-r from-indigo-500 to-purple-500 px-2 py-0.5 text-[10px] font-bold text-white shadow-sm">
                        v{fte.version}
                      </span>
                      <span className="inline-flex items-center rounded-md bg-slate-100 dark:bg-slate-700 px-2 py-0.5 text-[10px] font-medium text-slate-600 dark:text-slate-300 capitalize">
                        {fte.type.replace(/-/g, ' ')}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 flex items-center gap-2">
                      <Clock className="w-3 h-3" />
                      Uptime: <span className="font-medium text-slate-700 dark:text-slate-300">{formatUptime(fte.uptime_seconds)}</span>
                    </p>

                    {/* Metrics Grid */}
                    <div className="mt-3 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
                      <MetricBadge
                        icon={Zap}
                        value={fte.metrics.messages_per_minute.toFixed(1)}
                        label="msg/min"
                        color="indigo"
                      />
                      <MetricBadge
                        icon={Activity}
                        value={`${Math.round(fte.metrics.avg_latency_ms)}`}
                        label="latency"
                        suffix="ms"
                        color={
                          fte.metrics.avg_latency_ms > 300 ? 'red' : 
                          fte.metrics.avg_latency_ms > 200 ? 'yellow' : 'green'
                        }
                      />
                      <MetricBadge
                        icon={AlertCircle}
                        value={`${(fte.metrics.error_rate * 100).toFixed(1)}`}
                        label="errors"
                        suffix="%"
                        color={
                          fte.metrics.error_rate > 0.05 ? 'red' : 
                          fte.metrics.error_rate > 0.02 ? 'yellow' : 'green'
                        }
                      />
                      <MetricBadge
                        icon={Users}
                        value={fte.metrics.active_conversations.toString()}
                        label="active"
                        color="purple"
                      />
                    </div>
                  </div>
                </div>

                {/* Right Side - Actions */}
                <div className="flex flex-col items-end gap-2">
                  <div className="flex items-center gap-2">
                    <div className="flex h-2.5 w-2.5 items-center justify-center relative">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
                      <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 shadow-lg" />
                    </div>
                    <span className="text-xs font-medium text-slate-600 dark:text-slate-400">Live</span>
                  </div>
                  
                  <button
                    onClick={() => setExpandedFte(expandedFte === fte.id ? null : fte.id)}
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors"
                  >
                    {expandedFte === fte.id ? (
                      <>
                        Hide Details
                        <ChevronUp className="w-3.5 h-3.5" />
                      </>
                    ) : (
                      <>
                        View Details
                        <ChevronDown className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                  
                  <button className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-500 px-3 py-1.5 text-xs font-semibold text-white shadow-md hover:shadow-lg transition-all">
                    <ExternalLink className="w-3.5 h-3.5" />
                    Dashboard
                  </button>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedFte === fte.id && (
                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700 animate-in slide-in-from-top-2 duration-200">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <DetailCard
                      icon={TrendingUp}
                      label="Messages (24h)"
                      value={(fte.metrics.messages_per_minute * 1440).toFixed(0)}
                      trend="+12.5%"
                      trendUp={true}
                      iconColor="indigo"
                    />
                    <DetailCard
                      icon={Clock}
                      label="Avg Response"
                      value={`${Math.round(fte.metrics.avg_latency_ms)}ms`}
                      trend="-8.2%"
                      trendUp={true}
                      iconColor="green"
                    />
                    <DetailCard
                      icon={CheckCircle}
                      label="Success Rate"
                      value={`${((1 - fte.metrics.error_rate) * 100).toFixed(1)}%`}
                      trend="+0.3%"
                      trendUp={true}
                      iconColor="green"
                    />
                    <DetailCard
                      icon={BarChart3}
                      label="Peak Load"
                      value={`${(fte.metrics.messages_per_minute * 1.5).toFixed(1)} msg/min`}
                      trend="2:00 PM"
                      trendUp={undefined}
                      iconColor="purple"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusIndicator({ status }: { status: string }) {
  const configs: Record<string, { icon: React.ReactNode; gradient: string; shadow: string }> = {
    running: {
      icon: <CheckCircle className="h-5 w-5" />,
      gradient: 'from-green-500 to-emerald-600',
      shadow: 'shadow-green-500/30',
    },
    stopped: {
      icon: <AlertCircle className="h-5 w-5" />,
      gradient: 'from-slate-400 to-slate-500',
      shadow: 'shadow-slate-400/30',
    },
    error: {
      icon: <AlertCircle className="h-5 w-5" />,
      gradient: 'from-red-500 to-rose-600',
      shadow: 'shadow-red-500/30',
    },
    scaling: {
      icon: <Server className="h-5 w-5" />,
      gradient: 'from-indigo-500 to-purple-600',
      shadow: 'shadow-indigo-500/30',
    },
  };

  const config = configs[status] || configs.stopped;

  return (
    <div className={cn(
      'flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br shadow-lg',
      config.gradient,
      config.shadow
    )}>
      {config.icon}
    </div>
  );
}

function MetricBadge({
  icon,
  value,
  label,
  suffix,
  color = 'indigo',
}: {
  icon: React.ElementType;
  value: string;
  label: string;
  suffix?: string;
  color?: 'indigo' | 'green' | 'yellow' | 'red' | 'purple' | 'blue';
}) {
  const Icon = icon;
  
  const colorClasses = {
    indigo: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
    green: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    yellow: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    red: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    purple: 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    blue: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  };

  const iconColorClasses = {
    indigo: 'text-indigo-600 dark:text-indigo-400',
    green: 'text-green-600 dark:text-green-400',
    yellow: 'text-yellow-600 dark:text-yellow-400',
    red: 'text-red-600 dark:text-red-400',
    purple: 'text-purple-600 dark:text-purple-400',
    blue: 'text-blue-600 dark:text-blue-400',
  };

  return (
    <div className={cn(
      'flex items-center gap-2 rounded-lg px-2.5 py-2 transition-colors',
      colorClasses[color]
    )}>
      <Icon className={cn('h-4 w-4 flex-shrink-0', iconColorClasses[color])} />
      <div className="flex items-baseline gap-0.5">
        <span className="text-sm font-bold">{value}</span>
        <span className="text-[10px] font-medium opacity-70">{label}</span>
        {suffix && <span className="text-[10px] font-medium opacity-70">{suffix}</span>}
      </div>
    </div>
  );
}

function DetailCard({
  icon,
  label,
  value,
  trend,
  trendUp,
  iconColor = 'indigo',
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  trend?: string;
  trendUp?: boolean;
  iconColor?: string;
}) {
  const Icon = icon;
  
  const iconColors: Record<string, string> = {
    indigo: 'bg-indigo-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
    purple: 'bg-purple-500',
    blue: 'bg-blue-500',
  };

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 transition-all hover:shadow-md">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</span>
        <div className={cn('flex h-8 w-8 items-center justify-center rounded-lg', iconColors[iconColor])}>
          <Icon className="h-4 w-4 text-white" />
        </div>
      </div>
      <div className="flex items-end justify-between">
        <span className="text-lg font-bold text-slate-900 dark:text-white">{value}</span>
        {trend && (
          <span className={cn(
            'text-xs font-semibold',
            trendUp === true ? 'text-green-600 dark:text-green-400' :
            trendUp === false ? 'text-red-600 dark:text-red-400' :
            'text-slate-500 dark:text-slate-400'
          )}>
            {trend}
          </span>
        )}
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
            <div className="h-12 w-12 skeleton rounded-xl" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-36 skeleton" />
              <div className="h-2.5 w-28 skeleton" />
              <div className="flex gap-2">
                <div className="h-8 w-20 skeleton rounded-lg" />
                <div className="h-8 w-20 skeleton rounded-lg" />
                <div className="h-8 w-20 skeleton rounded-lg" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
