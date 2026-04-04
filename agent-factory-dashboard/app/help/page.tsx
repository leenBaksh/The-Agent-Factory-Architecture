'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import {
  HelpCircle,
  MessageSquare,
  Mail,
  Phone,
  Book,
  Video,
  Users,
  Search,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Zap,
  Shield,
  Settings,
  Ticket,
  ArrowRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const faqs = [
  {
    category: 'Getting Started',
    icon: Zap,
    questions: [
      {
        q: 'What is a Digital FTE?',
        a: 'A Digital FTE (Full-Time Equivalent) is an AI-powered agent that automates specific business processes. Each FTE is designed to handle tasks like customer support, sales inquiries, or technical assistance 24/7.',
      },
      {
        q: 'How do I create my first FTE?',
        a: 'Navigate to FTE Instances, click "Create New FTE", select a template (Customer Success, Sales, or Technical Support), configure the settings, and deploy. Your FTE will be active within minutes.',
      },
      {
        q: 'What channels do FTEs support?',
        a: 'Digital FTEs support Web chat, Gmail, WhatsApp, and can be extended to Slack, Microsoft Teams, and other channels through integrations.',
      },
    ],
  },
  {
    category: 'Features & Capabilities',
    icon: Shield,
    questions: [
      {
        q: 'How does SLA monitoring work?',
        a: 'The SLA Monitor tracks response times, resolution times, and compliance rates. Breaches are automatically detected and alerts are sent when tickets are at risk of missing SLA targets.',
      },
      {
        q: 'Can I customize FTE responses?',
        a: 'Yes! Each FTE has configurable guardrails, tone settings, and response templates. You can also set escalation rules for when human intervention is needed.',
      },
      {
        q: 'What analytics are available?',
        a: 'The Analytics page provides insights into conversation volume, resolution times, customer satisfaction, FTE performance, and trend analysis over time.',
      },
    ],
  },
  {
    category: 'Account & Settings',
    icon: Settings,
    questions: [
      {
        q: 'How do I change my password?',
        a: 'Go to Settings → Security → Password, click "Update", enter your current password and new password, then save changes.',
      },
      {
        q: 'Can I add team members?',
        a: 'Yes, navigate to Settings → Team Management, click "Invite Member", enter their email and role, and they\'ll receive an invitation.',
      },
      {
        q: 'How do I configure integrations?',
        a: 'Visit Settings → Integrations, select the service you want to connect (Slack, Gmail, etc.), and follow the authentication flow.',
      },
    ],
  },
  {
    category: 'Tickets & Escalations',
    icon: Ticket,
    questions: [
      {
        q: 'When does a ticket get escalated?',
        a: 'Tickets are automatically escalated when: SLA breach is imminent, confidence score is below threshold, customer requests human agent, or after max AI retries.',
      },
      {
        q: 'How do I view escalated tickets?',
        a: 'Go to Tickets page and use the filter to show "Escalated" tickets. You can also set up notifications for new escalations.',
      },
      {
        q: 'Can I reassign tickets?',
        a: 'Yes, open any ticket, click the "Assign" dropdown, and select a different team member or FTE instance.',
      },
    ],
  },
];

const quickLinks = [
  { 
    title: 'FTE Documentation', 
    description: 'Digital FTE setup & configuration', 
    icon: Book, 
    href: 'https://www.ibm.com/topics/robotic-process-automation',
    external: true,
  },
  { 
    title: 'Video Tutorials', 
    description: 'Learn to use Digital FTEs', 
    icon: Video, 
    href: 'https://www.youtube.com/results?search_query=digital+worker+automation+tutorial',
    external: true,
  },
  { 
    title: 'Community Forum', 
    description: 'Connect with FTE users', 
    icon: Users, 
    href: 'https://github.com/topics/rpa',
    external: true,
  },
  { 
    title: 'System Status', 
    description: 'FTE service health', 
    icon: Zap, 
    onClick: () => {
      const content = `⚡ Agent Factory System Status
      
✅ All Systems Operational

🟢 Core Services:
   • Dashboard API        ✓ Online
   • FTE Services         ✓ Online
   • Message Processing   ✓ Online
   • Database             ✓ Online

🟢 Integrations:
   • Gmail Integration    ✓ Online
   • WhatsApp Gateway     ✓ Online
   • Web Form Handler     ✓ Online

🟢 Monitoring:
   • SLA Monitor          ✓ Online
   • Alert System         ✓ Online
   • Analytics Engine     ✓ Online

Last updated: Just now
Uptime (30 days): 99.97%`;
      alert(content);
    },
  },
];

const contactOptions = [
  {
    title: 'Live Chat',
    description: 'Chat with our support team',
    icon: MessageSquare,
    color: 'from-fuchsia-500 to-cyan-500',
    action: 'Start Chat',
    available: 'Available 24/7',
    onClick: () => alert('🎨 Demo: Live Chat would open here\n\nIn production, this would connect to your support chat system.'),
  },
  {
    title: 'Email Support',
    description: 'Get help via email',
    icon: Mail,
    color: 'from-cyan-500 to-teal-500',
    action: 'Send Email',
    available: 'Response within 24h',
    onClick: () => window.location.href = 'mailto:support@agentfactory.com?subject=Help Request',
  },
  {
    title: 'Phone Support',
    description: 'Call us directly',
    icon: Phone,
    color: 'from-fuchsia-500 to-pink-500',
    action: 'Call Now',
    available: 'Mon-Fri, 9AM-6PM EST',
    onClick: () => window.location.href = 'tel:+1-800-AGENT-FTE',
  },
];

