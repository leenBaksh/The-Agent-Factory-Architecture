'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import {
  Users,
  Search,
  Filter,
  Mail,
  Phone,
  Building2,
  Ticket,
  Star,
  Clock,
  TrendingUp,
  MessageSquare,
  ChevronRight,
  X,
  Download,
  Plus,
  MoreHorizontal,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const planColors: Record<string, string> = {
  free: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  basic: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  premium: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
  enterprise: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300',
};

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  inactive: 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400',
  vip: 'bg-gradient-to-r from-amber-400 to-orange-500 text-white',
};

interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  plan: 'free' | 'basic' | 'premium' | 'enterprise';
  totalTickets: number;
  openTickets: number;
  satisfaction: number;
  lastContact: string;
  createdAt: string;
  avatar?: string;
  status: 'active' | 'inactive' | 'vip';
}

export default function CustomersPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPlan, setSelectedPlan] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');

  // Mock customer data
  const customers: Customer[] = [
    {
      id: '1',
      name: 'Sarah Johnson',
      email: 'sarah.johnson@techcorp.com',
      phone: '+1 (555) 123-4567',
      company: 'TechCorp Inc.',
      plan: 'enterprise',
      totalTickets: 45,
      openTickets: 2,
      satisfaction: 4.8,
      lastContact: '2026-04-02T14:30:00Z',
      createdAt: '2025-06-15T00:00:00Z',
      status: 'vip',
    },
    {
      id: '2',
      name: 'Michael Chen',
      email: 'm.chen@startuplab.io',
      phone: '+1 (555) 234-5678',
      company: 'StartupLab',
      plan: 'premium',
      totalTickets: 28,
      openTickets: 1,
      satisfaction: 4.5,
      lastContact: '2026-04-01T09:15:00Z',
      createdAt: '2025-08-22T00:00:00Z',
      status: 'active',
    },
    {
      id: '3',
      name: 'Emily Rodriguez',
      email: 'emily.r@designstudio.com',
      phone: '+1 (555) 345-6789',
      company: 'Design Studio',
      plan: 'basic',
      totalTickets: 12,
      openTickets: 0,
      satisfaction: 4.2,
      lastContact: '2026-03-28T16:45:00Z',
      createdAt: '2025-11-03T00:00:00Z',
      status: 'active',
    },
    {
      id: '4',
      name: 'James Wilson',
      email: 'james@freelance.dev',
      phone: undefined,
      company: undefined,
      plan: 'free',
      totalTickets: 5,
      openTickets: 1,
      satisfaction: 3.8,
      lastContact: '2026-03-15T11:20:00Z',
      createdAt: '2026-01-10T00:00:00Z',
      status: 'active',
    },
    {
      id: '5',
      name: 'Amanda Foster',
      email: 'a.foster@globaltech.com',
      phone: '+1 (555) 456-7890',
      company: 'GlobalTech Solutions',
      plan: 'enterprise',
      totalTickets: 67,
      openTickets: 3,
      satisfaction: 4.9,
      lastContact: '2026-04-02T18:00:00Z',
      createdAt: '2025-03-20T00:00:00Z',
      status: 'vip',
    },
    {
      id: '6',
      name: 'David Park',
      email: 'david.park@innovate.co',
      phone: '+1 (555) 567-8901',
      company: 'Innovate Co',
      plan: 'premium',
      totalTickets: 34,
      openTickets: 0,
      satisfaction: 4.6,
      lastContact: '2026-03-30T13:30:00Z',
      createdAt: '2025-07-08T00:00:00Z',
      status: 'active',
    },
    {
      id: '7',
      name: 'Lisa Thompson',
      email: 'lisa.t@creativemedia.com',
      phone: '+1 (555) 678-9012',
      company: 'Creative Media',
      plan: 'basic',
      totalTickets: 8,
      openTickets: 2,
      satisfaction: 4.0,
      lastContact: '2026-04-01T10:00:00Z',
      createdAt: '2025-12-01T00:00:00Z',
      status: 'active',
    },
    {
      id: '8',
      name: 'Robert Martinez',
      email: 'r.martinez@oldclient.com',
      phone: '+1 (555) 789-0123',
      company: 'OldClient Corp',
      plan: 'premium',
      totalTickets: 22,
      openTickets: 0,
      satisfaction: 4.3,
      lastContact: '2026-02-15T08:45:00Z',
      createdAt: '2025-04-12T00:00:00Z',
      status: 'inactive',
    },
  ];

  // Filter customers
  const filteredCustomers = customers.filter((customer) => {
    const matchesSearch =
      customer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      customer.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      customer.company?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPlan = selectedPlan === 'all' || customer.plan === selectedPlan;
    const matchesStatus = selectedStatus === 'all' || customer.status === selectedStatus;
    return matchesSearch && matchesPlan && matchesStatus;
  });

  // Stats
  const totalCustomers = customers.length;
  const activeCustomers = customers.filter((c) => c.status === 'active').length;
  const vipCustomers = customers.filter((c) => c.status === 'vip').length;
  const avgSatisfaction = (customers.reduce((acc, c) => acc + c.satisfaction, 0) / customers.length).toFixed(1);

  return (
    <>
      <Header title="Customers" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Stats Overview */}
          <div className="grid gap-4 md:grid-cols-4">
            <StatCard
              icon={Users}
              label="Total Customers"
              value={totalCustomers}
              color="indigo"
            />
            <StatCard
              icon={TrendingUp}
              label="Active"
              value={activeCustomers}
              color="green"
            />
            <StatCard
              icon={Star}
              label="VIP Customers"
              value={vipCustomers}
              color="amber"
            />
            <StatCard
              icon={Star}
              label="Avg Satisfaction"
              value={avgSatisfaction}
              suffix="/5.0"
              color="purple"
            />
          </div>

          {/* Header Controls */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-1 items-center gap-3">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
                <input
                  type="text"
                  placeholder="Search customers..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-10 w-full rounded-lg border border-zinc-200 bg-white pl-10 pr-4 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-900"
                />
              </div>
              <select
                value={selectedPlan}
                onChange={(e) => setSelectedPlan(e.target.value)}
                className="h-10 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-indigo-500 dark:border-zinc-700 dark:bg-zinc-900"
              >
                <option value="all">All Plans</option>
                <option value="free">Free</option>
                <option value="basic">Basic</option>
                <option value="premium">Premium</option>
                <option value="enterprise">Enterprise</option>
              </select>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="h-10 rounded-lg border border-zinc-200 bg-white px-3 text-sm outline-none focus:border-indigo-500 dark:border-zinc-700 dark:bg-zinc-900"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="vip">VIP</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <button className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
                <Download className="h-4 w-4" />
                Export
              </button>
              <button className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
                <Plus className="h-4 w-4" />
                Add Customer
              </button>
            </div>
          </div>

          {/* Customers Table */}
          <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-zinc-50 dark:bg-zinc-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Plan
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Status
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Tickets
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Satisfaction
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Last Contact
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-zinc-500">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
                  {filteredCustomers.map((customer) => (
                    <tr
                      key={customer.id}
                      className="cursor-pointer transition-colors hover:bg-zinc-50 dark:hover:bg-zinc-800"
                      onClick={() => setSelectedCustomer(customer)}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-semibold text-sm">
                            {customer.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                          </div>
                          <div>
                            <div className="font-medium text-zinc-900 dark:text-zinc-100">
                              {customer.name}
                            </div>
                            <div className="text-sm text-zinc-500 dark:text-zinc-400">
                              {customer.email}
                            </div>
                            {customer.company && (
                              <div className="text-xs text-zinc-400 dark:text-zinc-500 flex items-center gap-1">
                                <Building2 className="h-3 w-3" />
                                {customer.company}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={cn(
                            'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize',
                            planColors[customer.plan]
                          )}
                        >
                          {customer.plan}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={cn(
                            'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize',
                            statusColors[customer.status]
                          )}
                        >
                          {customer.status === 'vip' && <Star className="mr-1 h-3 w-3" />}
                          {customer.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Ticket className="h-4 w-4 text-zinc-400" />
                          <span className="text-sm text-zinc-600 dark:text-zinc-400">
                            {customer.totalTickets}
                          </span>
                          {customer.openTickets > 0 && (
                            <span className="ml-1 text-xs text-amber-600">
                              ({customer.openTickets} open)
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Star className="h-4 w-4 text-amber-500 fill-amber-500" />
                          <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                            {customer.satisfaction.toFixed(1)}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-sm text-zinc-500 dark:text-zinc-400">
                          <Clock className="h-4 w-4" />
                          {formatDate(customer.lastContact)}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedCustomer(customer);
                          }}
                          className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800 dark:hover:text-zinc-300"
                        >
                          <ChevronRight className="h-5 w-5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredCustomers.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12">
                <Users className="h-12 w-12 text-zinc-300" />
                <p className="mt-4 text-zinc-500 dark:text-zinc-400">No customers found</p>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Customer Detail Modal */}
      {selectedCustomer && (
        <CustomerDetailModal
          customer={selectedCustomer}
          onClose={() => setSelectedCustomer(null)}
        />
      )}
    </>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  suffix,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  suffix?: string;
  color: 'indigo' | 'green' | 'amber' | 'purple';
}) {
  const colorClasses = {
    indigo: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400',
    green: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
    amber: 'bg-amber-100 text-amber-600 dark:bg-amber-900 dark:text-amber-400',
    purple: 'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-400',
  };

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="flex items-center justify-between">
        <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg', colorClasses[color])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
          {value}{suffix && <span className="text-base font-normal text-zinc-500">{suffix}</span>}
        </p>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{label}</p>
      </div>
    </div>
  );
}

function CustomerDetailModal({
  customer,
  onClose,
}: {
  customer: Customer;
  onClose: () => void;
}) {
  const [activeTab, setActiveTab] = useState<'overview' | 'tickets' | 'messages'>('overview');

  // Mock customer activity data
  const recentTickets = [
    { id: 'TKT-2024-001', subject: 'Login issue with SSO', status: 'resolved', date: '2026-04-01' },
    { id: 'TKT-2024-002', subject: 'Feature request: Dark mode', status: 'in_progress', date: '2026-03-28' },
    { id: 'TKT-2024-003', subject: 'Billing question', status: 'open', date: '2026-04-02' },
  ];

  const recentMessages = [
    { id: '1', role: 'customer', content: 'Hi, I\'m having trouble logging in with my SSO credentials.', date: '2026-04-01T10:30:00Z' },
    { id: '2', role: 'agent', content: 'Hello! I\'d be happy to help you with your SSO login issue. Let me check your account settings.', date: '2026-04-01T10:32:00Z' },
    { id: '3', role: 'customer', content: 'Thank you! I\'ve been trying for the past 30 minutes.', date: '2026-04-01T10:33:00Z' },
    { id: '4', role: 'agent', content: 'I found the issue. Your SSO configuration was updated. I\'ve reset it on our end. Please try logging in again.', date: '2026-04-01T10:35:00Z' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-xl bg-white shadow-2xl dark:bg-zinc-900"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-200 bg-zinc-50 px-6 py-4 dark:border-zinc-700 dark:bg-zinc-800">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-bold text-lg">
              {customer.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                {customer.name}
              </h2>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">{customer.email}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-200 hover:text-zinc-600 dark:hover:bg-zinc-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-zinc-200 dark:border-zinc-700">
          {(['overview', 'tickets', 'messages'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'flex-1 px-4 py-3 text-sm font-medium capitalize transition-colors',
                activeTab === tab
                  ? 'border-b-2 border-indigo-600 text-indigo-600 dark:text-indigo-400'
                  : 'text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-300'
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="max-h-[60vh] overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Info Grid */}
              <div className="grid gap-4 md:grid-cols-2">
                <InfoItem icon={Mail} label="Email" value={customer.email} />
                {customer.phone && (
                  <InfoItem icon={Phone} label="Phone" value={customer.phone} />
                )}
                {customer.company && (
                  <InfoItem icon={Building2} label="Company" value={customer.company} />
                )}
                <InfoItem
                  icon={Users}
                  label="Plan"
                  value={
                    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium capitalize', planColors[customer.plan])}>
                      {customer.plan}
                    </span>
                  }
                />
                <InfoItem
                  icon={Star}
                  label="Status"
                  value={
                    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium capitalize', statusColors[customer.status])}>
                      {customer.status}
                    </span>
                  }
                />
                <InfoItem
                  icon={Clock}
                  label="Customer Since"
                  value={formatDate(customer.createdAt)}
                />
              </div>

              {/* Stats */}
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-lg bg-zinc-50 p-4 text-center dark:bg-zinc-800">
                  <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                    {customer.totalTickets}
                  </p>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">Total Tickets</p>
                </div>
                <div className="rounded-lg bg-zinc-50 p-4 text-center dark:bg-zinc-800">
                  <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                    {customer.openTickets}
                  </p>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">Open Tickets</p>
                </div>
                <div className="rounded-lg bg-zinc-50 p-4 text-center dark:bg-zinc-800">
                  <div className="flex items-center justify-center gap-1">
                    <Star className="h-5 w-5 text-amber-500 fill-amber-500" />
                    <p className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                      {customer.satisfaction.toFixed(1)}
                    </p>
                  </div>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">Satisfaction</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tickets' && (
            <div className="space-y-3">
              {recentTickets.map((ticket) => (
                <div
                  key={ticket.id}
                  className="flex items-center justify-between rounded-lg border border-zinc-200 p-4 dark:border-zinc-700"
                >
                  <div>
                    <p className="font-medium text-zinc-900 dark:text-zinc-100">{ticket.id}</p>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">{ticket.subject}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-zinc-500">{ticket.date}</span>
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded-full text-xs font-medium capitalize',
                        ticket.status === 'resolved'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                          : ticket.status === 'in_progress'
                          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                      )}
                    >
                      {ticket.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'messages' && (
            <div className="space-y-4">
              {recentMessages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    'flex rounded-lg p-4',
                    message.role === 'customer'
                      ? 'bg-indigo-50 dark:bg-indigo-900/20'
                      : 'bg-zinc-50 dark:bg-zinc-800'
                  )}
                >
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100 capitalize">
                        {message.role}
                      </span>
                      <span className="text-xs text-zinc-500">
                        {formatDate(message.date)}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-zinc-700 dark:text-zinc-300">{message.content}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 dark:bg-zinc-800">
        <Icon className="h-4 w-4 text-zinc-500" />
      </div>
      <div className="flex-1">
        <p className="text-xs text-zinc-500 dark:text-zinc-400">{label}</p>
        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{value}</p>
      </div>
    </div>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return date.toLocaleDateString('en-US', { weekday: 'long' });
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
}
