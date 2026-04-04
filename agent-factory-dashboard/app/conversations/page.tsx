'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import {
  MessageSquare,
  Search,
  Filter,
  Send,
  Paperclip,
  Smile,
  MoreVertical,
  Phone,
  Video,
  Info,
  X,
  Check,
  CheckCheck,
  Clock,
  AlertCircle,
  User,
  Bot,
  ArrowLeft,
  ThumbsUp,
  ThumbsDown,
  Flag,
  Archive,
  Trash2,
  Mail,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  conversationId: string;
  role: 'customer' | 'agent' | 'system' | 'ai';
  content: string;
  timestamp: string;
  status?: 'sent' | 'delivered' | 'read';
  sentiment?: number;
  attachments?: string[];
}

interface Conversation {
  id: string;
  customerId: string;
  customerName: string;
  customerAvatar?: string;
  channel: 'web' | 'gmail' | 'whatsapp';
  status: 'active' | 'waiting' | 'resolved' | 'closed';
  lastMessage: string;
  lastMessageTime: string;
  unreadCount: number;
  ticketId?: string;
  messages: Message[];
  sentiment: 'positive' | 'neutral' | 'negative';
  assignedTo?: string;
}

export default function ConversationsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedChannel, setSelectedChannel] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [showMobileDetail, setShowMobileDetail] = useState(false);

  // Mock conversations data
  const conversations: Conversation[] = [
    {
      id: '1',
      customerId: 'CUST-001',
      customerName: 'Sarah Johnson',
      customerAvatar: 'SJ',
      channel: 'web',
      status: 'active',
      lastMessage: 'Thank you so much for your help!',
      lastMessageTime: '2026-04-02T23:45:00Z',
      unreadCount: 0,
      ticketId: 'TKT-2024-1250',
      sentiment: 'positive',
      assignedTo: 'Agent AI-1',
      messages: [
        { id: '1', conversationId: '1', role: 'customer', content: 'Hi, I\'m having trouble accessing my account dashboard. It keeps showing an error.', timestamp: '2026-04-02T23:30:00Z', sentiment: -0.3 },
        { id: '2', conversationId: '1', role: 'ai', content: 'Hello Sarah! I\'d be happy to help you with your dashboard access issue. Let me check your account status.', timestamp: '2026-04-02T23:30:15Z', status: 'read' },
        { id: '3', conversationId: '1', role: 'ai', content: 'I can see that your session may have expired. I\'ve just refreshed your access. Could you please try logging in again?', timestamp: '2026-04-02T23:31:00Z', status: 'read' },
        { id: '4', conversationId: '1', role: 'customer', content: 'Perfect! It\'s working now. Thank you so much for your help!', timestamp: '2026-04-02T23:45:00Z', sentiment: 0.8 },
      ],
    },
    {
      id: '2',
      customerId: 'CUST-002',
      customerName: 'Michael Chen',
      customerAvatar: 'MC',
      channel: 'gmail',
      status: 'waiting',
      lastMessage: 'I\'m waiting for a response on this billing issue...',
      lastMessageTime: '2026-04-02T22:30:00Z',
      unreadCount: 2,
      ticketId: 'TKT-2024-1249',
      sentiment: 'negative',
      assignedTo: 'Agent AI-2',
      messages: [
        { id: '1', conversationId: '2', role: 'customer', content: 'I was charged twice for my subscription this month. Can someone help?', timestamp: '2026-04-02T21:00:00Z', sentiment: -0.5 },
        { id: '2', conversationId: '2', role: 'ai', content: 'Hi Michael, I apologize for the inconvenience. Let me look into your billing history right away.', timestamp: '2026-04-02T21:01:00Z', status: 'read' },
        { id: '3', conversationId: '2', role: 'customer', content: 'I\'m waiting for a response on this billing issue. This is urgent!', timestamp: '2026-04-02T22:30:00Z', sentiment: -0.7 },
      ],
    },
    {
      id: '3',
      customerId: 'CUST-003',
      customerName: 'Emily Rodriguez',
      customerAvatar: 'ER',
      channel: 'whatsapp',
      status: 'active',
      lastMessage: 'Is this feature available in the premium plan?',
      lastMessageTime: '2026-04-02T23:50:00Z',
      unreadCount: 1,
      ticketId: 'TKT-2024-1248',
      sentiment: 'neutral',
      assignedTo: 'Agent AI-1',
      messages: [
        { id: '1', conversationId: '3', role: 'customer', content: 'Hi! I\'m interested in upgrading my plan.', timestamp: '2026-04-02T23:45:00Z', sentiment: 0.2 },
        { id: '2', conversationId: '3', role: 'ai', content: 'Hello Emily! I\'d be happy to help you with plan upgrades. What features are you looking for?', timestamp: '2026-04-02T23:46:00Z', status: 'read' },
        { id: '3', conversationId: '3', role: 'customer', content: 'Is this feature available in the premium plan?', timestamp: '2026-04-02T23:50:00Z', sentiment: 0 },
      ],
    },
    {
      id: '4',
      customerId: 'CUST-004',
      customerName: 'James Wilson',
      customerAvatar: 'JW',
      channel: 'web',
      status: 'resolved',
      lastMessage: 'Great, that solved my problem!',
      lastMessageTime: '2026-04-02T20:15:00Z',
      unreadCount: 0,
      ticketId: 'TKT-2024-1247',
      sentiment: 'positive',
      assignedTo: 'Agent AI-3',
      messages: [
        { id: '1', conversationId: '4', role: 'customer', content: 'How do I export my data?', timestamp: '2026-04-02T20:00:00Z', sentiment: 0 },
        { id: '2', conversationId: '4', role: 'ai', content: 'You can export your data by going to Settings > Data > Export. Would you like me to guide you through it?', timestamp: '2026-04-02T20:01:00Z', status: 'read' },
        { id: '3', conversationId: '4', role: 'customer', content: 'Great, that solved my problem!', timestamp: '2026-04-02T20:15:00Z', sentiment: 0.9 },
      ],
    },
    {
      id: '5',
      customerId: 'CUST-005',
      customerName: 'Amanda Foster',
      customerAvatar: 'AF',
      channel: 'gmail',
      status: 'active',
      lastMessage: 'Can we schedule a call to discuss enterprise features?',
      lastMessageTime: '2026-04-02T23:55:00Z',
      unreadCount: 1,
      ticketId: 'TKT-2024-1246',
      sentiment: 'positive',
      assignedTo: 'Agent AI-2',
      messages: [
        { id: '1', conversationId: '5', role: 'customer', content: 'Hello, I\'m interested in enterprise features for my team.', timestamp: '2026-04-02T23:30:00Z', sentiment: 0.4 },
        { id: '2', conversationId: '5', role: 'ai', content: 'Hi Amanda! I\'d be happy to tell you about our enterprise features. What specific capabilities are you looking for?', timestamp: '2026-04-02T23:31:00Z', status: 'read' },
        { id: '3', conversationId: '5', role: 'customer', content: 'Can we schedule a call to discuss enterprise features?', timestamp: '2026-04-02T23:55:00Z', sentiment: 0.5 },
      ],
    },
  ];

  const channelIcons: Record<string, React.ElementType> = {
    web: MessageSquare,
    gmail: Mail,
    whatsapp: Phone,
  };

  const channelColors: Record<string, string> = {
    web: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400',
    gmail: 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400',
    whatsapp: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
  };

  const statusColors: Record<string, string> = {
    active: 'bg-green-500',
    waiting: 'bg-amber-500',
    resolved: 'bg-blue-500',
    closed: 'bg-slate-500',
  };

  const sentimentColors: Record<string, string> = {
    positive: 'text-green-600 bg-green-50 dark:bg-green-900/20',
    neutral: 'text-slate-600 bg-slate-50 dark:bg-slate-800',
    negative: 'text-red-600 bg-red-50 dark:bg-red-900/20',
  };

  // Filter conversations
  const filteredConversations = conversations.filter((conv) => {
    const matchesSearch =
      conv.customerName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.lastMessage.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesChannel = selectedChannel === 'all' || conv.channel === selectedChannel;
    const matchesStatus = selectedStatus === 'all' || conv.status === selectedStatus;
    return matchesSearch && matchesChannel && matchesStatus;
  });

  const activeCount = conversations.filter((c) => c.status === 'active').length;
  const waitingCount = conversations.filter((c) => c.status === 'waiting').length;
  const totalUnread = conversations.reduce((acc, c) => acc + c.unreadCount, 0);

  const handleSendMessage = () => {
    if (!messageInput.trim() || !selectedConversation) return;
    // In real app, would send message via API
    setMessageInput('');
  };

  const handleSelectConversation = (conv: Conversation) => {
    setSelectedConversation(conv);
    setShowMobileDetail(true);
  };

  return (
    <>
      <Header title="Conversations" />
      <main className="flex-1 overflow-hidden bg-zinc-50 dark:bg-zinc-950">
        <div className="flex h-full">
          {/* Conversations List */}
          <div className={cn(
            'w-full border-r border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 md:w-96',
            showMobileDetail && 'hidden md:flex'
          )}>
            {/* Stats Header */}
            <div className="border-b border-zinc-200 p-4 dark:border-zinc-800">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
                  All Conversations
                </h2>
                <span className="text-xs text-zinc-500">
                  {activeCount} active • {waitingCount} waiting
                </span>
              </div>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
                  <input
                    type="text"
                    placeholder="Search conversations..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="h-9 w-full rounded-lg border border-zinc-200 bg-zinc-50 pl-9 pr-3 text-sm outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
                  />
                </div>
                <select
                  value={selectedChannel}
                  onChange={(e) => setSelectedChannel(e.target.value)}
                  className="h-9 rounded-lg border border-zinc-200 bg-zinc-50 px-2 text-sm outline-none focus:border-indigo-500 dark:border-zinc-700 dark:bg-zinc-800"
                >
                  <option value="all">All</option>
                  <option value="web">Web</option>
                  <option value="gmail">Gmail</option>
                  <option value="whatsapp">WhatsApp</option>
                </select>
              </div>
            </div>

            {/* Conversations List */}
            <div className="overflow-y-auto" style={{ height: 'calc(100vh - 220px)' }}>
              {filteredConversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv)}
                  className={cn(
                    'cursor-pointer border-b border-zinc-100 p-4 transition-colors hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-800',
                    selectedConversation?.id === conv.id && 'bg-indigo-50 dark:bg-indigo-900/20'
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className="relative">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-semibold text-sm">
                        {conv.customerAvatar}
                      </div>
                      <div className={cn(
                        'absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white dark:border-zinc-900',
                        statusColors[conv.status]
                      )} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate">
                          {conv.customerName}
                        </h3>
                        <span className="text-xs text-zinc-400">
                          {formatTime(conv.lastMessageTime)}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center gap-2">
                        <span className={cn(
                          'flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium capitalize',
                          channelColors[conv.channel]
                        )}>
                          {React.createElement(channelIcons[conv.channel], { className: 'h-2.5 w-2.5' })}
                          {conv.channel}
                        </span>
                        <span className={cn(
                          'rounded px-1.5 py-0.5 text-[10px] font-medium capitalize',
                          sentimentColors[conv.sentiment]
                        )}>
                          {conv.sentiment}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400 truncate">
                        {conv.lastMessage}
                      </p>
                    </div>
                    {conv.unreadCount > 0 && (
                      <div className="flex h-5 min-w-5 items-center justify-center rounded-full bg-indigo-600 px-1 text-xs font-medium text-white">
                        {conv.unreadCount}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Conversation Detail */}
          <div className={cn(
            'hidden flex-1 flex-col bg-white dark:bg-zinc-900 md:flex',
            showMobileDetail && 'flex w-full'
          )}>
            {selectedConversation ? (
              <>
                {/* Header */}
                <div className="flex items-center justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setShowMobileDetail(false)}
                      className="md:hidden rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                    >
                      <ArrowLeft className="h-5 w-5" />
                    </button>
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-semibold">
                      {selectedConversation.customerAvatar}
                    </div>
                    <div>
                      <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">
                        {selectedConversation.customerName}
                      </h2>
                      <div className="flex items-center gap-2 text-xs text-zinc-500">
                        <span className="capitalize">{selectedConversation.channel}</span>
                        {selectedConversation.ticketId && (
                          <>
                            <span>•</span>
                            <span>{selectedConversation.ticketId}</span>
                          </>
                        )}
                        {selectedConversation.assignedTo && (
                          <>
                            <span>•</span>
                            <span>{selectedConversation.assignedTo}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800">
                      <Phone className="h-5 w-5" />
                    </button>
                    <button className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800">
                      <Video className="h-5 w-5" />
                    </button>
                    <button className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800">
                      <Info className="h-5 w-5" />
                    </button>
                    <div className="relative">
                      <button className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800">
                        <MoreVertical className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6" style={{ height: 'calc(100vh - 380px)' }}>
                  <div className="space-y-4">
                    {selectedConversation.messages.map((message, index) => (
                      <div
                        key={message.id}
                        className={cn(
                          'flex gap-3',
                          message.role === 'customer' ? 'flex-row' : 'flex-row-reverse'
                        )}
                      >
                        <div className={cn(
                          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white text-xs font-semibold',
                          message.role === 'customer'
                            ? 'bg-gradient-to-br from-indigo-500 to-purple-600'
                            : message.role === 'ai'
                            ? 'bg-gradient-to-br from-emerald-500 to-teal-600'
                            : 'bg-slate-400'
                        )}>
                          {message.role === 'customer' ? (
                            selectedConversation.customerAvatar
                          ) : message.role === 'ai' ? (
                            <Bot className="h-4 w-4" />
                          ) : (
                            <User className="h-4 w-4" />
                          )}
                        </div>
                        <div className={cn(
                          'max-w-[70%] rounded-2xl px-4 py-3',
                          message.role === 'customer'
                            ? 'bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-zinc-100'
                            : message.role === 'ai'
                            ? 'bg-indigo-600 text-white'
                            : 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-zinc-100'
                        )}>
                          <p className="text-sm">{message.content}</p>
                          <div className={cn(
                            'mt-2 flex items-center gap-2 text-xs',
                            message.role === 'ai' ? 'text-indigo-200' : 'text-zinc-400'
                          )}>
                            <span>{formatMessageTime(message.timestamp)}</span>
                            {message.status && (
                              <span>
                                {message.status === 'read' ? (
                                  <CheckCheck className="h-3.5 w-3.5" />
                                ) : message.status === 'delivered' ? (
                                  <Check className="h-3.5 w-3.5" />
                                ) : (
                                  <Clock className="h-3.5 w-3.5" />
                                )}
                              </span>
                            )}
                            {message.sentiment !== undefined && (
                              <span className={cn(
                                'ml-1 rounded px-1 text-[10px]',
                                message.sentiment > 0.3 ? 'bg-green-500/20' :
                                message.sentiment < -0.3 ? 'bg-red-500/20' : 'bg-slate-500/20'
                              )}>
                                {message.sentiment > 0.3 ? '😊' : message.sentiment < -0.3 ? '😟' : '😐'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="flex items-center gap-2 border-y border-zinc-200 px-6 py-2 dark:border-zinc-800">
                  <button className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800">
                    <ThumbsUp className="h-3.5 w-3.5" />
                    Mark Helpful
                  </button>
                  <button className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800">
                    <Flag className="h-3.5 w-3.5" />
                    Flag
                  </button>
                  <button className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800">
                    <Archive className="h-3.5 w-3.5" />
                    Archive
                  </button>
                  <button className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete
                  </button>
                </div>

                {/* Message Input */}
                <div className="border-t border-zinc-200 p-4 dark:border-zinc-800">
                  <div className="flex items-end gap-3">
                    <button className="shrink-0 rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800">
                      <Paperclip className="h-5 w-5" />
                    </button>
                    <div className="flex-1 rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-2 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-800">
                      <textarea
                        value={messageInput}
                        onChange={(e) => setMessageInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSendMessage();
                          }
                        }}
                        placeholder="Type a message..."
                        rows={1}
                        className="w-full resize-none bg-transparent text-sm outline-none placeholder:text-zinc-400"
                      />
                    </div>
                    <button className="shrink-0 rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800">
                      <Smile className="h-5 w-5" />
                    </button>
                    <button
                      onClick={handleSendMessage}
                      disabled={!messageInput.trim()}
                      className="shrink-0 rounded-lg bg-indigo-600 p-2 text-white transition-colors hover:bg-indigo-700 disabled:opacity-50"
                    >
                      <Send className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex h-full flex-col items-center justify-center text-zinc-400">
                <MessageSquare className="mb-4 h-16 w-16" />
                <p className="text-lg font-medium text-zinc-500 dark:text-zinc-400">
                  Select a conversation
                </p>
                <p className="mt-1 text-sm text-zinc-400 dark:text-zinc-500">
                  Choose from the list to view messages
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return date.toLocaleDateString('en-US', { weekday: 'short' });
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
}

function formatMessageTime(dateString: string): string {
  return new Date(dateString).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  });
}
