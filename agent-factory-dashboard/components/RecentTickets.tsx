'use client';

import React from 'react';
import { useDashboard } from '@/contexts/DashboardContext';
import { Clock, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

const statusStyles: Record<string, string> = {
  open: 'badge-indigo',
  in_progress: 'badge-yellow',
  waiting_customer: 'badge-purple',
  resolved: 'badge-green',
  closed: 'badge-slate',
};

const priorityStyles: Record<string, string> = {
  low: 'badge-slate',
  medium: 'badge-indigo',
  high: 'badge-yellow',
  critical: 'badge-red',
};

const channelStyles: Record<string, string> = {
  web: 'bg-blue-600',
  gmail: 'bg-red-600',
  whatsapp: 'bg-green-600',
};

export function RecentTickets() {
  const { metrics, loading } = useDashboard();

  if (loading || !metrics) {
    return <TicketsSkeleton />;
  }

  return (
    <div className="table-container">
      {/* Header */}
      <div className="table-header">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Recent Tickets</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Latest support requests</p>
          </div>
          <button className="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-700 transition-colors dark:text-indigo-400 dark:hover:text-indigo-300">
            View All
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200 dark:bg-slate-700/50 dark:border-slate-700">
            <tr>
              <th className="table-th">Ticket</th>
              <th className="table-th">Customer</th>
              <th className="table-th">Channel</th>
              <th className="table-th">Status</th>
              <th className="table-th">Priority</th>
              <th className="table-th">SLA Status</th>
              <th className="table-th">Sentiment</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
            {metrics.recent_tickets.map((ticket) => (
              <tr key={ticket.id} className="table-row">
                <td className="table-td">
                  <div>
                    <div className="font-medium text-slate-900 dark:text-white">{ticket.id}</div>
                    <div className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{ticket.subject}</div>
                  </div>
                </td>
                <td className="table-td">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-indigo-700 flex items-center justify-center text-white text-sm font-medium shadow-sm">
                      {getInitials(ticket.customer_name)}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-slate-900 dark:text-white">
                        {ticket.customer_name}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        {ticket.customer_email}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="table-td">
                  <span className={cn(
                    'inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium text-white',
                    channelStyles[ticket.channel] || channelStyles.web
                  )}>
                    {ticket.channel}
                  </span>
                </td>
                <td className="table-td">
                  <span className={cn(
                    'badge',
                    statusStyles[ticket.status] || statusStyles.open
                  )}>
                    {ticket.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="table-td">
                  <span className={cn(
                    'badge',
                    priorityStyles[ticket.priority] || priorityStyles.medium
                  )}>
                    {ticket.priority}
                  </span>
                </td>
                <td className="table-td">
                  <SLAStatusIndicator status={ticket.sla_status} />
                </td>
                <td className="table-td">
                  <SentimentBar score={ticket.sentiment_score ?? 0.5} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SLAStatusIndicator({ status }: { status: string }) {
  const configs: Record<string, { icon: React.ReactNode; color: string; bg: string }> = {
    on_track: {
      icon: <CheckCircle className="w-4 h-4" />,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    at_risk: {
      icon: <Clock className="w-4 h-4" />,
      color: 'text-yellow-600',
      bg: 'bg-yellow-50',
    },
    breached: {
      icon: <AlertCircle className="w-4 h-4" />,
      color: 'text-red-600',
      bg: 'bg-red-50',
    },
  };

  const config = configs[status] || configs.on_track;

  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium',
      config.bg,
      config.color
    )}>
      {config.icon}
      {status.replace('_', ' ')}
    </span>
  );
}

function SentimentBar({ score }: { score: number }) {
  const percentage = Math.round(score * 100);
  const gradient =
    score >= 0.7
      ? 'bg-green-500'
      : score >= 0.4
      ? 'bg-yellow-500'
      : 'bg-red-500';

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className={`h-full rounded-full ${gradient} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs font-medium text-slate-600 dark:text-slate-400">{percentage}%</span>
    </div>
  );
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

function TicketsSkeleton() {
  return (
    <div className="table-container">
      <div className="table-header">
        <div className="h-5 w-32 skeleton" />
      </div>
      <div className="p-6">
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 skeleton rounded-lg" />
          ))}
        </div>
      </div>
    </div>
  );
}
