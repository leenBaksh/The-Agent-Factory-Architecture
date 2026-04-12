'use client';

import React, { useState } from 'react';
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
  ChevronUp,
  HelpCircle,
  Zap,
  ChevronLeft,
  ChevronRight,
  Menu,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

const navigation = [
  {
    section: 'Main',
    items: [
      { name: 'Dashboard', href: '/', icon: LayoutDashboard, badge: null },
      { name: 'Tickets', href: '/tickets', icon: Ticket, badge: '12' },
      { name: 'Conversations', href: '/conversations', icon: MessagesSquare, badge: null },
      { name: 'Customers', href: '/customers', icon: Users, badge: null },
    ],
  },
  {
    section: 'Management',
    items: [
      { name: 'FTE Instances', href: '/ftes', icon: Server, badge: null },
      { name: 'Analytics', href: '/analytics', icon: Activity, badge: null },
      { name: 'SLA Monitor', href: '/sla', icon: ShieldCheck, badge: '3' },
      { name: 'Guardrails', href: '/guardrails', icon: Sparkles, badge: null },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [expandedSections, setExpandedSections] = useState({
    Main: true,
    Management: true,
  });
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section as keyof typeof prev],
    }));
  };

  const isSectionExpanded = (section: string): boolean => {
    return expandedSections[section as keyof typeof expandedSections] ?? true;
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2.5 rounded-xl bg-gradient-to-r from-fuchsia-500 to-cyan-500 text-white shadow-lg shadow-fuchsia-500/30"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 h-full bg-gradient-to-b from-white via-slate-50 to-white border-r border-slate-200 flex flex-col z-50 backdrop-blur-xl transition-all duration-300 ease-in-out dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 dark:border-slate-700',
          isCollapsed ? 'w-20' : 'w-64',
          'lg:translate-x-0',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Collapse Toggle - Desktop */}
        <button
          onClick={toggleSidebar}
          className="hidden lg:flex absolute -right-3 top-16 items-center justify-center w-6 h-6 rounded-full bg-gradient-to-r from-fuchsia-500 to-cyan-500 text-white shadow-lg cursor-pointer z-10"
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>

        {/* Logo Section */}
        <div className={cn(
          'px-4 py-4 border-b border-slate-200 bg-gradient-to-r from-fuchsia-50/30 via-cyan-50/30 to-transparent dark:border-slate-700 dark:from-fuchsia-900/20 dark:via-cyan-900/20 transition-all',
          isCollapsed ? 'px-2' : 'px-4'
        )}>
          <Link href="/" className="group flex items-center gap-2.5">
            <div className="relative flex-shrink-0">
              <div className={cn(
                'rounded-lg bg-gradient-to-br from-fuchsia-500 via-cyan-500 to-teal-500 flex items-center justify-center shadow-lg shadow-fuchsia-500/30 group-hover:shadow-xl group-hover:shadow-fuchsia-500/40 transition-all duration-300',
                isCollapsed ? 'w-10 h-10' : 'w-9 h-9'
              )}>
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white dark:border-slate-800"></div>
            </div>
            {!isCollapsed && (
              <div className="overflow-hidden">
                <h1 className="text-sm font-bold bg-gradient-to-r from-fuchsia-600 via-cyan-600 to-teal-600 bg-clip-text text-transparent whitespace-nowrap">
                  Agent Factory
                </h1>
                <p className="text-[9px] text-slate-500 dark:text-slate-400 whitespace-nowrap font-medium">Digital FTE Management</p>
              </div>
            )}
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-3 space-y-4 overflow-y-auto custom-scrollbar">
          {navigation.map((section) => (
            <div key={section.section} className="nav-section">
              {!isCollapsed && (
                <button
                  onClick={() => toggleSection(section.section)}
                  className="flex items-center justify-between w-full px-2.5 py-1.5 mb-1 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                >
                  <h3 className="text-[9px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">{section.section}</h3>
                  {isSectionExpanded(section.section) ? (
                    <ChevronUp className="w-3 h-3 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-3 h-3 text-slate-400" />
                  )}
                </button>
              )}
              
              {(isSectionExpanded(section.section) || isCollapsed) && (
                <div className="space-y-0.5">
                  {section.items.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;

                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        className={cn(
                          'nav-item group relative',
                          isActive ? 'nav-item-active' : '',
                          isCollapsed ? 'justify-center px-2' : 'px-2.5'
                        )}
                        title={isCollapsed ? item.name : undefined}
                      >
                        {/* Active indicator line - curved */}
                        {isActive && (
                          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-fuchsia-500 to-cyan-500 rounded-r-full"></div>
                        )}

                        <div className={cn(
                          'nav-item-icon relative flex items-center justify-center',
                          isActive ? 'text-fuchsia-600 dark:text-fuchsia-400' : 'text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300'
                        )}>
                          <Icon className={cn(isCollapsed ? 'w-6 h-6' : 'w-5 h-5')} />
                          {item.badge && !isCollapsed && (
                            <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-[16px] px-0.5 flex items-center justify-center text-[9px] font-bold text-white bg-gradient-to-r from-fuchsia-500 to-cyan-500 rounded-full shadow-sm">
                              {item.badge}
                            </span>
                          )}
                          {item.badge && isCollapsed && (
                            <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-gradient-to-r from-fuchsia-500 to-cyan-500 rounded-full border-2 border-white dark:border-slate-800"></span>
                          )}
                        </div>
                        {!isCollapsed && <span className="flex-1 text-xs font-medium whitespace-nowrap">{item.name}</span>}

                        {/* Hover gradient background - curved */}
                        {!isActive && (
                          <div className="absolute inset-0 bg-gradient-to-r from-fuchsia-50 to-transparent dark:from-fuchsia-900/10 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg -z-10"></div>
                        )}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          ))}

          {/* Bottom Actions */}
          <div className={cn('mt-auto pt-3 space-y-1', isCollapsed ? 'space-y-2' : '')}>
            <Link 
              href="/settings" 
              className={cn(
                'flex items-center gap-2.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-700/50 dark:hover:text-white transition-all',
                isCollapsed ? 'justify-center px-2 py-2.5' : 'px-2.5 py-2'
              )}
              title={isCollapsed ? 'Settings' : undefined}
            >
              <Settings className={cn(isCollapsed ? 'w-5 h-5' : 'w-4 h-4')} />
              {!isCollapsed && <span>Settings</span>}
            </Link>
            
            <Link 
              href="/help" 
              className={cn(
                'flex items-center gap-2.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-700/50 dark:hover:text-white transition-all w-full',
                isCollapsed ? 'justify-center px-2 py-2.5' : 'px-2.5 py-2'
              )}
              title={isCollapsed ? 'Help' : undefined}
            >
              <HelpCircle className={cn(isCollapsed ? 'w-5 h-5' : 'w-4 h-4')} />
              {!isCollapsed && <span>Help</span>}
            </Link>
            
            <button 
              onClick={logout}
              className={cn(
                'flex items-center gap-2.5 rounded-lg text-xs font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all w-full',
                isCollapsed ? 'justify-center px-2 py-2.5' : 'px-2.5 py-2'
              )}
              title={isCollapsed ? 'Logout' : undefined}
            >
              <LogOut className={cn(isCollapsed ? 'w-5 h-5' : 'w-4 h-4')} />
              {!isCollapsed && <span>Logout</span>}
            </button>
          </div>
        </nav>

        {/* User Profile */}
        <div className={cn(
          'px-3 py-3 border-t border-slate-200 dark:border-slate-700',
          isCollapsed ? 'px-2' : 'px-3'
        )}>
          <div className="relative group">
            <div className="absolute inset-0 bg-gradient-to-r from-fuchsia-500/10 via-cyan-500/10 to-teal-500/10 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <button 
              className={cn(
                'flex items-center gap-2.5 w-full rounded-lg hover:bg-transparent transition-colors relative',
                isCollapsed ? 'justify-center p-2' : 'p-1.5'
              )}
              title={isCollapsed ? `${user?.name || 'Admin'} - ${user?.role || 'Administrator'}` : undefined}
            >
              <div className="relative flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-fuchsia-500 via-cyan-500 to-teal-500 flex items-center justify-center text-white text-xs font-bold shadow-lg shadow-fuchsia-500/30">
                  {user?.name ? getInitials(user.name) : 'AU'}
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white dark:border-slate-800"></div>
              </div>
              {!isCollapsed && (
                <div className="flex-1 text-left min-w-0">
                  <p className="text-[11px] font-semibold text-slate-900 dark:text-white truncate">{user?.name || 'Admin User'}</p>
                  <p className="text-[9px] text-slate-500 dark:text-slate-400 truncate">{user?.role || 'Administrator'}</p>
                </div>
              )}
            </button>
          </div>
        </div>
      </aside>

      {/* Custom Scrollbar Styles */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(to bottom, #d946ef, #06b6d4, #14b8a6);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(to bottom, #c026d3, #0891b2, #0d9488);
        }
      `}</style>
    </>
  );
}
