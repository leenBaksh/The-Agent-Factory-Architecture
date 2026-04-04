'use client';

import React, { useState } from 'react';
import { Header } from '@/components/Header';
import {
  Shield,
  Eye,
  AlertTriangle,
  Heart,
  Save,
  Plus,
  Trash2,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Guardrails configuration types
interface PIIRule {
  id: string;
  name: string;
  pattern: string;
  enabled: boolean;
  action: 'redact' | 'flag' | 'block';
}

interface KeywordRule {
  id: string;
  keywords: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
}

interface SentimentThreshold {
  type: 'negative' | 'positive';
  threshold: number;
  action: 'notify' | 'escalate' | 'log';
}

export default function GuardrailsPage() {
  // PII Detection Rules
  const [piiRules, setPiiRules] = useState<PIIRule[]>([
    { id: '1', name: 'Email Addresses', pattern: '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b', enabled: true, action: 'redact' },
    { id: '2', name: 'Phone Numbers', pattern: '\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b', enabled: true, action: 'redact' },
    { id: '3', name: 'Credit Card Numbers', pattern: '\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b', enabled: true, action: 'block' },
    { id: '4', name: 'SSN', pattern: '\\b\\d{3}-\\d{2}-\\d{4}\\b', enabled: true, action: 'block' },
    { id: '5', name: 'IP Addresses', pattern: '\\b\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\b', enabled: false, action: 'flag' },
  ]);

  // Keyword Escalation Rules
  const [keywordRules, setKeywordRules] = useState<KeywordRule[]>([
    { id: '1', keywords: ['lawsuit', 'sue', 'legal action', 'attorney', 'lawyer'], priority: 'critical', enabled: true },
    { id: '2', keywords: ['cancel', 'refund', 'chargeback', 'dispute'], priority: 'high', enabled: true },
    { id: '3', keywords: ['unhappy', 'disappointed', 'frustrated', 'angry'], priority: 'medium', enabled: true },
    { id: '4', keywords: ['supervisor', 'manager', 'speak to someone'], priority: 'high', enabled: true },
  ]);

  // Sentiment Thresholds
  const [sentimentThresholds, setSentimentThresholds] = useState<SentimentThreshold[]>([
    { type: 'negative', threshold: -0.7, action: 'escalate' },
    { type: 'negative', threshold: -0.4, action: 'notify' },
    { type: 'positive', threshold: 0.8, action: 'log' },
  ]);

  // Toggle states
  const [guardrailsEnabled, setGuardrailsEnabled] = useState(true);
  const [autoEscalationEnabled, setAutoEscalationEnabled] = useState(true);

  const togglePIIRule = (id: string) => {
    setPiiRules(piiRules.map(rule =>
      rule.id === id ? { ...rule, enabled: !rule.enabled } : rule
    ));
  };

  const updatePIIAction = (id: string, action: 'redact' | 'flag' | 'block') => {
    setPiiRules(piiRules.map(rule =>
      rule.id === id ? { ...rule, action } : rule
    ));
  };

  const deletePIIRule = (id: string) => {
    setPiiRules(piiRules.filter(rule => rule.id !== id));
  };

  const addPIIRule = () => {
    const newRule: PIIRule = {
      id: Date.now().toString(),
      name: 'New Rule',
      pattern: '',
      enabled: true,
      action: 'flag',
    };
    setPiiRules([...piiRules, newRule]);
  };

  const toggleKeywordRule = (id: string) => {
    setKeywordRules(keywordRules.map(rule =>
      rule.id === id ? { ...rule, enabled: !rule.enabled } : rule
    ));
  };

  const updateKeywordPriority = (id: string, priority: 'low' | 'medium' | 'high' | 'critical') => {
    setKeywordRules(keywordRules.map(rule =>
      rule.id === id ? { ...rule, priority } : rule
    ));
  };

  const deleteKeywordRule = (id: string) => {
    setKeywordRules(keywordRules.filter(rule => rule.id !== id));
  };

  const addKeywordRule = () => {
    const newRule: KeywordRule = {
      id: Date.now().toString(),
      keywords: [],
      priority: 'medium',
      enabled: true,
    };
    setKeywordRules([...keywordRules, newRule]);
  };

  const updateSentimentThreshold = (index: number, field: keyof SentimentThreshold, value: number | string) => {
    const updated = [...sentimentThresholds];
    updated[index] = { ...updated[index], [field]: value };
    setSentimentThresholds(updated);
  };

  const addSentimentThreshold = () => {
    setSentimentThresholds([...sentimentThresholds, { type: 'negative', threshold: -0.5, action: 'notify' }]);
  };

  const deleteSentimentThreshold = (index: number) => {
    setSentimentThresholds(sentimentThresholds.filter((_, i) => i !== index));
  };

  const priorityColors: Record<string, string> = {
    low: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200',
    medium: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    high: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
    critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };

  const actionColors: Record<string, string> = {
    redact: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    flag: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
    block: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    notify: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    escalate: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    log: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  };

  return (
    <>
      <Header title="Guardrails" />
      <main className="flex-1 overflow-y-auto bg-zinc-50 p-6 dark:bg-zinc-950">
        <div className="mx-auto max-w-5xl space-y-6">
          {/* Header Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                  Guardrails Configuration
                </h2>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  PII detection, keyword escalation, and sentiment thresholds
                </p>
              </div>
            </div>
            <button className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              <Save className="h-4 w-4" />
              Save Configuration
            </button>
          </div>

          {/* Global Toggles */}
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
              Global Settings
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-zinc-900 dark:text-zinc-100">Guardrails Enabled</p>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">
                    Enable or disable all guardrail protections
                  </p>
                </div>
                <button
                  onClick={() => setGuardrailsEnabled(!guardrailsEnabled)}
                  className="relative"
                >
                  {guardrailsEnabled ? (
                    <ToggleRight className="h-8 w-8 text-green-600" />
                  ) : (
                    <ToggleLeft className="h-8 w-8 text-zinc-400" />
                  )}
                </button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-zinc-900 dark:text-zinc-100">Auto Escalation</p>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">
                    Automatically escalate messages matching critical keywords
                  </p>
                </div>
                <button
                  onClick={() => setAutoEscalationEnabled(!autoEscalationEnabled)}
                  className="relative"
                >
                  {autoEscalationEnabled ? (
                    <ToggleRight className="h-8 w-8 text-green-600" />
                  ) : (
                    <ToggleLeft className="h-8 w-8 text-zinc-400" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* PII Detection */}
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Eye className="h-5 w-5 text-indigo-600" />
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  PII Detection Rules
                </h3>
              </div>
              <button
                onClick={addPIIRule}
                className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700"
              >
                <Plus className="h-4 w-4" />
                Add Rule
              </button>
            </div>
            <div className="space-y-3">
              {piiRules.map((rule) => (
                <div
                  key={rule.id}
                  className={cn(
                    'flex items-center justify-between rounded-lg border p-4',
                    rule.enabled
                      ? 'border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-800'
                      : 'border-zinc-100 bg-zinc-50 opacity-60 dark:border-zinc-800 dark:bg-zinc-900'
                  )}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-zinc-900 dark:text-zinc-100">
                        {rule.name}
                      </span>
                      <span className={cn('px-2 py-0.5 text-xs rounded-full', actionColors[rule.action])}>
                        {rule.action}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 font-mono">
                      {rule.pattern || 'No pattern defined'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={rule.action}
                      onChange={(e) => updatePIIAction(rule.id, e.target.value as 'redact' | 'flag' | 'block')}
                      className="text-sm border border-zinc-200 rounded-md px-2 py-1 dark:border-zinc-700 dark:bg-zinc-800"
                    >
                      <option value="redact">Redact</option>
                      <option value="flag">Flag</option>
                      <option value="block">Block</option>
                    </select>
                    <button
                      onClick={() => togglePIIRule(rule.id)}
                      className="text-zinc-400 hover:text-zinc-600"
                    >
                      {rule.enabled ? (
                        <ToggleRight className="h-6 w-6 text-green-600" />
                      ) : (
                        <ToggleLeft className="h-6 w-6 text-zinc-400" />
                      )}
                    </button>
                    <button
                      onClick={() => deletePIIRule(rule.id)}
                      className="text-zinc-400 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Keyword Escalation */}
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  Keyword Escalation Rules
                </h3>
              </div>
              <button
                onClick={addKeywordRule}
                className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700"
              >
                <Plus className="h-4 w-4" />
                Add Rule
              </button>
            </div>
            <div className="space-y-3">
              {keywordRules.map((rule) => (
                <div
                  key={rule.id}
                  className={cn(
                    'flex items-center justify-between rounded-lg border p-4',
                    rule.enabled
                      ? 'border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-800'
                      : 'border-zinc-100 bg-zinc-50 opacity-60 dark:border-zinc-800 dark:bg-zinc-900'
                  )}
                >
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {rule.keywords.map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 text-xs rounded-md bg-zinc-100 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300"
                        >
                          {keyword}
                        </span>
                      ))}
                      {rule.keywords.length === 0 && (
                        <span className="text-sm text-zinc-400">No keywords defined</span>
                      )}
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="text-xs text-zinc-500">Priority:</span>
                      <span className={cn('px-2 py-0.5 text-xs rounded-full', priorityColors[rule.priority])}>
                        {rule.priority}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={rule.priority}
                      onChange={(e) => updateKeywordPriority(rule.id, e.target.value as 'low' | 'medium' | 'high' | 'critical')}
                      className="text-sm border border-zinc-200 rounded-md px-2 py-1 dark:border-zinc-700 dark:bg-zinc-800"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                    <button
                      onClick={() => toggleKeywordRule(rule.id)}
                      className="text-zinc-400 hover:text-zinc-600"
                    >
                      {rule.enabled ? (
                        <ToggleRight className="h-6 w-6 text-green-600" />
                      ) : (
                        <ToggleLeft className="h-6 w-6 text-zinc-400" />
                      )}
                    </button>
                    <button
                      onClick={() => deleteKeywordRule(rule.id)}
                      className="text-zinc-400 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sentiment Thresholds */}
          <div className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Heart className="h-5 w-5 text-rose-600" />
                <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                  Sentiment Thresholds
                </h3>
              </div>
              <button
                onClick={addSentimentThreshold}
                className="flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700"
              >
                <Plus className="h-4 w-4" />
                Add Threshold
              </button>
            </div>
            <div className="space-y-3">
              {sentimentThresholds.map((threshold, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-800"
                >
                  <div className="flex items-center gap-4">
                    <span
                      className={cn(
                        'px-3 py-1 text-sm font-medium rounded-full',
                        threshold.type === 'negative'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      )}
                    >
                      {threshold.type === 'negative' ? '😟 Negative' : '😊 Positive'}
                    </span>
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        step="0.1"
                        min="-1"
                        max="1"
                        value={threshold.threshold}
                        onChange={(e) => updateSentimentThreshold(index, 'threshold', parseFloat(e.target.value))}
                        className="w-20 text-sm border border-zinc-200 rounded-md px-2 py-1 dark:border-zinc-700 dark:bg-zinc-900"
                      />
                      <span className="text-sm text-zinc-500">threshold</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={threshold.action}
                      onChange={(e) => updateSentimentThreshold(index, 'action', e.target.value)}
                      className="text-sm border border-zinc-200 rounded-md px-2 py-1 dark:border-zinc-700 dark:bg-zinc-800"
                    >
                      <option value="notify">Notify</option>
                      <option value="escalate">Escalate</option>
                      <option value="log">Log Only</option>
                    </select>
                    <span className={cn('px-2 py-0.5 text-xs rounded-full', actionColors[threshold.action])}>
                      {threshold.action}
                    </span>
                    <button
                      onClick={() => deleteSentimentThreshold(index)}
                      className="text-zinc-400 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Sentiment Scale Visualization */}
            <div className="mt-6 p-4 rounded-lg bg-gradient-to-r from-red-50 via-zinc-50 to-green-50 dark:from-red-900/20 dark:via-zinc-800 dark:to-green-900/20">
              <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-3">
                Sentiment Scale Reference
              </p>
              <div className="relative h-4 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500">
                {sentimentThresholds.map((threshold, index) => (
                  <div
                    key={index}
                    className="absolute top-0 h-full w-0.5 bg-white"
                    style={{ left: `${((threshold.threshold + 1) / 2) * 100}%` }}
                  >
                    <div className="absolute -top-8 -translate-x-1/2 text-xs font-medium text-zinc-700 dark:text-zinc-300 whitespace-nowrap">
                      {threshold.action} ({threshold.threshold})
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex justify-between mt-2 text-xs text-zinc-500">
                <span>-1.0 (Very Negative)</span>
                <span>0.0 (Neutral)</span>
                <span>1.0 (Very Positive)</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
