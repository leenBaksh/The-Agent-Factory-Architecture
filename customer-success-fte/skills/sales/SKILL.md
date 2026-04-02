# Skill: Sales Support

## Overview

The Sales Support skill handles pre-sales inquiries, pricing questions, upgrade paths, and enterprise sales assistance.

## Skill Metadata

- **Skill ID**: `sales-support`
- **Version**: 1.0.0
- **Priority**: Medium
- **Owner**: Sales Team

## Capabilities

This skill enables the agent to:

1. **Pricing Information**
   - Plan comparison
   - Feature breakdown by tier
   - Discount eligibility
   - Promotional offers

2. **Upgrade Assistance**
   - Upgrade path guidance
   - Feature gap analysis
   - ROI justification
   - Migration planning

3. **Enterprise Sales**
   - Enterprise feature overview
   - Custom requirements
   - Security/compliance info
   - SLA information

4. **Trial Management**
   - Trial extension requests
   - Trial feature access
   - Conversion assistance
   - Onboarding guidance

## Triggers

This skill is activated when the user message contains:

### Keywords
- "pricing"
- "cost"
- "upgrade"
- "enterprise"
- "demo"
- "trial"
- "features"
- "plans"
- "subscription"
- "buy"
- "purchase"
- "quote"
- "proposal"
- "contract"
- "volume discount"
- "team plan"

### Intents
- Pre-sales inquiry
- Upgrade consideration
- Feature comparison
- Enterprise requirements
- Trial extension

## Tools

| Tool | Description | When to Use |
|------|-------------|-------------|
| `get_pricing_info` | Retrieve current pricing | Pricing inquiries |
| `compare_plans` | Compare feature by plan | Plan comparison requests |
| `check_upgrade_options` | Get upgrade paths | Upgrade inquiries |
| `get_enterprise_info` | Enterprise features/SLA | Enterprise inquiries |
| `extend_trial` | Extend trial period | Trial extension requests |
| `create_sales_lead` | Create lead in CRM | Sales qualified leads |
| `schedule_demo` | Schedule product demo | Demo requests |
| `escalate_to_sales` | Transfer to sales rep | High-value opportunities |

## Response Guidelines

### Tone
- Enthusiastic and helpful
- Value-focused
- Non-pushy
- Consultative

### Format
- Clear plan comparisons
- Feature benefit explanations
- ROI examples when relevant
- Clear next steps

### Sales Qualification
Qualify leads by identifying:
- Company size
- Use case
- Timeline
- Budget range
- Decision makers

## Pricing Guidelines

### Standard Plans
- Free: Basic features, limited usage
- Pro: Full features, standard support
- Business: Advanced features, priority support
- Enterprise: Custom, dedicated support

### Discounts
- Annual billing: 20% discount
- Non-profit: 30% discount
- Education: 40% discount
- Volume: Custom pricing

## Knowledge Base Integration

This skill uses the following KB categories:
- Pricing & Plans
- Feature Comparison
- Enterprise Features
- Trial Information
- Migration Guides

## Metrics

Success metrics for this skill:
- Lead conversion rate
- Upgrade conversion rate
- Trial-to-paid conversion
- Sales qualified leads generated
- Average deal size

## Examples

### Example 1: Plan Comparison
**User**: "What's the difference between Pro and Business?"

**Agent**:
1. Provide feature comparison table
2. Highlight key differentiators
3. Explain use cases for each
4. Offer personalized recommendation
5. Provide upgrade link if interested

### Example 2: Enterprise Inquiry
**User**: "Do you offer enterprise pricing?"

**Agent**:
1. Confirm enterprise availability
2. Explain enterprise features
3. Mention SLA and support options
4. Collect company information
5. Connect with enterprise sales rep

## Handoff Rules

Handoff to other skills:
- **Customer Support**: Existing customer issues
- **Billing**: Payment processing, refunds
- **Technical**: Technical feasibility questions

Handoff to human when:
- Large enterprise opportunity (>100 seats)
- Custom contract required
- Complex integration requirements
- Strategic account

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial skill definition |