export default function HelpPage() {
  const [expandedFaq, setExpandedFaq] = useState<{ category: string; index: number } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const toggleFaq = (category: string, index: number) => {
    setExpandedFaq(expandedFaq?.category === category && expandedFaq.index === index ? null : { category, index });
  };

  return (
    <>
      <Header title="Help & Support" subtitle="Get help with your Digital FTEs" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-4 sm:p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-6xl space-y-8">
          
          {/* Search */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl blur opacity-20"></div>
            <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-2">
              <div className="flex items-center gap-3">
                <Search className="w-5 h-5 text-slate-400 ml-3" />
                <input
                  type="text"
                  placeholder="Search for help articles, guides, FAQs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 px-4 py-3 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 outline-none"
                />
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {quickLinks.map((link) => {
              const Icon = link.icon;
              
              // Render as link if href exists, otherwise as button
              if (link.href) {
                return (
                  <a
                    key={link.title}
                    href={link.href}
                    target={link.external ? '_blank' : '_self'}
                    rel={link.external ? 'noopener noreferrer' : undefined}
                    className="group relative overflow-hidden rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:shadow-lg hover:-translate-y-1 text-left dark:border-slate-700 dark:bg-slate-800"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-fuchsia-500 to-cyan-500">
                        <Icon className="h-5 w-5 text-white" />
                      </div>
                      <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-fuchsia-500 group-hover:translate-x-1 transition-all" />
                    </div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">{link.title}</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{link.description}</p>
                  </a>
                );
              }

              // Render as button for onClick handlers
              return (
                <button
                  key={link.title}
                  onClick={link.onClick}
                  className="group relative overflow-hidden rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:shadow-lg hover:-translate-y-1 text-left dark:border-slate-700 dark:bg-slate-800"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-fuchsia-500 to-cyan-500">
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-fuchsia-500 group-hover:translate-x-1 transition-all" />
                  </div>
                  <h3 className="font-semibold text-slate-900 dark:text-white">{link.title}</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{link.description}</p>
                </button>
              );
            })}
          </div>

          {/* Contact Options */}
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Contact Support</h2>
            <div className="grid gap-4 md:grid-cols-3">
              {contactOptions.map((option) => {
                const Icon = option.icon;
                return (
                  <div
                    key={option.title}
                    className="group relative overflow-hidden rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:shadow-lg dark:border-slate-700 dark:bg-slate-800"
                  >
                    <div className={`absolute inset-0 bg-gradient-to-br ${option.color} opacity-0 group-hover:opacity-5 transition-opacity`}></div>
                    <div className="relative">
                      <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${option.color} mb-4`}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{option.title}</h3>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{option.description}</p>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mt-3">{option.available}</p>
                      <button
                        onClick={option.onClick}
                        className={`mt-4 w-full py-2.5 rounded-lg bg-gradient-to-r ${option.color} text-white font-medium text-sm hover:shadow-lg transition-all`}
                      >
                        {option.action}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* FAQs */}
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Frequently Asked Questions</h2>
            <div className="space-y-4">
              {faqs.map((category) => {
                const Icon = category.icon;
                return (
                  <div
                    key={category.category}
                    className="rounded-xl border border-slate-200 bg-white overflow-hidden dark:border-slate-700 dark:bg-slate-800"
                  >
                    <div className="flex items-center gap-3 px-6 py-4 bg-gradient-to-r from-slate-50 to-transparent dark:from-slate-700/50">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500">
                        <Icon className="h-5 w-5 text-white" />
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{category.category}</h3>
                    </div>
                    <div className="divide-y divide-slate-100 dark:divide-slate-700">
                      {category.questions.map((faq, index) => (
                        <div key={index}>
                          <button
                            onClick={() => toggleFaq(category.category, index)}
                            className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                          >
                            <span className="text-sm font-medium text-slate-900 dark:text-white text-left pr-4">
                              {faq.q}
                            </span>
                            {expandedFaq?.category === category.category && expandedFaq.index === index ? (
                              <ChevronUp className="w-5 h-5 text-slate-400 flex-shrink-0" />
                            ) : (
                              <ChevronDown className="w-5 h-5 text-slate-400 flex-shrink-0" />
                            )}
                          </button>
                          {expandedFaq?.category === category.category && expandedFaq.index === index && (
                            <div className="px-6 pb-4 animate-in slide-in-from-top-2 duration-200">
                              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                                {faq.a}
                              </p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Still Need Help? */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-fuchsia-500 via-cyan-500 to-teal-500 p-8 text-center">
            <div className="absolute inset-0 bg-black/10"></div>
            <div className="relative">
              <HelpCircle className="w-16 h-16 text-white/80 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Still need help?</h2>
              <p className="text-white/80 mb-6 max-w-md mx-auto">
                Our support team is here to help you with any questions or issues you may have.
              </p>
              <div className="flex flex-wrap justify-center gap-3">
                <button
                  onClick={() => alert('🎨 Demo: Create Ticket\n\nThis would open a ticket creation form where users can describe their issue.')}
                  className="px-6 py-3 bg-white text-fuchsia-600 font-semibold rounded-lg hover:shadow-lg transition-all"
                >
                  Create a Ticket
                </button>
                <button
                  onClick={() => alert('🎨 Demo: Schedule a Call\n\nThis would open a calendar scheduling tool like Calendly.')}
                  className="px-6 py-3 bg-white/20 text-white font-semibold rounded-lg backdrop-blur-sm hover:bg-white/30 transition-all"
                >
                  Schedule a Call
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
