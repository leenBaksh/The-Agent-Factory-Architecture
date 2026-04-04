'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import { useDashboard } from '@/contexts/DashboardContext';
import { SLABreachesPanel } from '@/components/SLABreachesPanel';
import { AlertTriangle, CheckCircle, AlertCircle, TrendingUp, TrendingDown, RefreshCw, Settings, Download, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function SLAMonitorPage() {
  const { metrics, slaBreaches, loading, refreshMetrics } = useDashboard();
  const [refreshing, setRefreshing] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refreshMetrics();
    setTimeout(() => setRefreshing(false), 1000);
  };

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

  // Calculate trend
  const calculateTrend = () => {
    if (!metrics?.metrics_history || metrics.metrics_history.length < 2) return null;

    const history = metrics.metrics_history;
    const current = history[history.length - 1]?.sla_compliance_rate || 0;
    const previous = history[history.length - 2]?.sla_compliance_rate || 0;
    const change = current - previous;
    const changePercent = previous > 0 ? ((change / previous) * 100).toFixed(1) : '0';

    return {
      change: Math.abs(parseFloat(changePercent)),
      trendUp: change >= 0,
      current,
      previous,
    };
  };

  const trend = calculateTrend();

  return (
    <>
      <Header title="SLA Monitor" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Success Banner */}
          {saveSuccess && (
            <div className="flex items-center gap-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4 animate-in slide-in-from-top-2 duration-300">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" />
              <p className="text-sm font-medium text-green-800 dark:text-green-200 flex-1">
                SLA settings saved successfully!
              </p>
              <button 
                onClick={() => setSaveSuccess(false)}
                className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Header Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button 
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 disabled:opacity-50"
              >
                <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
                {refreshing ? 'Refreshing...' : 'Refresh'}
              </button>
              <button 
                onClick={() => setShowConfigModal(true)}
                className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
              >
                <Settings className="h-4 w-4" />
                SLA Settings
              </button>
              <button 
                onClick={() => alert('Exporting SLA report...')}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Download className="h-4 w-4" />
                Export Report
              </button>
            </div>
          </div>

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
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  SLA Compliance Trend
                </h3>
                {trend && (
                  <div className="flex items-center gap-2 mt-1">
                    <span className={cn(
                      'inline-flex items-center gap-1 text-sm font-semibold',
                      trend.trendUp ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                    )}>
                      {trend.trendUp ? (
                        <TrendingUp className="w-4 h-4" />
                      ) : (
                        <TrendingDown className="w-4 h-4" />
                      )}
                      {trend.change}%
                    </span>
                    <span className="text-sm text-zinc-500 dark:text-zinc-400">vs previous period</span>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gradient-to-r from-green-500 to-emerald-500"></div>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">≥95%</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gradient-to-r from-amber-500 to-orange-500"></div>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">90-95%</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gradient-to-r from-red-500 to-rose-500"></div>
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">&lt;90%</span>
                </div>
              </div>
            </div>

            <div className="h-64">
              {metrics?.metrics_history && (
                <div className="flex h-full items-end justify-between gap-2">
                  {metrics.metrics_history.map((day, index) => {
                    const complianceRate = day.sla_compliance_rate || 0;
                    const height = Math.max(complianceRate, 0);
                    const isLast = index === metrics.metrics_history.length - 1;
                    const isGood = complianceRate >= 95;
                    const isWarning = complianceRate >= 90 && complianceRate < 95;

                    return (
                      <div key={index} className="flex flex-1 flex-col items-center gap-2 group">
                        <div className="relative w-full">
                          {/* Tooltip */}
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 dark:bg-slate-700 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10 shadow-lg">
                            <div className="font-semibold">{complianceRate.toFixed(1)}%</div>
                            <div className="text-slate-300">{day.date}</div>
                            <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1">
                              <div className="border-4 border-transparent border-t-slate-900 dark:border-t-slate-700"></div>
                            </div>
                          </div>
                          {/* Bar */}
                          <div
                            className={`w-full rounded-t-lg transition-all duration-500 ease-out ${
                              isGood
                                ? 'bg-gradient-to-t from-green-600 via-green-500 to-emerald-400'
                                : isWarning
                                ? 'bg-gradient-to-t from-amber-600 via-amber-500 to-orange-400'
                                : 'bg-gradient-to-t from-red-600 via-red-500 to-rose-400'
                            } ${isLast ? 'ring-2 ring-indigo-500 ring-offset-2 dark:ring-offset-slate-900' : 'hover:opacity-80'}`}
                            style={{ height: `${height}%` }}
                          />
                        </div>
                        <span className="text-xs text-zinc-500 dark:text-zinc-400 font-medium transform -rotate-45 origin-top text-right w-full">
                          {day.date.slice(5)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* SLA Settings Modal */}
      {showConfigModal && (
        <SLASettingsModal 
          onClose={() => setShowConfigModal(false)}
          onSaveSuccess={() => {
            setSaveSuccess(true);
            setTimeout(() => setSaveSuccess(false), 4000);
          }}
        />
      )}
    </>
  );
}

function SLASettingsModal({ onClose, onSaveSuccess }: { onClose: () => void; onSaveSuccess: () => void }) {
  const [settings, setSettings] = useState({
    complianceTarget: 95,
    firstResponseTarget: 5,
    resolutionTarget: 60,
    alertThreshold: 90,
    emailNotifications: true,
    slackNotifications: true,
  });

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-lg w-full p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
          <X className="w-5 h-5" />
        </button>
        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">SLA Settings</h3>
        <div className="space-y-4">
          <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Targets</h4>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Compliance Target (%)</label>
                <input
                  type="number"
                  value={settings.complianceTarget}
                  onChange={(e) => setSettings({...settings, complianceTarget: parseInt(e.target.value) || 0})}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-600 px-3 py-2 text-sm outline-none focus:border-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">First Response (min)</label>
                  <input
                    type="number"
                    value={settings.firstResponseTarget}
                    onChange={(e) => setSettings({...settings, firstResponseTarget: parseInt(e.target.value) || 0})}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-600 px-3 py-2 text-sm outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Resolution Time (min)</label>
                  <input
                    type="number"
                    value={settings.resolutionTarget}
                    onChange={(e) => setSettings({...settings, resolutionTarget: parseInt(e.target.value) || 0})}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-600 px-3 py-2 text-sm outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Alert Threshold (%)</label>
                <input
                  type="number"
                  value={settings.alertThreshold}
                  onChange={(e) => setSettings({...settings, alertThreshold: parseInt(e.target.value) || 0})}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-600 px-3 py-2 text-sm outline-none focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Notifications</h4>
            <div className="space-y-3">
              <ToggleSetting 
                label="Email Notifications" 
                description="Send SLA breach alerts via email"
                checked={settings.emailNotifications} 
                onChange={(v) => setSettings({...settings, emailNotifications: v})} 
              />
              <ToggleSetting 
                label="Slack Notifications" 
                description="Send alerts to Slack channel"
                checked={settings.slackNotifications} 
                onChange={(v) => setSettings({...settings, slackNotifications: v})} 
              />
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={onClose} className="flex-1 py-2.5 px-4 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700">
              Cancel
            </button>
            <button onClick={() => { onSaveSuccess(); onClose(); }} className="flex-1 py-2.5 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700">
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ToggleSetting({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{label}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">{description}</p>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 rounded-full transition-colors ${checked ? 'bg-blue-600' : 'bg-slate-300 dark:bg-slate-600'}`}
      >
        <span className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-transform ${checked ? 'left-6' : 'left-1'}`} />
      </button>
    </div>
  );
}
