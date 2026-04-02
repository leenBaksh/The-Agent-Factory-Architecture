'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  LayoutDashboard,
  Ticket,
  MessagesSquare,
  Users,
  Server,
  Activity,
  ShieldCheck,
  Sparkles,
  Settings,
  LogOut,
  ChevronDown,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const navigation = [
  {
    section: 'Main',
    items: [
      { name: 'Dashboard', href: '/', icon: LayoutDashboard },
      { name: 'Tickets', href: '/tickets', icon: Ticket },
      { name: 'Conversations', href: '/conversations', icon: MessagesSquare },
      { name: 'Customers', href: '/customers', icon: Users },
    ],
  },
  {
    section: 'Management',
    items: [
      { name: 'FTE Instances', href: '/ftes', icon: Server },
      { name: 'Analytics', href: '/analytics', icon: Activity },
      { name: 'SLA Monitor', href: '/sla', icon: ShieldCheck },
      { name: 'Guardrails', href: '/guardrails', icon: Sparkles },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-header">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 flex items-center justify-center shadow-md">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 dark:text-white">Agent Factory</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">Digital FTE Management</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {navigation.map((section) => (
          <div key={section.section} className="nav-section">
            <h3 className="nav-section-title">{section.section}</h3>
            <div className="space-y-1">
              {section.items.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`nav-item ${isActive ? 'nav-item-active' : ''}`}
                  >
                    <Icon className={`nav-item-icon ${isActive ? 'text-indigo-600 dark:text-indigo-400' : ''}`} />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}

        {/* Bottom Section */}
        <div className="mt-auto pt-6 border-t border-slate-200 dark:border-slate-700">
          <div className="space-y-1">
            <Link href="/settings" className="nav-item">
              <Settings className="nav-item-icon" />
              <span>Settings</span>
            </Link>
            <button onClick={logout} className="nav-item w-full text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20">
              <LogOut className="nav-item-icon" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </nav>

      {/* User Profile */}
      <div className="px-4 py-4 border-t border-slate-200 dark:border-slate-700">
        <button className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-600 to-indigo-700 flex items-center justify-center text-white text-sm font-semibold shadow-md">
            {user?.name ? getInitials(user.name) : 'JD'}
          </div>
          <div className="flex-1 text-left">
            <p className="text-sm font-medium text-slate-900 dark:text-white">{user?.name || 'John Doe'}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">{user?.role || 'Administrator'}</p>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400" />
        </button>
      </div>
    </aside>
  );
}
