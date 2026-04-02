'use client';

import React from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import {
  Ticket,
  TrendingUp,
  Users,
  Clock,
  CheckCircle,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';

export function MetricsOverview() {
  const { metrics, loading } = useDashboard();

  if (loading || !metrics) {
    return <MetricsSkeleton />;
  }

  const statCards = [
    {
      title: 'Total Tickets',
      value: metrics.summary.total_tickets.toLocaleString(),
      trend: '+12.5%',
      trendLabel: 'vs last week',
      trendUp: true,
      icon: Ticket,
      iconBg: 'icon-circle-indigo',
    },
    {
      title: 'Open Tickets',
      value: metrics.summary.open_tickets.toString(),
      trend: '-3',
      trendLabel: 'vs yesterday',
      trendUp: true,
      icon: Users,
      iconBg: 'icon-circle-amber',
    },
    {
      title: 'Avg Resolution',
      value: `${metrics.summary.avg_resolution_time_hours}h`,
      trend: '-15%',
      trendLabel: 'improvement',
      trendUp: true,
      icon: Clock,
      iconBg: 'icon-circle-green',
    },
    {
      title: 'Satisfaction',
      value: metrics.summary.avg_satisfaction_rating.toFixed(1),
      trend: '+0.3',
      trendLabel: 'vs last week',
      trendUp: true,
      icon: CheckCircle,
      iconBg: 'icon-circle-purple',
    },
    {
      title: 'SLA Compliance',
      value: `${metrics.summary.sla_compliance_rate}%`,
      trend: metrics.summary.sla_compliance_rate >= 95 ? 'On target' : 'Below target',
      trendLabel: 'target: 95%',
      trendUp: metrics.summary.sla_compliance_rate >= 95,
      icon: AlertTriangle,
      iconBg: metrics.summary.sla_compliance_rate >= 95 ? 'icon-circle-green' : 'icon-circle-red',
    },
    {
      title: 'Conversations (24h)',
      value: metrics.summary.total_conversations_24h.toLocaleString(),
      trend: '+8%',
      trendLabel: 'vs yesterday',
      trendUp: true,
      icon: TrendingUp,
      iconBg: 'icon-circle-blue',
    },
  ];

  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        const TrendIcon = stat.trendUp ? ArrowUpRight : ArrowDownRight;
        const trendColor = stat.trendUp ? 'stat-change-up' : 'stat-change-down';

        return (
          <div
            key={stat.title}
            className="stat-card animate-slide-up"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <span className="stat-label text-slate-600 dark:text-slate-300 font-medium">{stat.title}</span>
              <div className={`icon-circle ${stat.iconBg}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>

            {/* Value */}
            <div className="mb-3">
              <p className="stat-value text-slate-900 dark:text-white text-3xl font-bold">{stat.value}</p>
            </div>

            {/* Trend */}
            <div className="flex items-center gap-2">
              <span className={`stat-change ${trendColor} text-sm font-medium`}>
                <TrendIcon className="w-4 h-4" />
                {stat.trend}
              </span>
              <span className="text-sm text-slate-500 dark:text-slate-400 font-medium">{stat.trendLabel}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function MetricsSkeleton() {
  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-slate-200 bg-white p-6 dark:bg-slate-800 dark:border-slate-700"
        >
          <div className="flex items-start justify-between">
            <div className="space-y-3">
              <div className="h-3 w-20 skeleton" />
              <div className="h-8 w-16 skeleton" />
              <div className="h-2.5 w-28 skeleton" />
            </div>
            <div className="h-10 w-10 skeleton rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  );
}
