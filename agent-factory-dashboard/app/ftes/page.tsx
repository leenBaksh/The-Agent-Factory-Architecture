'use client';

import React from 'react';
import { Header } from '@/components/Header';
import { useDashboard } from '@/contexts/DashboardContext';
import { FTEInstancesPanel } from '@/components/FTEInstancesPanel';
import { Bot, Plus, Settings2, Power, Activity } from 'lucide-react';

export default function FTEsPage() {
  const { fteInstances, loading } = useDashboard();

  if (loading) {
    return (
      <>
        <Header title="FTE Instances" />
        <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
          <div className="mx-auto max-w-7xl">
            <div className="animate-pulse space-y-4">
              <div className="h-10 w-full bg-zinc-200 dark:bg-zinc-800 rounded-lg" />
              <div className="grid gap-6 md:grid-cols-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-48 bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
                ))}
              </div>
            </div>
          </div>
        </main>
      </>
    );
  }

  const runningCount = fteInstances.filter((f) => f.status === 'running').length;
  const errorCount = fteInstances.filter((f) => f.status === 'error').length;

  return (
    <>
      <Header title="FTE Instances" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Header Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                <Plus className="h-4 w-4" />
                Deploy New FTE
              </button>
              <button className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
                <Settings2 className="h-4 w-4" />
                Configure
              </button>
            </div>
            <div className="flex items-center gap-4 text-sm text-zinc-500">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                {runningCount} running
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                {errorCount} errors
              </span>
            </div>
          </div>

          {/* Empty State */}
          {fteInstances.length === 0 && (
            <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <Bot className="mx-auto h-16 w-16 text-zinc-300" />
              <h3 className="mt-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                No FTE Instances
              </h3>
              <p className="mt-2 text-zinc-500 dark:text-zinc-400">
                Deploy your first Digital FTE to get started
              </p>
            </div>
          )}

          {/* FTE Cards */}
          {fteInstances.length > 0 && (
            <div className="grid gap-6 md:grid-cols-2">
              {fteInstances.map((fte) => (
                <div
                  key={fte.id}
                  className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900">
                        <Bot className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                            {fte.name}
                          </h3>
                          <span
                            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                              fte.status === 'running'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                : fte.status === 'error'
                                ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                : 'bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200'
                            }`}
                          >
                            {fte.status}
                          </span>
                        </div>
                        <p className="text-sm text-zinc-500 dark:text-zinc-400">
                          {fte.type} • v{fte.version}
                        </p>
                        <p className="mt-1 text-xs text-zinc-400">
                          Uptime: {Math.floor(fte.uptime_seconds / 86400)}d{' '}
                          {Math.floor((fte.uptime_seconds % 86400) / 3600)}h
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800">
                        <Activity className="h-5 w-5" />
                      </button>
                      <button className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800">
                        <Settings2 className="h-5 w-5" />
                      </button>
                      <button className="rounded-lg p-2 text-red-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20">
                        <Power className="h-5 w-5" />
                      </button>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="mt-6 grid grid-cols-4 gap-4">
                    <MetricCard
                      label="Messages/min"
                      value={fte.metrics.messages_per_minute.toFixed(1)}
                    />
                    <MetricCard
                      label="Avg Latency"
                      value={`${Math.round(fte.metrics.avg_latency_ms)}ms`}
                    />
                    <MetricCard
                      label="Error Rate"
                      value={`${(fte.metrics.error_rate * 100).toFixed(2)}%`}
                      highlight={fte.metrics.error_rate > 0.05}
                    />
                    <MetricCard
                      label="Active Conv."
                      value={fte.metrics.active_conversations.toString()}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  );
}

function MetricCard({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="rounded-lg bg-zinc-50 p-4 dark:bg-zinc-800">
      <p className="text-xs text-zinc-500 dark:text-zinc-400">{label}</p>
      <p
        className={`mt-1 text-xl font-semibold ${
          highlight
            ? 'text-red-600 dark:text-red-400'
            : 'text-zinc-900 dark:text-zinc-100'
        }`}
      >
        {value}
      </p>
    </div>
  );
}
