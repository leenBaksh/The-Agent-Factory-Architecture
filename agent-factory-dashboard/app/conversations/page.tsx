'use client';

import React from 'react';
import { Header } from '@/components/Header';
import { MessageSquare } from 'lucide-react';

export default function ConversationsPage() {
  return (
    <>
      <Header title="Conversations" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <MessageSquare className="mx-auto h-16 w-16 text-zinc-300" />
            <h3 className="mt-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
              Conversations View
            </h3>
            <p className="mt-2 text-zinc-500 dark:text-zinc-400">
              Real-time conversation monitoring coming soon
            </p>
          </div>
        </div>
      </main>
    </>
  );
}
