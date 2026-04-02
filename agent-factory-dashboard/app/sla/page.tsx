'use client';

import React from 'react';
import { Header } from '@/components/Header';
import { useDashboard } from '@/contexts/DashboardContext';
import { SLABreachesPanel } from '@/components/SLABreachesPanel';
import { AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

export default function SLAMonitorPage() {
  const { metrics, slaBreaches, loading } = useDashboard();

  const slaMetrics = [
    {
      label: 'SLA Compliance Rate',
      value: `${metrics?.summary.sla_compliance_rate.toFixed(1) || 0}%`,
      target: 'Target: 95%',
      status: (metrics?.summary.sla_compliance_rate || 0) >= 95 ? 'good' : 'warning',
    },
    {
      label: 'Avg First Response',
      value: `${(metrics?.metrics_history[0]?.avg_first_response_time_minutes || 0).toFixed(0)} min`,
      target: 'Target: < 5 min',
      status: 'good',
    },
    {
      label: 'Avg Resolution Time',
      value: `${(metrics?.metrics_history[0]?.avg_resolution_time_minutes || 0).toFixed(0)} min`,
      target: 'Target: < 60 min',
      status: 'good',
    },
    {
      label: 'Active Breaches',
      value: slaBreaches.filter((b) => b.status === 'active').length.toString(),
      target: 'Target: 0',
      status: slaBreaches.filter((b) => b.status === 'active').length === 0 ? 'good' : 'critical',
    },
  ];

  return (
    <>
      <Header title="SLA Monitor" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* SLA Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {slaMetrics.map((metric) => (
              <div
                key={metric.label}
                className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-zinc-500 dark:text-zinc-400">
                      {metric.label}
                    </p>
                    <p className="mt-2 text-3xl font-semibold text-zinc-900 dark:text-zinc-100">
                      {metric.value}
                    </p>
                    <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                      {metric.target}
                    </p>
                  </div>
                  <div
                    className={`rounded-lg p-3 ${
                      metric.status === 'good'
                        ? 'bg-green-100 dark:bg-green-900'
                        : metric.status === 'warning'
                        ? 'bg-amber-100 dark:bg-amber-900'
                        : 'bg-red-100 dark:bg-red-900'
                    }`}
                  >
                    {metric.status === 'good' ? (
                      <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
                    ) : metric.status === 'warning' ? (
                      <AlertTriangle className="h-6 w-6 text-amber-600 dark:text-amber-400" />
                    ) : (
                      <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* SLA Breaches Panel */}
          <SLABreachesPanel />

          {/* SLA History Chart */}
          <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <h3 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
              SLA Compliance Trend
            </h3>
            <div className="h-64">
              {metrics?.metrics_history && (
                <div className="flex h-full items-end justify-between gap-2">
                  {metrics.metrics_history.map((day, index) => {
                    const complianceRate =
                      100 - (day.sla_breach_count / Math.max(day.total_tickets, 1)) * 100;
                    const height = Math.max(complianceRate, 0);

                    return (
                      <div key={index} className="flex flex-1 flex-col items-center gap-2">
                        <div
                          className={`w-full rounded-t ${
                            height >= 95
                              ? 'bg-green-500'
                              : height >= 90
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                          }`}
                          style={{ height: `${height}%` }}
                        />
                        <span className="text-xs text-zinc-500">{day.date.slice(5)}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
