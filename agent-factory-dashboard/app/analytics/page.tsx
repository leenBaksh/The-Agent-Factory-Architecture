'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import { useDashboard } from '@/contexts/DashboardContext';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  Ticket,
  MessageSquare,
  Clock,
  Smile,
  AlertCircle,
  Download,
  Calendar,
  Filter,
  X,
  CheckCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function AnalyticsPage() {
  const { metrics, loading } = useDashboard();
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('7d');
  const [selectedChannel, setSelectedChannel] = useState<string>('all');
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [exportStatus, setExportStatus] = useState<'idle' | 'exporting' | 'done'>('idle');

  // Mock historical data for charts
  const mockDailyData = [
    { date: '2026-04-01', tickets: 45, resolved: 40, avgResponse: 5.2, satisfaction: 4.5 },
    { date: '2026-04-02', tickets: 52, resolved: 48, avgResponse: 4.8, satisfaction: 4.6 },
    { date: '2026-04-03', tickets: 38, resolved: 35, avgResponse: 6.1, satisfaction: 4.3 },
    { date: '2026-04-04', tickets: 61, resolved: 55, avgResponse: 4.2, satisfaction: 4.7 },
    { date: '2026-04-05', tickets: 48, resolved: 44, avgResponse: 5.5, satisfaction: 4.4 },
    { date: '2026-04-06', tickets: 55, resolved: 50, avgResponse: 4.9, satisfaction: 4.6 },
    { date: '2026-04-07', tickets: 42, resolved: 38, avgResponse: 5.8, satisfaction: 4.5 },
  ];

  const mockChannelData = [
    { channel: 'Web', tickets: 145, resolved: 132, avgTime: 4.2, satisfaction: 4.6 },
    { channel: 'Gmail', tickets: 98, resolved: 85, avgTime: 5.8, satisfaction: 4.4 },
    { channel: 'WhatsApp', tickets: 44, resolved: 40, avgTime: 2.1, satisfaction: 4.8 },
  ];

  const mockHourlyDistribution = [
    { hour: '00:00', volume: 5 },
    { hour: '02:00', volume: 3 },
    { hour: '04:00', volume: 2 },
    { hour: '06:00', volume: 8 },
    { hour: '08:00', volume: 25 },
    { hour: '10:00', volume: 42 },
    { hour: '12:00', volume: 38 },
    { hour: '14:00', volume: 45 },
    { hour: '16:00', volume: 35 },
    { hour: '18:00', volume: 22 },
    { hour: '20:00', volume: 15 },
    { hour: '22:00', volume: 8 },
  ];

  const mockTopIssues = [
    { issue: 'Login/Authentication Issues', count: 45, trend: 12 },
    { issue: 'Billing Questions', count: 38, trend: -5 },
    { issue: 'Feature Requests', count: 32, trend: 8 },
    { issue: 'Bug Reports', count: 28, trend: -15 },
    { issue: 'Account Setup', count: 25, trend: 3 },
  ];

  const mockAgentPerformance = [
    { agent: 'Agent AI-1', tickets: 156, avgResponse: 3.2, satisfaction: 4.8, resolution: 92 },
    { agent: 'Agent AI-2', tickets: 142, avgResponse: 4.1, satisfaction: 4.6, resolution: 88 },
    { agent: 'Agent AI-3', tickets: 128, avgResponse: 3.8, satisfaction: 4.7, resolution: 90 },
  ];

  if (loading) {
    return (
      <>
        <Header title="Analytics" />
        <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
          <div className="mx-auto max-w-7xl">
            <div className="animate-pulse space-y-6">
              <div className="h-10 w-full bg-zinc-200 dark:bg-zinc-800 rounded-lg" />
              <div className="grid gap-6 md:grid-cols-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-32 bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
                ))}
              </div>
              <div className="h-80 bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
            </div>
          </div>
        </main>
      </>
    );
  }

  const summary = metrics?.summary;

  // Calculate trends (mock)
  const getTrendIcon = (value: number) => {
    if (value > 0) return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (value < 0) return <TrendingDown className="h-4 w-4 text-red-600" />;
    return null;
  };

  return (
    <>
      <Header title="Analytics" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Header Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                <BarChart3 className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Advanced Analytics
                </h2>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  Performance insights and reporting
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 rounded-lg border border-zinc-200 bg-white p-1 dark:border-zinc-700 dark:bg-zinc-900">
                {(['7d', '30d', '90d'] as const).map((range) => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    className={cn(
                      'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
                      timeRange === range
                        ? 'bg-indigo-600 text-white'
                        : 'text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800'
                    )}
                  >
                    {range}
                  </button>
                ))}
              </div>
              <button 
                onClick={() => setShowFilterModal(true)}
                className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
              >
                <Filter className="h-4 w-4" />
                Filter
              </button>
              <button 
                onClick={() => {
                  setExportStatus('exporting');
                  setTimeout(() => {
                    setExportStatus('done');
                    setTimeout(() => setExportStatus('idle'), 2000);
                  }, 1500);
                }}
                disabled={exportStatus === 'exporting'}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {exportStatus === 'exporting' ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Exporting...
                  </>
                ) : exportStatus === 'done' ? (
                  <>
                    <CheckCircle className="h-4 w-4" />
                    Exported!
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Export
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              icon={Ticket}
              label="Total Tickets"
              value={summary?.total_tickets.toLocaleString() ?? '0'}
              trend={12.5}
              trendLabel="vs last period"
            />
            <MetricCard
              icon={MessageSquare}
              label="Conversations (24h)"
              value={summary?.total_conversations_24h.toLocaleString() ?? '0'}
              trend={8.2}
              trendLabel="vs yesterday"
            />
            <MetricCard
              icon={Clock}
              label="Avg Resolution"
              value={`${summary?.avg_resolution_time_hours.toFixed(1) ?? '0'}h`}
              trend={-5.3}
              trendLabel="improvement"
              trendPositive={false}
            />
            <MetricCard
              icon={Smile}
              label="Satisfaction"
              value={`${(summary?.avg_satisfaction_rating ?? 0).toFixed(1)}/5.0`}
              trend={3.1}
              trendLabel="vs last period"
            />
          </div>

          {/* Charts Row 1 */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Daily Ticket Volume */}
            <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  Daily Ticket Volume
                </h3>
                <Calendar className="h-5 w-5 text-zinc-400" />
              </div>
              <div className="h-64">
                <BarChart data={mockDailyData} dataKey="tickets" color="#6366f1" />
              </div>
            </div>

            {/* Resolution Rate */}
            <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  Daily Resolution Rate
                </h3>
                <TrendingUp className="h-5 w-5 text-zinc-400" />
              </div>
              <div className="h-64">
                <BarChart data={mockDailyData} dataKey="resolved" color="#22c55e" />
              </div>
            </div>
          </div>

          {/* Charts Row 2 */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Channel Distribution */}
            <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  By Channel
                </h3>
                <MessageSquare className="h-5 w-5 text-zinc-400" />
              </div>
              <div className="space-y-4">
                {mockChannelData.map((channel) => (
                  <div key={channel.channel} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-zinc-700 dark:text-zinc-300">
                        {channel.channel}
                      </span>
                      <span className="text-zinc-500">{channel.tickets} tickets</span>
                    </div>
                    <div className="h-2 rounded-full bg-zinc-100 dark:bg-zinc-800">
                      <div
                        className={cn(
                          'h-full rounded-full transition-all',
                          channel.channel === 'Web' ? 'bg-indigo-600' :
                          channel.channel === 'Gmail' ? 'bg-red-600' : 'bg-green-600'
                        )}
                        style={{ width: `${(channel.tickets / 145) * 100}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-xs text-zinc-500">
                      <span>Avg: {channel.avgTime}h</span>
                      <span>CSAT: {channel.satisfaction}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Hourly Distribution */}
            <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  Hourly Distribution
                </h3>
                <Clock className="h-5 w-5 text-zinc-400" />
              </div>
              <div className="h-48 flex items-end gap-1">
                {mockHourlyDistribution.map((item) => {
                  const isPeak = item.volume >= 40;
                  const isLow = item.volume <= 5;
                  return (
                    <div key={item.hour} className="flex-1 flex flex-col items-center gap-1 group relative">
                      {/* Tooltip */}
                      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 dark:bg-slate-700 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                        {item.hour.slice(0, 5)}: {item.volume} tickets
                      </div>
                      <div
                        className={cn(
                          'w-full rounded-t transition-all hover:opacity-80',
                          isPeak ? 'bg-gradient-to-t from-red-500 to-orange-400' :
                          isLow ? 'bg-slate-300 dark:bg-slate-600' :
                          'bg-gradient-to-t from-indigo-500 to-indigo-400'
                        )}
                        style={{ height: `${(item.volume / 45) * 100}%` }}
                      />
                      <span className="text-[10px] text-zinc-500 rotate-45 origin-left">
                        {item.hour.slice(0, 5)}
                      </span>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 flex items-center justify-between text-xs text-zinc-500">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-gradient-to-t from-indigo-500 to-indigo-400" />
                    <span>Normal</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-gradient-to-t from-red-500 to-orange-400" />
                    <span>Peak (≥40)</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-3 h-3 rounded bg-slate-300 dark:bg-slate-600" />
                    <span>Low (≤5)</span>
                  </div>
                </div>
                <span className="text-xs text-zinc-400">
                  Peak: 14:00 (45 tickets)
                </span>
              </div>
            </div>

            {/* SLA Compliance */}
            <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  SLA Compliance
                </h3>
                <AlertCircle className="h-5 w-5 text-zinc-400" />
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-600 dark:text-zinc-400">Compliance Rate</span>
                  <span className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                    {summary?.sla_compliance_rate.toFixed(1) ?? '0'}%
                  </span>
                </div>
                <div className="h-3 rounded-full bg-zinc-100 dark:bg-zinc-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-green-500 to-emerald-600 transition-all"
                    style={{ width: `${summary?.sla_compliance_rate ?? 0}%` }}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4">
                  <div className="rounded-lg bg-green-50 p-3 dark:bg-green-900/20">
                    <p className="text-xs text-green-600 dark:text-green-400">On Track</p>
                    <p className="text-lg font-semibold text-green-700 dark:text-green-300">
                      {Math.round((summary?.total_tickets ?? 0) * 0.85)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-red-50 p-3 dark:bg-red-900/20">
                    <p className="text-xs text-red-600 dark:text-red-400">At Risk</p>
                    <p className="text-lg font-semibold text-red-700 dark:text-red-300">
                      {Math.round((summary?.total_tickets ?? 0) * 0.15)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Top Issues */}
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                Top Issues This Period
              </h3>
              <TrendingUp className="h-5 w-5 text-zinc-400" />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-zinc-200 dark:border-zinc-700">
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Issue Category
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Count
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Trend
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                      % of Total
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
                  {mockTopIssues.map((item, index) => (
                    <tr key={index} className="hover:bg-zinc-50 dark:hover:bg-zinc-800">
                      <td className="px-4 py-3 text-sm font-medium text-zinc-900 dark:text-zinc-100">
                        {item.issue}
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-zinc-600 dark:text-zinc-400">
                        {item.count.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          {getTrendIcon(item.trend)}
                          <span className={cn(
                            'text-sm font-medium',
                            item.trend > 0 ? 'text-red-600' : 'text-green-600'
                          )}>
                            {Math.abs(item.trend)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-zinc-600 dark:text-zinc-400">
                        {((item.count / 168) * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Agent Performance */}
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                Agent Performance
              </h3>
              <Users className="h-5 w-5 text-zinc-400" />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-zinc-200 dark:border-zinc-700">
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Agent
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Tickets Handled
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Avg Response (min)
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Satisfaction
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Resolution Rate
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
                  {mockAgentPerformance.map((agent, index) => (
                    <tr key={index} className="hover:bg-zinc-50 dark:hover:bg-zinc-800">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 dark:bg-indigo-900">
                            <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                              {index + 1}
                            </span>
                          </div>
                          <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                            {agent.agent}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-zinc-600 dark:text-zinc-400">
                        {agent.tickets.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-zinc-600 dark:text-zinc-400">
                        {agent.avgResponse}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Smile className="h-4 w-4 text-amber-500" />
                          <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                            {agent.satisfaction}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <div className="h-2 w-20 rounded-full bg-zinc-100 dark:bg-zinc-800">
                            <div
                              className="h-full rounded-full bg-green-500"
                              style={{ width: `${agent.resolution}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                            {agent.resolution}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>

      {/* Filter Modal */}
      {showFilterModal && (
        <FilterModal onClose={() => setShowFilterModal(false)} />
      )}
    </>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  trend,
  trendLabel,
  trendPositive = true,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  trend?: number;
  trendLabel?: string;
  trendPositive?: boolean;
}) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100 dark:bg-indigo-900">
          <Icon className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        {trend !== undefined && (
          <div className={cn(
            'flex items-center gap-1 text-sm font-medium',
            (trend > 0) === trendPositive ? 'text-green-600' : 'text-red-600'
          )}>
            {trend > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">{value}</p>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{label}</p>
        {trendLabel && (
          <p className="mt-1 text-xs text-zinc-400 dark:text-zinc-500">{trendLabel}</p>
        )}
      </div>
    </div>
  );
}

// Simple bar chart component
function BarChart({
  data,
  dataKey,
  color,
}: {
  data: Record<string, number | string>[];
  dataKey: string;
  color: string;
}) {
  const maxValue = Math.max(...data.map((d) => d[dataKey] as number));

  return (
    <div className="flex h-full items-end gap-2">
      {data.map((item, index) => (
        <div key={index} className="flex-1 flex flex-col items-center gap-1">
          <div
            className="w-full rounded-t transition-all hover:opacity-80"
            style={{
              height: `${((item[dataKey] as number) / maxValue) * 100}%`,
              backgroundColor: color,
              minHeight: '4px',
            }}
          />
          <span className="text-[10px] text-zinc-500">
            {new Date(item.date as string).toLocaleDateString('en-US', { weekday: 'short' })}
          </span>
        </div>
      ))}
    </div>
  );
}

function FilterModal({ onClose }: { onClose: () => void }) {
  const [filters, setFilters] = useState({
    channel: 'all',
    status: 'all',
    priority: 'all',
    dateFrom: '',
    dateTo: '',
  });

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
          <X className="w-5 h-5" />
        </button>
        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Filter Analytics</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Channel</label>
            <select
              value={filters.channel}
              onChange={(e) => setFilters({...filters, channel: e.target.value})}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              <option value="all">All Channels</option>
              <option value="web">Web</option>
              <option value="gmail">Gmail</option>
              <option value="whatsapp">WhatsApp</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Priority</label>
            <select
              value={filters.priority}
              onChange={(e) => setFilters({...filters, priority: e.target.value})}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              <option value="all">All Priorities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">From Date</label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => setFilters({...filters, dateFrom: e.target.value})}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">To Date</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => setFilters({...filters, dateTo: e.target.value})}
                className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-3 pt-4">
            <button onClick={onClose} className="flex-1 py-2.5 px-4 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700">
              Cancel
            </button>
            <button onClick={onClose} className="flex-1 py-2.5 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700">
              Apply Filters
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
