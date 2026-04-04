'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import { useDashboard } from '@/contexts/DashboardContext';
import { FTEInstancesPanel } from '@/components/FTEInstancesPanel';
import { Bot, Plus, Settings2, Power, Activity, X, CheckCircle, AlertCircle } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8003';

export default function FTEsPage() {
  const { fteInstances, loading } = useDashboard();
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedFTE, setSelectedFTE] = useState<any>(null);
  const [viewingMetrics, setViewingMetrics] = useState<any>(null);
  const [actionStatus, setActionStatus] = useState<{type: 'success' | 'error', message: string} | null>(null);

  // Normalize FTE data with defaults for missing fields
  const normalizedFTEs = (Array.isArray(fteInstances) ? fteInstances : []).map((fte) => ({
    ...fte,
    status: fte.status ?? 'running',
    version: fte.version ?? '1.0.0',
    uptime_seconds: fte.uptime_seconds ?? 0,
    metrics: {
      messages_per_minute: fte.metrics?.messages_per_minute ?? 0,
      avg_latency_ms: fte.metrics?.avg_latency_ms ?? 0,
      error_rate: fte.metrics?.error_rate ?? 0,
      active_conversations: fte.metrics?.active_conversations ?? 0,
    },
  }));

  const handleDeployFTE = async (fteData: any) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/a2a/ftes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fteData),
      });
      
      if (response.ok) {
        setActionStatus({ type: 'success', message: `FTE "${fteData.name}" deployed successfully!` });
        setShowDeployModal(false);
        setTimeout(() => setActionStatus(null), 3000);
      } else {
        setActionStatus({ type: 'error', message: 'Failed to deploy FTE' });
      }
    } catch (error) {
      setActionStatus({ type: 'error', message: 'Connection error' });
    }
  };

  const handleStopFTE = async (fteId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/a2a/ftes/${fteId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setActionStatus({ type: 'success', message: 'FTE stopped successfully' });
        setTimeout(() => setActionStatus(null), 3000);
      }
    } catch (error) {
      setActionStatus({ type: 'error', message: 'Failed to stop FTE' });
    }
  };

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

  const runningCount = normalizedFTEs.filter((f) => f.status === 'running').length;
  const errorCount = normalizedFTEs.filter((f) => f.status === 'error').length;

  return (
    <>
      <Header title="FTE Instances" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Status Notification */}
          {actionStatus && (
            <div className={`flex items-center gap-3 rounded-lg p-4 ${
              actionStatus.type === 'success' 
                ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' 
                : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
            }`}>
              {actionStatus.type === 'success' ? (
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
              )}
              <p className={`text-sm font-medium ${
                actionStatus.type === 'success' ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'
              }`}>
                {actionStatus.message}
              </p>
            </div>
          )}

          {/* Header Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setShowDeployModal(true)}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                Deploy New FTE
              </button>
              <button 
                onClick={() => setShowConfigModal(true)}
                className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
              >
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
          {normalizedFTEs.length === 0 && (
            <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <Bot className="mx-auto h-16 w-16 text-zinc-300" />
              <h3 className="mt-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                No FTE Instances
              </h3>
              <p className="mt-2 text-zinc-500 dark:text-zinc-400">
                Deploy your first Digital FTE to get started
              </p>
              <button 
                onClick={() => setShowDeployModal(true)}
                className="mt-4 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 mx-auto"
              >
                <Plus className="h-4 w-4" />
                Deploy FTE
              </button>
            </div>
          )}

          {/* FTE Cards */}
          {normalizedFTEs.length > 0 && (
            <div className="grid gap-6 md:grid-cols-2">
              {normalizedFTEs.map((fte) => (
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
                      <button 
                        onClick={() => setViewingMetrics(fte)}
                        className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800"
                        title="View Metrics"
                      >
                        <Activity className="h-5 w-5" />
                      </button>
                      <button 
                        onClick={() => setSelectedFTE(fte)}
                        className="rounded-lg p-2 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:hover:bg-zinc-800"
                        title="Configure"
                      >
                        <Settings2 className="h-5 w-5" />
                      </button>
                      <button 
                        onClick={() => handleStopFTE(fte.id)}
                        className="rounded-lg p-2 text-red-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
                        title="Stop FTE"
                      >
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

      {/* Deploy FTE Modal */}
      {showDeployModal && (
        <DeployModal 
          onClose={() => setShowDeployModal(false)} 
          onDeploy={handleDeployFTE} 
        />
      )}

      {/* Configure Modal */}
      {selectedFTE && (
        <ConfigModal 
          fte={selectedFTE}
          onClose={() => setSelectedFTE(null)} 
        />
      )}

      {/* Metrics Modal */}
      {viewingMetrics && (
        <MetricsModal 
          fte={viewingMetrics}
          onClose={() => setViewingMetrics(null)} 
        />
      )}
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

function DeployModal({ onClose, onDeploy }: { onClose: () => void; onDeploy: (data: any) => void }) {
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    type: 'customer-success',
    version: '1.0.0',
    status: 'running',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onDeploy(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
          <X className="w-5 h-5" />
        </button>
        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Deploy New FTE</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">FTE ID</label>
            <input
              type="text"
              value={formData.id}
              onChange={(e) => setFormData({...formData, id: e.target.value})}
              placeholder="e.g., hr-support-fte-001"
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="e.g., HR Support FTE"
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Type</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({...formData, type: e.target.value})}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              <option value="customer-success">Customer Success</option>
              <option value="sales">Sales</option>
              <option value="technical-support">Technical Support</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Version</label>
            <input
              type="text"
              value={formData.version}
              onChange={(e) => setFormData({...formData, version: e.target.value})}
              placeholder="1.0.0"
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-700 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex gap-3 pt-4">
            <button type="button" onClick={onClose} className="flex-1 py-2.5 px-4 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700">
              Cancel
            </button>
            <button type="submit" className="flex-1 py-2.5 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700">
              Deploy
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ConfigModal({ fte, onClose }: { fte: any; onClose: () => void }) {
  const [config, setConfig] = useState({
    name: fte.name || '',
    type: fte.type || 'customer-success',
    version: fte.version || '1.0.0',
    maxConcurrent: fte.maxConcurrent || 100,
    rateLimit: fte.rateLimit || 1000,
    autoScale: fte.autoScale ?? true,
    notifications: fte.notifications ?? true,
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 1500);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-lg w-full p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
          <X className="w-5 h-5" />
        </button>
        
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900">
            <Settings2 className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">Configure: {fte.name}</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">FTE ID: {fte.id}</p>
          </div>
        </div>

        {saved && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
            <p className="text-sm text-green-800 dark:text-green-200">Configuration saved successfully!</p>
          </div>
        )}

        <div className="space-y-4">
          {/* Basic Info */}
          <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Basic Information</h4>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Name</label>
                <input
                  type="text"
                  value={config.name}
                  onChange={(e) => setConfig({...config, name: e.target.value})}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-600 px-3 py-2 text-sm outline-none focus:border-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Type</label>
                  <select
                    value={config.type}
                    onChange={(e) => setConfig({...config, type: e.target.value})}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-600 px-3 py-2 text-sm outline-none focus:border-blue-500"
                  >
                    <option value="customer-success">Customer Success</option>
                    <option value="sales">Sales</option>
                    <option value="technical-support">Technical Support</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Version</label>
                  <input
                    type="text"
                    value={config.version}
                    onChange={(e) => setConfig({...config, version: e.target.value})}
                    className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-600 px-3 py-2 text-sm outline-none focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Performance Settings */}
          <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Performance Settings</h4>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Max Concurrent Conversations</label>
                <input
                  type="number"
                  value={config.maxConcurrent}
                  onChange={(e) => setConfig({...config, maxConcurrent: parseInt(e.target.value) || 0})}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-600 px-3 py-2 text-sm outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">Rate Limit (messages/min)</label>
                <input
                  type="number"
                  value={config.rateLimit}
                  onChange={(e) => setConfig({...config, rateLimit: parseInt(e.target.value) || 0})}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-600 px-3 py-2 text-sm outline-none focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Toggles */}
          <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Features</h4>
            <div className="space-y-3">
              <ToggleSetting 
                label="Auto-scaling" 
                description="Automatically scale based on load"
                checked={config.autoScale} 
                onChange={(v) => setConfig({...config, autoScale: v})} 
              />
              <ToggleSetting 
                label="Notifications" 
                description="Send alerts for errors and SLA breaches"
                checked={config.notifications} 
                onChange={(v) => setConfig({...config, notifications: v})} 
              />
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={onClose} className="flex-1 py-2.5 px-4 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700">
              Cancel
            </button>
            <button onClick={handleSave} className="flex-1 py-2.5 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700">
              Save Changes
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

function MetricsModal({ fte, onClose }: { fte: any; onClose: () => void }) {
  const metrics = fte.metrics || {};
  const errorRate = (metrics.error_rate || 0) * 100;
  const healthScore = Math.max(0, 100 - errorRate * 2 - (metrics.avg_latency_ms > 300 ? 20 : 0));
  
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-lg w-full p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
          <X className="w-5 h-5" />
        </button>
        
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900">
            <Activity className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">Metrics: {fte.name}</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">Real-time performance data</p>
          </div>
        </div>

        {/* Health Score */}
        <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Health Score</span>
            <span className={`text-2xl font-bold ${healthScore >= 80 ? 'text-green-600' : healthScore >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
              {healthScore.toFixed(0)}%
            </span>
          </div>
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all ${healthScore >= 80 ? 'bg-green-500' : healthScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
              style={{ width: `${healthScore}%` }}
            />
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <MetricDetail label="Messages/min" value={metrics.messages_per_minute?.toFixed(1) || '0'} icon="📨" />
          <MetricDetail label="Avg Latency" value={`${Math.round(metrics.avg_latency_ms || 0)}ms`} icon="⚡" />
          <MetricDetail label="Error Rate" value={`${errorRate.toFixed(2)}%`} icon="❌" highlight={errorRate > 5} />
          <MetricDetail label="Active Conversations" value={metrics.active_conversations?.toString() || '0'} icon="💬" />
          <MetricDetail label="Uptime" value={`${Math.floor((fte.uptime_seconds || 0) / 86400)}d ${Math.floor(((fte.uptime_seconds || 0) % 86400) / 3600)}h`} icon="⏱️" />
          <MetricDetail label="Status" value={fte.status || 'unknown'} icon={fte.status === 'running' ? '✅' : '⚠️'} />
        </div>

        {/* Performance Insights */}
        <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg mb-6">
          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Performance Insights</h4>
          <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-400">
            {metrics.messages_per_minute > 15 && <li>🔥 High throughput: Processing {metrics.messages_per_minute.toFixed(1)} msg/min</li>}
            {metrics.avg_latency_ms < 200 && <li>⚡ Fast response time: {Math.round(metrics.avg_latency_ms)}ms average</li>}
            {metrics.avg_latency_ms > 300 && <li>⚠️ High latency detected: {Math.round(metrics.avg_latency_ms)}ms</li>}
            {errorRate < 2 && <li>✅ Excellent error rate: {errorRate.toFixed(2)}%</li>}
            {errorRate > 5 && <li>❌ High error rate: {errorRate.toFixed(2)}% - needs attention</li>}
            {metrics.active_conversations > 10 && <li>📊 Heavy load: {metrics.active_conversations} active conversations</li>}
          </ul>
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 py-2.5 px-4 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function MetricDetail({ label, value, icon, highlight = false }: { label: string; value: string; icon: string; highlight?: boolean }) {
  return (
    <div className="p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className="text-xs text-slate-500 dark:text-slate-400">{label}</span>
      </div>
      <p className={`text-lg font-semibold ${highlight ? 'text-red-600 dark:text-red-400' : 'text-slate-900 dark:text-slate-100'}`}>
        {value}
      </p>
    </div>
  );
}
