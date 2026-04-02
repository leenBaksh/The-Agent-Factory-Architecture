'use client';

import React from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from 'recharts';
import { TrendingUp, MessageSquare, Activity, PieChart as PieChartIcon } from 'lucide-react';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export function ChartsSection() {
  const { metrics, loading } = useDashboard();

  if (loading || !metrics) {
    return <ChartsSkeleton />;
  }

  const statusData = Object.entries(metrics.tickets_by_status).map(([name, value]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    value,
  }));

  const channelData = Object.entries(metrics.tickets_by_channel).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const conversationData = metrics.metrics_history.map((m) => ({
    date: m.date,
    Conversations: m.total_conversations,
    Tickets: m.total_tickets,
  }));

  const performanceData = metrics.metrics_history.map((m) => ({
    date: m.date,
    'Resolution Time': Math.round(m.avg_resolution_time_minutes),
    'First Response': Math.round(m.avg_first_response_time_minutes),
  }));

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Conversations Trend - Area Chart */}
      <div className="chart-card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="chart-title text-slate-900 dark:text-white text-lg font-bold">Conversations Trend</h3>
            <p className="chart-subtitle text-slate-500 dark:text-slate-400 text-sm font-medium mt-0.5">Volume over last 7 days</p>
          </div>
          <div className="icon-circle icon-circle-indigo">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>

        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={conversationData}>
            <defs>
              <linearGradient id="colorConversations" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                padding: '12px 16px',
                fontSize: '13px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '16px' }} />
            <Area
              type="monotone"
              dataKey="Conversations"
              stroke="#6366f1"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorConversations)"
            />
            <Area
              type="monotone"
              dataKey="Tickets"
              stroke="#10b981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorConversations)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Performance Metrics - Line Chart */}
      <div className="chart-card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="chart-title text-slate-900 dark:text-white text-lg font-bold">Performance Metrics</h3>
            <p className="chart-subtitle text-slate-500 dark:text-slate-400 text-sm font-medium mt-0.5">Response times in minutes</p>
          </div>
          <div className="icon-circle icon-circle-green">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                padding: '12px 16px',
                fontSize: '13px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '16px' }} />
            <Line
              type="monotone"
              dataKey="Resolution Time"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="First Response"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Tickets by Status - Donut Chart */}
      <div className="chart-card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="chart-title text-slate-900 dark:text-white text-lg font-bold">Tickets by Status</h3>
            <p className="chart-subtitle text-slate-500 dark:text-slate-400 text-sm font-medium mt-0.5">Current distribution</p>
          </div>
          <div className="icon-circle icon-circle-purple">
            <PieChartIcon className="w-5 h-5" />
          </div>
        </div>

        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={statusData}
              cx="50%"
              cy="50%"
              innerRadius={80}
              outerRadius={110}
              paddingAngle={2}
              dataKey="value"
              strokeWidth={2}
              stroke="#fff"
            >
              {statusData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                padding: '12px 16px',
                fontSize: '13px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '16px' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Tickets by Channel - Bar Chart */}
      <div className="chart-card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="chart-title text-slate-900 dark:text-white text-lg font-bold">Tickets by Channel</h3>
            <p className="chart-subtitle text-slate-500 dark:text-slate-400 text-sm font-medium mt-0.5">Volume by source</p>
          </div>
          <div className="icon-circle icon-circle-cyan">
            <MessageSquare className="w-5 h-5" />
          </div>
        </div>

        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={channelData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="name"
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                padding: '12px 16px',
                fontSize: '13px',
              }}
              cursor={{ fill: '#f1f5f9' }}
            />
            <Bar
              dataKey="value"
              fill="#6366f1"
              radius={[6, 6, 0, 0]}
              maxBarSize={60}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ChartsSkeleton() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="rounded-xl border border-slate-200 bg-white p-6 dark:bg-slate-800 dark:border-slate-700"
        >
          <div className="mb-6 flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg skeleton" />
            <div className="space-y-2">
              <div className="h-4 w-32 skeleton" />
              <div className="h-2.5 w-24 skeleton" />
            </div>
          </div>
          <div className="h-[280px] skeleton rounded-lg" />
        </div>
      ))}
    </div>
  );
}
