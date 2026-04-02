'use client';

import React from 'react';
import { Header } from '@/components/Header';
import { Shield } from 'lucide-react';

export default function GuardrailsPage() {
  return (
    <>
      <Header title="Guardrails" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <Shield className="mx-auto h-16 w-16 text-zinc-300" />
            <h3 className="mt-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
              Guardrails Configuration
            </h3>
            <p className="mt-2 text-zinc-500 dark:text-zinc-400">
              PII detection, keyword escalation, and sentiment thresholds
            </p>
          </div>
        </div>
      </main>
    </>
  );
}
