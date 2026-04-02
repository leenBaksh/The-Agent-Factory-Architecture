'use client';

import React from 'react';
import { Header } from '@/components/Header';
import { MetricsOverview } from '@/components/MetricsOverview';
import { ChartsSection } from '@/components/ChartsSection';
import { RecentTickets } from '@/components/RecentTickets';
import { SLABreachesPanel } from '@/components/SLABreachesPanel';
import { FTEInstancesPanel } from '@/components/FTEInstancesPanel';
import { ErrorBanner } from '@/components/ErrorBanner';
import { useDashboard } from '@/contexts/DashboardContext';

export default function Dashboard() {
  const { error, refreshMetrics } = useDashboard();

  return (
    <>
      <Header 
        title="Dashboard" 
        subtitle="Monitor your Digital FTEs and support metrics"
      />
      
      {/* Error Banner */}
      {error && (
        <ErrorBanner
          error={error}
          onRetry={refreshMetrics}
          type="disconnected"
        />
      )}

      <div className="p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Metrics Overview */}
          <MetricsOverview />

          {/* Charts Section */}
          <ChartsSection />

          {/* Bottom Section */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Left - Recent Tickets */}
            <div className="lg:col-span-2">
              <RecentTickets />
            </div>

            {/* Right - SLA and FTE */}
            <div className="space-y-6">
              <SLABreachesPanel />
              <FTEInstancesPanel />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
