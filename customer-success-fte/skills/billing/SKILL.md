# Skill: Billing Support

## Overview

The Billing Support skill handles all payment, subscription, invoicing, and refund-related inquiries.

## Skill Metadata

- **Skill ID**: `billing-support`
- **Version**: 1.0.0
- **Priority**: High
- **Owner**: Billing Team

## Capabilities

This skill enables the agent to:

1. **Payment Processing**
   - Payment method updates
   - Failed payment troubleshooting
   - Payment history inquiries
   - Invoice access and delivery

2. **Subscription Management**
   - Plan changes (upgrade/downgrade)
   - Cancellation requests
   - Renewal information
   - Trial extensions

3. **Refund Handling**
   - Refund policy explanation
   - Refund status checks
   - Refund request processing
   - Credit adjustments

4. **Pricing Information**
   - Current plan details
   - Upgrade options
   - Enterprise pricing
   - Discount eligibility

## Triggers

This skill is activated when the user message contains:

### Keywords
- "billing"
- "payment"
- "invoice"
- "refund"
- "charge"
- "subscription"
- "cancel"
- "upgrade"
- "downgrade"
- "plan"
- "pricing"
- "cost"
- "price"
- "credit card"
- "failed payment"

### Intents
- Payment issue
- Refund request
- Subscription change
- Invoice request
- Pricing inquiry

## Tools

| Tool | Description | When to Use |
|------|-------------|-------------|
| `get_billing_info` | Retrieve customer billing details | Any billing inquiry |
| `get_subscription_status` | Check current subscription | Subscription questions |
| `update_payment_method` | Update payment details | Payment update requests |
| `process_refund` | Initiate refund | Valid refund requests |
| `change_subscription` | Modify subscription plan | Plan change requests |
| `send_invoice` | Email invoice to customer | Invoice requests |
| `create_billing_ticket` | Create billing support ticket | Complex billing issues |
| `escalate_to_billing_team` | Transfer to billing specialist | Requires human review |

## Response Guidelines

### Tone
- Professional and precise
- Empathetic for payment issues
- Clear and unambiguous
- Reassuring for concerns

### Security
- Never request full credit card numbers
- Never ask for CVV or PIN
- Use secure payment links
- Verify customer identity before changes

### Escalation Criteria
Escalate to billing team when:
- Refund exceeds policy limits
- Disputed charges
- Complex subscription changes
- Enterprise account modifications
- Legal/compliance concerns

## Policies

### Refund Policy
- Full refund within 14 days of purchase
- Pro-rated refund for annual plans
- No refund for usage beyond 30 days
- Exception requires manager approval

### Cancellation Policy
- Cancel anytime
- Access until end of billing period
- Data export available for 90 days
- Reactivation within 30 days preserves data

## Knowledge Base Integration

This skill uses the following KB categories:
- Billing & Payments
- Subscription Management
- Refund Policy
- Invoice Information
- Plan Comparison

## Metrics

Success metrics for this skill:
- Refund processing time
- Subscription change accuracy
- Billing ticket resolution rate
- Customer satisfaction (billing)
- Payment success rate

## Compliance

This skill must comply with:
- PCI DSS (payment card data)
- GDPR (data privacy)
- Local consumer protection laws
- Company billing policies

## Examples

### Example 1: Refund Request
**User**: "I'd like a refund for my last payment"

**Agent**:
1. Verify customer identity
2. Check purchase date and usage
3. Apply refund policy
4. Process if eligible or explain why not
5. Create ticket if exception needed

### Example 2: Plan Upgrade
**User**: "How do I upgrade to the pro plan?"

**Agent**:
1. Explain pro plan benefits
2. Show pricing difference
3. Provide upgrade link or process
4. Confirm effective date
5. Offer setup assistance

## Handoff Rules

Handoff to other skills:
- **Customer Support**: General product questions
- **Sales**: Enterprise pricing, custom contracts
- **Technical**: Payment integration issues

Handoff to human when:
- Refund exception required
- Disputed charge
- Legal review needed
- High-value account changes

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial skill definition |
