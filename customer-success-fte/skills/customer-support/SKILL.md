# Skill: Customer Support

## Overview

The Customer Support skill provides comprehensive customer service capabilities for handling general inquiries, product questions, and support requests.

## Skill Metadata

- **Skill ID**: `customer-support`
- **Version**: 1.0.0
- **Priority**: Medium
- **Owner**: Customer Success Team

## Capabilities

This skill enables the agent to:

1. **Answer Product Questions**
   - Feature explanations
   - Usage guidance
   - Best practices
   - Troubleshooting steps

2. **Handle Support Requests**
   - Create and manage tickets
   - Track issue resolution
   - Provide status updates
   - Escalate when needed

3. **Customer Communication**
   - Professional, empathetic responses
   - Multi-channel support (web, email, WhatsApp)
   - Satisfaction surveys
   - Follow-up communications

## Triggers

This skill is activated when the user message contains:

### Keywords
- "help"
- "support"
- "question"
- "issue"
- "problem"
- "how to"
- "cannot"
- "can't"
- "error"
- "not working"

### Intents
- Product inquiry
- Technical assistance
- Account help
- Feature request
- Bug report

### Sentiment
- Confusion
- Frustration (mild)
- Curiosity

## Tools

| Tool | Description | When to Use |
|------|-------------|-------------|
| `search_knowledge_base` | Search KB articles | First step for any inquiry |
| `get_customer_history` | View customer's past interactions | Personalize response |
| `create_ticket` | Create support ticket | Issue requires tracking |
| `send_response` | Send message to customer | Always use for replies |
| `resolve_ticket` | Close ticket with resolution | Issue fully resolved |
| `escalate_to_human` | Transfer to human agent | Cannot resolve from KB |

## Response Guidelines

### Tone
- Professional yet warm
- Empathetic and understanding
- Concise but thorough
- Action-oriented

### Format
- Use numbered lists for steps
- Keep under 200 words
- Include offer for further help
- Reference relevant KB articles

### Escalation Criteria
Escalate to human agent when:
- Issue not in knowledge base
- Customer requests human agent
- Multiple failed resolution attempts
- Highly frustrated customer (sentiment < 0.3)
- Complex technical issue beyond scope

## Knowledge Base Integration

This skill uses the following KB categories:
- Getting Started
- Features & Functionality
- Troubleshooting
- Best Practices
- FAQ

## Metrics

Success metrics for this skill:
- First contact resolution rate
- Average resolution time
- Customer satisfaction score
- Escalation rate
- Ticket reopen rate

## Examples

### Example 1: Feature Question
**User**: "How do I export my data?"

**Agent**: 
1. Search KB for "export data"
2. Find relevant article
3. Provide step-by-step instructions
4. Offer further assistance

### Example 2: Technical Issue
**User**: "I'm getting an error when logging in"

**Agent**:
1. Acknowledge the frustration
2. Ask for error details
3. Search KB for login errors
4. Create ticket if not immediately resolvable
5. Provide workaround if available

## Handoff Rules

Handoff to other skills:
- **Billing Skill**: Payment, refund, subscription questions
- **Technical Skill**: Complex technical issues, API problems
- **Sales Skill**: Upgrade, pricing, enterprise features

Handoff to human when:
- All KB resources exhausted
- Customer explicitly requests human
- Legal/compliance issues arise
- High-value customer with complex issue

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial skill definition |
