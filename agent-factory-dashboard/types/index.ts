// API Types for Agent Factory Dashboard

export interface Ticket {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  channel: 'web' | 'gmail' | 'whatsapp';
  status: 'open' | 'in_progress' | 'waiting_customer' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  subject: string;
  description: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  assigned_to?: string;
  sla_status: 'on_track' | 'at_risk' | 'breached';
  sla_due_at?: string;
  sentiment_score?: number;
  survey_rating?: number;
  survey_feedback?: string;
}

export interface Customer {
  id: string;
  email: string;
  phone?: string;
  name?: string;
  company?: string;
  plan: 'free' | 'basic' | 'premium' | 'enterprise';
  total_tickets: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  customer_id: string;
  ticket_id?: string;
  channel: 'web' | 'gmail' | 'whatsapp';
  message_count: number;
  created_at: string;
  last_message_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'customer' | 'agent' | 'system';
  content: string;
  channel: string;
  created_at: string;
  sentiment_score?: number;
}

export interface AgentMetrics {
  date: string;
  total_conversations: number;
  total_tickets: number;
  resolved_tickets: number;
  avg_resolution_time_minutes: number;
  avg_first_response_time_minutes: number;
  total_tokens_in: number;
  total_tokens_out: number;
  escalation_count: number;
  survey_avg_rating: number;
  sla_breach_count: number;
}

export interface DashboardMetrics {
  summary: {
    total_tickets: number;
    open_tickets: number;
    avg_resolution_time_hours: number;
    avg_satisfaction_rating: number;
    sla_compliance_rate: number;
    total_conversations_24h: number;
  };
  tickets_by_status: Record<string, number>;
  tickets_by_channel: Record<string, number>;
  recent_tickets: Ticket[];
  sla_breaches: SLABreach[];
  metrics_history: AgentMetrics[];
}

export interface FTEInstance {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'stopped' | 'error' | 'scaling';
  version: string;
  uptime_seconds: number;
  last_health_check: string;
  metrics: {
    messages_per_minute: number;
    avg_latency_ms: number;
    error_rate: number;
    active_conversations: number;
  };
}

export interface SLABreach {
  id: string;
  ticket_id: string;
  customer_name: string;
  sla_type: 'first_response' | 'resolution';
  breached_at: string;
  breach_duration_minutes: number;
  status: 'active' | 'acknowledged' | 'resolved';
}
