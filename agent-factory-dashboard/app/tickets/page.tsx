'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import { useDashboard } from '@/contexts/DashboardContext';
import { Ticket as TicketType } from '@/types';
import { Search, Filter, MoreHorizontal, MessageCircle, Bell, CheckCircle, Plus, X } from 'lucide-react';
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
  const [showWhatsAppModal, setShowWhatsAppModal] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<TicketType | null>(null);
  const [notificationSent, setNotificationSent] = useState(false);
  const [showNewTicketModal, setShowNewTicketModal] = useState(false);
  const [ticketCreated, setTicketCreated] = useState(false);

  const sendWhatsAppNotification = (ticket: TicketType) => {
    setSelectedTicket(ticket);
    setShowWhatsAppModal(true);
    setNotificationSent(false);
  };

  const handleSendWhatsApp = async () => {
    if (selectedTicket) {
      try {
        const message = `🎫 Ticket Update\n\nTicket ID: ${selectedTicket.id}\nStatus: ${selectedTicket.status}\nPriority: ${selectedTicket.priority}\nSubject: ${selectedTicket.subject}\n\nYour ticket has been updated. Please check your dashboard for details.`;

        // Call the real WhatsApp API
        const response = await fetch('http://localhost:8000/api/notifications/whatsapp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            to_phone: '+923103871019', // Your verified number
            message: message,
          }),
        });

        if (response.ok) {
          setNotificationSent(true);
          setTimeout(() => {
            setShowWhatsAppModal(false);
            setSelectedTicket(null);
            setNotificationSent(false);
          }, 2000);
        } else {
          const error = await response.json();
          alert('Failed to send: ' + (error.detail?.error || 'Unknown error'));
        }
      } catch (error) {
        alert('Connection error: ' + (error as Error).message);
      }
    }
  };

  // Mock extended tickets list - use stable IDs to prevent hydration errors
  const allTickets: TicketType[] = [
    ...(metrics?.recent_tickets || []),
    ...Array.from({ length: 20 }, (_, i) => ({
      id: `MOCK-${String(i).padStart(3, '0')}`,
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
            <button 
              onClick={() => setShowNewTicketModal(true)}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
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
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => sendWhatsAppNotification(ticket)}
                          className="rounded-lg p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                          title="Send WhatsApp Notification"
                        >
                          <MessageCircle className="h-5 w-5" />
                        </button>
                        <button className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300">
                          <MoreHorizontal className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* WhatsApp Notification Modal */}
      {showWhatsAppModal && selectedTicket && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 relative animate-in fade-in zoom-in duration-200">
            {/* Close Button */}
            <button
              onClick={() => {
                setShowWhatsAppModal(false);
                setSelectedTicket(null);
                setNotificationSent(false);
              }}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            >
              ✕
            </button>

            {!notificationSent ? (
              <>
                {/* Header */}
                <div className="flex items-center gap-3 mb-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-emerald-500">
                    <MessageCircle className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                      WhatsApp Notification
                    </h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      Send update to customer
                    </p>
                  </div>
                </div>

                {/* Ticket Info */}
                <div className="mb-6 p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500 dark:text-slate-400">Ticket ID:</span>
                      <span className="font-medium text-slate-900 dark:text-white">{selectedTicket.id}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500 dark:text-slate-400">Customer:</span>
                      <span className="font-medium text-slate-900 dark:text-white">{selectedTicket.customer_name}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500 dark:text-slate-400">Status:</span>
                      <span className="font-medium text-slate-900 dark:text-white capitalize">{selectedTicket.status.replace('_', ' ')}</span>
                    </div>
                  </div>
                </div>

                {/* Message Preview */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Message Preview
                  </label>
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
                    <p className="text-sm text-green-900 dark:text-green-100 whitespace-pre-line">
{`🎫 Ticket Update

Ticket ID: ${selectedTicket.id}
Status: ${selectedTicket.status.replace('_', ' ')}
Priority: ${selectedTicket.priority}

Your ticket has been updated. Please check your dashboard for details.`}
                    </p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setShowWhatsAppModal(false);
                      setSelectedTicket(null);
                    }}
                    className="flex-1 py-2.5 px-4 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSendWhatsApp}
                    className="flex-1 py-2.5 px-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-medium rounded-lg hover:shadow-lg transition-all flex items-center justify-center gap-2"
                  >
                    <Bell className="w-4 h-4" />
                    Send Notification
                  </button>
                </div>
              </>
            ) : (
              /* Success State */
              <div className="text-center py-8">
                <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4 mx-auto">
                  <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                  Notification Sent!
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  WhatsApp notification sent to {selectedTicket.customer_name}
                </p>
                <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <p className="text-xs text-green-700 dark:text-green-300">
                    ✅ Message delivered successfully
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Success Banner */}
      {ticketCreated && (
        <div className="fixed top-4 right-4 z-50 flex items-center gap-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4 shadow-lg animate-in slide-in-from-top-2 duration-300">
          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" />
          <p className="text-sm font-medium text-green-800 dark:text-green-200 flex-1">
            Ticket created successfully!
          </p>
          <button 
            onClick={() => setTicketCreated(false)}
            className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* New Ticket Modal */}
      {showNewTicketModal && (
        <NewTicketModal 
          onClose={() => setShowNewTicketModal(false)}
          onSuccess={() => {
            setTicketCreated(true);
            setShowNewTicketModal(false);
            setTimeout(() => setTicketCreated(false), 4000);
          }}
        />
      )}
    </>
  );
}

function NewTicketModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    customerName: '',
    customerEmail: '',
    priority: 'medium',
    channel: 'web',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Creating ticket:', formData);
    onSuccess();
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-lg w-full p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
          <X className="w-5 h-5" />
        </button>
        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Create New Ticket</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Subject</label>
            <input type="text" value={formData.subject} onChange={(e) => setFormData({...formData, subject: e.target.value})} placeholder="Brief description of the issue" className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Description</label>
            <textarea value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} placeholder="Detailed description" rows={3} className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500 resize-none" required />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Customer Name</label>
              <input type="text" value={formData.customerName} onChange={(e) => setFormData({...formData, customerName: e.target.value})} placeholder="John Doe" className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Customer Email</label>
              <input type="email" value={formData.customerEmail} onChange={(e) => setFormData({...formData, customerEmail: e.target.value})} placeholder="john@example.com" className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500" required />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Priority</label>
              <select value={formData.priority} onChange={(e) => setFormData({...formData, priority: e.target.value})} className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Channel</label>
              <select value={formData.channel} onChange={(e) => setFormData({...formData, channel: e.target.value})} className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500">
                <option value="web">Web</option>
                <option value="gmail">Gmail</option>
                <option value="whatsapp">WhatsApp</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3 pt-4">
            <button type="button" onClick={onClose} className="flex-1 py-2.5 px-4 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700">Cancel</button>
            <button type="submit" className="flex-1 py-2.5 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700">Create Ticket</button>
          </div>
        </form>
      </div>
    </div>
  );
}
