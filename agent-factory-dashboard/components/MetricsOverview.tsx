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
  Activity,
} from 'lucide-react';

export function MetricsOverview() {
  const { metrics, loading } = useDashboard();

  if (loading || !metrics) {
    return <MetricsSkeleton />;
  }

  // Calculate SLA trend from history
  const calculateSlaTrend = () => {
    if (!metrics.metrics_history || metrics.metrics_history.length < 2) return { change: 0, trendUp: true, isOnTarget: true };
    
    const current = metrics.summary.sla_compliance_rate || 0;
    const previous = metrics.metrics_history[metrics.metrics_history.length - 2]?.sla_compliance_rate || current;
    const change = previous > 0 ? ((current - previous) / previous * 100).toFixed(1) : '0';
    
    return {
      change: Math.abs(parseFloat(change)),
      trendUp: current >= previous,
      isOnTarget: current >= 95,
    };
  };

  const slaTrend = calculateSlaTrend();

  // Safe access to summary values with defaults
  const summary = metrics.summary || {};
  const totalTickets = summary.total_tickets || 0;
  const openTickets = summary.open_tickets || 0;
  const avgResolution = summary.avg_resolution_time_hours || 0;
  const avgSatisfaction = summary.avg_satisfaction_rating || 0;
  const slaCompliance = summary.sla_compliance_rate || 0;
  const conversations24h = summary.total_conversations_24h || 0;

  const statCards = [
    {
      title: 'Total Tickets',
      value: totalTickets.toLocaleString(),
      trend: '+12.5%',
      trendLabel: 'vs last week',
      trendUp: true,
      icon: Ticket,
      iconBg: 'icon-circle-indigo',
    },
    {
      title: 'Open Tickets',
      value: openTickets.toString(),
      trend: '-3',
      trendLabel: 'vs yesterday',
      trendUp: true,
      icon: Users,
      iconBg: 'icon-circle-amber',
    },
    {
      title: 'Avg Resolution',
      value: `${avgResolution}h`,
      trend: '-15%',
      trendLabel: 'improvement',
      trendUp: true,
      icon: Clock,
      iconBg: 'icon-circle-blue',
    },
    {
      title: 'Satisfaction',
      value: avgSatisfaction.toFixed(1),
      trend: '+0.3',
      trendLabel: 'vs last week',
      trendUp: true,
      icon: CheckCircle,
      iconBg: 'icon-circle-purple',
    },
    {
      title: 'SLA Compliance',
      value: `${slaCompliance.toFixed(1)}%`,
      trend: slaTrend.isOnTarget ? `+${slaTrend.change}%` : `-${slaTrend.change}%`,
      trendLabel: slaTrend.isOnTarget ? 'vs last week' : 'needs attention',
      trendUp: slaTrend.trendUp && slaTrend.isOnTarget,
      icon: AlertTriangle,
      iconBg: slaTrend.isOnTarget ? 'icon-circle-indigo' : 'icon-circle-red',
      sparkline: metrics.metrics_history?.slice(-7).map((m: any) => m.sla_compliance_rate || 0) || [],
    },
    {
      title: 'Conversations (24h)',
      value: conversations24h.toLocaleString(),
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
            <div className="flex items-center gap-2 mb-3">
              <span className={`stat-change ${trendColor} text-sm font-medium`}>
                <TrendIcon className="w-4 h-4" />
                {stat.trend}
              </span>
              <span className="text-sm text-slate-500 dark:text-slate-400 font-medium">{stat.trendLabel}</span>
            </div>

            {/* Sparkline for SLA Compliance */}
            {stat.sparkline && stat.sparkline.length > 0 && (
              <div className="flex items-end gap-1 h-12 pt-3 border-t border-slate-100 dark:border-slate-700">
                {stat.sparkline.map((value: number, i: number) => {
                  const height = Math.max((value / 100) * 100, 10);
                  const isLast = i === stat.sparkline.length - 1;
                  const isGood = value >= 95;
                  
                  return (
                    <div
                      key={i}
                      className={`flex-1 rounded-t transition-all duration-300 ${
                        isGood 
                          ? 'bg-gradient-to-t from-green-500 to-emerald-400' 
                          : 'bg-gradient-to-t from-red-500 to-rose-400'
                      } ${isLast ? 'opacity-100 shadow-lg' : 'opacity-70 hover:opacity-100'}`}
                      style={{ height: `${height}%` }}
                      title={`${value.toFixed(1)}%`}
                    />
                  );
                })}
              </div>
            )}
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
