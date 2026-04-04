'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { DashboardMetrics, Ticket, FTEInstance, SLABreach } from '@/types';

interface DashboardContextType {
  metrics: DashboardMetrics | null;
  fteInstances: FTEInstance[];
  slaBreaches: SLABreach[];
  loading: boolean;
  lastUpdated: Date | null;
  error: string | null;
  refreshMetrics: () => Promise<void>;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
}

const DashboardContext = createContext<DashboardContextType>({
  metrics: null,
  fteInstances: [],
  slaBreaches: [],
  loading: true,
  lastUpdated: null,
  error: null,
  refreshMetrics: async () => {},
  searchQuery: '',
  setSearchQuery: () => {},
});

// API base URL from environment or default
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003';
const FTE_API_URL = 'http://localhost:8003';

// Fetch metrics from real API
async function fetchMetrics(): Promise<DashboardMetrics> {
  const response = await fetch(`${API_BASE_URL}/metrics/dashboard`, {
    signal: AbortSignal.timeout(5000) // 5 second timeout
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch metrics: ${response.status}`);
  }
  const text = await response.text();
  if (!text) {
    throw new Error('Empty response from metrics API');
  }
  const data = JSON.parse(text);
  // Ensure we return a valid metrics structure
  return {
    summary: data.summary || {
      total_tickets: 0,
      open_tickets: 0,
      avg_resolution_time_hours: 0,
      avg_satisfaction_rating: 0,
      sla_compliance_rate: 0,
      total_conversations_24h: 0,
    },
    tickets_by_status: data.tickets_by_status || { open: 0, in_progress: 0, waiting_customer: 0, resolved: 0, closed: 0 },
    tickets_by_channel: data.tickets_by_channel || { web: 0, gmail: 0, whatsapp: 0 },
    recent_tickets: Array.isArray(data.recent_tickets) ? data.recent_tickets : [],
    sla_breaches: Array.isArray(data.sla_breaches) ? data.sla_breaches : [],
    metrics_history: Array.isArray(data.metrics_history) ? data.metrics_history : [],
  };
}

// Fetch FTE instances from real API
async function fetchFTEInstances(): Promise<FTEInstance[]> {
  const response = await fetch(`${API_BASE_URL}/api/a2a/ftes`, {
    signal: AbortSignal.timeout(5000) // 5 second timeout
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch FTE instances: ${response.status}`);
  }
  const text = await response.text();
  if (!text) {
    throw new Error('Empty response from FTE API');
  }
  const data = JSON.parse(text);
  // Ensure we always return an array
  return Array.isArray(data) ? data : [];
}

// Fetch SLA breaches from real API
async function fetchSLABreaches(): Promise<SLABreach[]> {
  const response = await fetch(`${API_BASE_URL}/metrics/sla-breaches`, {
    signal: AbortSignal.timeout(5000)
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch SLA breaches: ${response.status}`);
  }
  const text = await response.text();
  if (!text) {
    throw new Error('Empty response from SLA API');
  }
  const data = JSON.parse(text);
  // Ensure we always return an array
  return Array.isArray(data) ? data : [];
}

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [fteInstances, setFteInstances] = useState<FTEInstance[]>([]);
  const [slaBreaches, setSlaBreaches] = useState<SLABreach[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const refreshMetricsRef = React.useRef<() => Promise<void>>(() => Promise.resolve());

  const refreshMetrics = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [metricsData, fteData, slaData] = await Promise.allSettled([
        fetchMetrics(),
        fetchFTEInstances(),
        fetchSLABreaches(),
      ]);
      
      // Handle metrics result
      if (metricsData.status === 'fulfilled') {
        setMetrics(metricsData.value);
      } else {
        console.warn('Failed to fetch metrics:', metricsData.reason);
      }
      
      // Handle FTE instances result
      if (fteData.status === 'fulfilled') {
        setFteInstances(fteData.value);
      } else {
        console.warn('Failed to fetch FTE instances:', fteData.reason);
      }
      
      // Handle SLA breaches result
      if (slaData.status === 'fulfilled') {
        setSlaBreaches(slaData.value);
      } else {
        console.warn('Failed to fetch SLA breaches:', slaData.reason);
      }
      
      setLastUpdated(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data';
      setError(errorMessage);
      console.error('Failed to fetch metrics:', err);
    } finally {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Store refreshMetrics in ref for stable reference
  React.useEffect(() => {
    refreshMetricsRef.current = refreshMetrics;
  }, [refreshMetrics]);

  useEffect(() => {
    refreshMetrics();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => refreshMetricsRef.current(), 30000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Intentionally empty - only run on mount

  // Stable refreshMetrics wrapper for context
  const stableRefreshMetrics = React.useCallback(() => {
    return refreshMetricsRef.current();
  }, []);

  return (
    <DashboardContext.Provider
      value={{
        metrics,
        fteInstances,
        slaBreaches,
        loading,
        lastUpdated,
        error,
        refreshMetrics: stableRefreshMetrics,
        searchQuery,
        setSearchQuery,
      }}
    >
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  return useContext(DashboardContext);
}
