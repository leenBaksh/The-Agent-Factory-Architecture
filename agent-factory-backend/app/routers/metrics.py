"""
Metrics Router - Aggregates metrics from all FTEs.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import get_settings
from app.services.fte_registry import fte_registry

logger = logging.getLogger(__name__)
settings = get_settings()


async def aggregate_dashboard_metrics() -> dict[str, Any]:
    """
    Aggregate dashboard metrics from all FTE instances.
    
    Returns comprehensive metrics including:
    - Summary statistics
    - Tickets by status and channel
    - Recent tickets
    - SLA breaches
    - Historical metrics
    """
    
    # Mock data for demonstration (in production, fetch from all FTEs)
    now = datetime.now()
    history = []
    for i in range(7):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        history.append({
            "date": date,
            "total_conversations": 150 + i * 10,
            "total_tickets": 45 + i * 5,
            "resolved_tickets": 40 + i * 4,
            "avg_resolution_time_minutes": 45 - i * 2,
            "avg_first_response_time_minutes": 5 - i * 0.3,
            "sla_breach_count": max(0, 3 - i),
        })
    
    return {
        "summary": {
            "total_tickets": 287,
            "open_tickets": 23,
            "avg_resolution_time_hours": 1.2,
            "avg_satisfaction_rating": 4.6,
            "sla_compliance_rate": 94.5,
            "total_conversations_24h": 156,
        },
        "tickets_by_status": {
            "open": 23,
            "in_progress": 15,
            "waiting_customer": 8,
            "resolved": 189,
            "closed": 52,
        },
        "tickets_by_channel": {
            "web": 145,
            "gmail": 98,
            "whatsapp": 44,
        },
        "recent_tickets": [
            {
                "id": f"TKT-2024-{1250 - i}",
                "customer_id": f"CUST-{str(i + 1).zfill(3)}",
                "customer_name": f"Customer {i + 1}",
                "customer_email": f"customer{i + 1}@example.com",
                "channel": ["web", "gmail", "whatsapp"][i % 3],
                "status": ["open", "in_progress", "resolved", "closed"][i % 4],
                "priority": ["low", "medium", "high", "critical"][i % 4],
                "subject": f"Sample ticket subject {i + 1}",
                "description": f"This is a sample ticket description for ticket {i + 1}",
                "created_at": (now - timedelta(hours=i + 1)).isoformat(),
                "updated_at": now.isoformat(),
                "sla_status": ["on_track", "at_risk", "breached"][i % 3],
                "sentiment_score": 0.3 + (i % 7) * 0.1,
            }
            for i in range(10)
        ],
        "sla_breaches": [],
        "metrics_history": history,
    }


async def get_all_sla_breaches() -> list[dict[str, Any]]:
    """Get SLA breaches from all FTEs."""
    
    # Mock data for demonstration
    now = datetime.now()
    return [
        {
            "id": f"SLA-{i + 1}",
            "ticket_id": f"TKT-2024-{1200 + i}",
            "customer_name": f"Customer {i + 1}",
            "sla_type": ["first_response", "resolution"][i % 2],
            "breached_at": (now - timedelta(hours=i + 2)).isoformat(),
            "breach_duration_minutes": (i + 1) * 30,
            "status": ["active", "acknowledged", "resolved"][i % 3],
        }
        for i in range(5)
    ]
