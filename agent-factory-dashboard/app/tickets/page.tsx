'use client';

import React from 'react';
import { Header } from '@/components/Header';
import { useDashboard } from '@/contexts/DashboardContext';
import { Ticket as TicketType } from '@/types';
import { Search, Filter, MoreHorizontal } from 'lucide-react';
import { cn } from '@/lib/utils';

const statusColors: Record<string, string> = {
  open: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  in_progress: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  waiting_customer: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  resolved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  closed: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
};

export default function TicketsPage() {
  const { metrics, loading } = useDashboard();

  // Mock extended tickets list
  const allTickets: TicketType[] = [
    ...(metrics?.recent_tickets || []),
    ...Array.from({ length: 20 }, (_, i) => ({
      id: `TKT-2024-${String(1247 - i - 1).padStart(4, '0')}`,
      customer_id: `CUST-${String(i + 1).padStart(3, '0')}`,
      customer_name: `Customer ${i + 1}`,
      customer_email: `customer${i + 1}@example.com`,
      channel: ['web', 'gmail', 'whatsapp'][i % 3] as 'web' | 'gmail' | 'whatsapp',
      status: ['open', 'in_progress', 'resolved', 'closed'][i % 4] as TicketType['status'],
      priority: ['low', 'medium', 'high', 'critical'][i % 4] as TicketType['priority'],
      subject: `Sample ticket subject ${i + 1}`,
      description: `This is a sample ticket description for ticket ${i + 1}`,
      created_at: new Date(Date.now() - (i + 1) * 3600000).toISOString(),
      updated_at: new Date().toISOString(),
      sla_status: ['on_track', 'at_risk', 'breached'][i % 3] as TicketType['sla_status'],
      sentiment_score: 0.3 + (i % 7) * 0.1,
    })),
  ];

  return (
    <>
      <Header title="Tickets" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Filters */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
                <input
                  type="text"
                  placeholder="Search tickets..."
                  className="h-10 w-80 rounded-lg border border-zinc-200 bg-white pl-10 pr-4 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-900"
                />
              </div>
              <button className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
                <Filter className="h-4 w-4" />
                Filter
              </button>
            </div>
            <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              New Ticket
            </button>
          </div>

          {/* Tickets Table */}
          <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <table className="w-full">
              <thead className="bg-zinc-50 dark:bg-zinc-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                    Ticket
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                    Channel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                    Priority
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {allTickets.map((ticket) => (
                  <tr
                    key={ticket.id}
                    className="transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800"
                  >
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-zinc-900 dark:text-zinc-100">
                          {ticket.id}
                        </div>
                        <div className="text-sm text-zinc-500 dark:text-zinc-400">
                          {ticket.subject}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-zinc-900 dark:text-zinc-100">
                        {ticket.customer_name}
                      </div>
                      <div className="text-sm text-zinc-500 dark:text-zinc-400">
                        {ticket.customer_email}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={cn(
                          'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize',
                          {
                            'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200':
                              ticket.channel === 'web',
                            'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200':
                              ticket.channel === 'gmail',
                            'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200':
                              ticket.channel === 'whatsapp',
                          }
                        )}
                      >
                        {ticket.channel}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={cn(
                          'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize',
                          statusColors[ticket.status]
                        )}
                      >
                        {ticket.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={cn(
                          'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize',
                          {
                            'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200':
                              ticket.priority === 'low',
                            'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200':
                              ticket.priority === 'medium',
                            'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200':
                              ticket.priority === 'high',
                            'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200':
                              ticket.priority === 'critical',
                          }
                        )}
                      >
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-zinc-500 dark:text-zinc-400">
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300">
                        <MoreHorizontal className="h-5 w-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </>
  );
}
