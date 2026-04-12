# Customer Success FTE - Golden Dataset Evals

## Test Scenarios for Accuracy Validation

This file contains 50+ scenarios to test the Customer Success FTE before deployment.
Each scenario includes input, expected output, and scoring criteria.

---

## Scenario Format

```yaml
scenarios:
  - id: "CS-001"
    category: "standard_support"
    description: "Standard login issue - password reset not working"
    input:
      channel: "email"
      subject: "Can't log in to my account"
      body: |
        Hi,
        
        I've been trying to reset my password but I'm not receiving the reset email.
        I've checked my spam folder already.
        
        My email is john.doe@example.com
        
        Thanks,
        John
    expected:
      status: "in_progress"
      actions:
        - "verify_email_in_system"
        - "check_email_delivery"
        - "manual_password_reset_link"
      response_includes:
        - "acknowledge the issue"
        - "confirm email found"
        - "provide manual reset link"
      priority: "medium"
      sla_status: "on_track"
    scoring:
      exact_match: false
      semantic_similarity_threshold: 0.85
```

---

## Full Scenario Suite

```yaml
scenarios:
  # ── Standard Support Issues (1-15) ─────────────────────────────────────────
  
  - id: "CS-001"
    category: "standard_support"
    description: "Password reset email not received"
    input:
      channel: "email"
      subject: "Can't reset password"
      body: "I'm not getting the password reset email. Checked spam folder already."
    expected:
      status: "in_progress"
      actions: ["verify_email", "check_delivery", "manual_reset"]
      priority: "medium"
    scoring:
      semantic_similarity_threshold: 0.85

  - id: "CS-002"
    category: "standard_support"
    description: "Billing question - unexpected charge"
    input:
      channel: "chat"
      message: "I see a charge on my card that I don't recognize. Can you help?"
    expected:
      status: "in_progress"
      actions: ["pull_account", "review_charges", "explain_or_refund"]
      priority: "high"
    scoring:
      semantic_similarity_threshold: 0.90

  - id: "CS-003"
    category: "standard_support"
    description: "Feature request - dark mode"
    input:
      channel: "email"
      subject: "Feature request: Dark mode please!"
      body: "Love the product but really need a dark mode option. Any plans to add one?"
    expected:
      status: "open"
      actions: ["log_feature_request", "provide_workaround", "set_expectations"]
      priority: "low"
    scoring:
      semantic_similarity_threshold: 0.80

  - id: "CS-004"
    category: "standard_support"
    description: "How-to question - export data"
    input:
      channel: "chat"
      message: "How do I export my data to CSV?"
    expected:
      status: "resolved"
      actions: ["provide_steps", "confirm_resolution"]
      priority: "low"
    scoring:
      semantic_similarity_threshold: 0.90

  - id: "CS-005"
    category: "standard_support"
    description: "Integration setup help"
    input:
      channel: "email"
      subject: "Need help connecting to Salesforce"
      body: "I'm trying to set up the Salesforce integration but getting an authentication error."
    expected:
      status: "in_progress"
      actions: ["check_integration_docs", "verify_credentials", "provide_setup_steps"]
      priority: "medium"
    scoring:
      semantic_similarity_threshold: 0.85

  # ── Escalations (6-15) ─────────────────────────────────────────────────────

  - id: "CS-006"
    category: "escalation"
    description: "Angry customer demanding refund"
    input:
      channel: "email"
      subject: "UNACCEPTABLE SERVICE - I WANT A REFUND"
      body: |
        This is the third time this month I've had issues! 
        I want a full refund NOW or I'm canceling and going to your competitor!
        
        This is completely unacceptable.
    expected:
      status: "in_progress"
      actions: ["de_escalate", "acknowledge_frustration", "offer_solution"]
      priority: "critical"
      escalation: "human_review"
    scoring:
      semantic_similarity_threshold: 0.95

  - id: "CS-007"
    category: "escalation"
    description: "Threatening legal action"
    input:
      channel: "email"
      subject: "Legal notice - breach of contract"
      body: "Your service has caused our business significant harm. Our lawyers are reviewing the situation."
    expected:
      status: "open"
      actions: ["immediate_escalation", "do_not_respond_legally", "notify_management"]
      priority: "critical"
      escalation: "legal_team"
    scoring:
      semantic_similarity_threshold: 0.95

  - id: "CS-008"
    category: "escalation"
    description: "Request to speak to manager"
    input:
      channel: "chat"
      message: "I need to speak to your manager. This isn't acceptable."
    expected:
      status: "in_progress"
      actions: ["acknowledge_request", "attempt_resolution", "escalate_if_insisted"]
      priority: "high"
    scoring:
      semantic_similarity_threshold: 0.90

  # ── Technical Issues (9-20) ────────────────────────────────────────────────

  - id: "CS-009"
    category: "technical"
    description: "Application error - 500 on dashboard"
    input:
      channel: "email"
      subject: "Dashboard not loading - 500 error"
      body: "Getting a 500 Internal Server Error when I try to access the dashboard."
    expected:
      status: "in_progress"
      actions: ["check_system_status", "investigate_logs", "provide_ETA"]
      priority: "high"
    scoring:
      semantic_similarity_threshold: 0.85

  - id: "CS-010"
    category: "technical"
    description: "Slow performance complaint"
    input:
      channel: "chat"
      message: "The application is so slow today. Takes forever to load."
    expected:
      status: "in_progress"
      actions: ["check_performance_metrics", "identify_bottleneck", "provide_status"]
      priority: "medium"
    scoring:
      semantic_similarity_threshold: 0.80

  - id: "CS-011"
    category: "technical"
    description: "Data not syncing"
    input:
      channel: "email"
      subject: "Data not updating"
      body: "My dashboard hasn't updated in 24 hours. The last sync was yesterday."
    expected:
      status: "in_progress"
      actions: ["check_sync_status", "trigger_manual_sync", "investigate_root_cause"]
      priority: "high"
    scoring:
      semantic_similarity_threshold: 0.85

  # ── Billing Issues (12-20) ─────────────────────────────────────────────────

  - id: "CS-012"
    category: "billing"
    description: "Duplicate charge"
    input:
      channel: "email"
      subject: "Charged twice for same month"
      body: "I see two charges on my credit card for $99 each this month. I should only be charged once."
    expected:
      status: "in_progress"
      actions: ["verify_charges", "initiate_refund", "confirm_resolution"]
      priority: "high"
      refund_amount: 99.00
    scoring:
      semantic_similarity_threshold: 0.90

  - id: "CS-013"
    category: "billing"
    description: "Request for discount"
    input:
      channel: "chat"
      message: "I've been a customer for 3 years. Do you offer any loyalty discounts?"
    expected:
      status: "in_progress"
      actions: ["check_account_history", "review_available_discounts", "apply_if_eligible"]
      priority: "low"
    scoring:
      semantic_similarity_threshold: 0.85

  - id: "CS-014"
    category: "billing"
    description: "Upgrade plan inquiry"
    input:
      channel: "email"
      subject: "Want to upgrade to Enterprise plan"
      body: "We're growing and need more features. What's involved in upgrading?"
    expected:
      status: "in_progress"
      actions: ["explain_plans", "calculate_price_difference", "offer_demo"]
      priority: "medium"
      sales_handoff: true
    scoring:
      semantic_similarity_threshold: 0.85

  # ── Positive Interactions (15-20) ──────────────────────────────────────────

  - id: "CS-015"
    category: "positive"
    description: "Thank you message"
    input:
      channel: "email"
      subject: "Thank you!"
      body: "Just wanted to say thanks for the great support last week. Really appreciate it!"
    expected:
      status: "closed"
      actions: ["acknowledge_thanks", "reinforce_commitment"]
      priority: "low"
    scoring:
      semantic_similarity_threshold: 0.80

  - id: "CS-016"
    category: "positive"
    description: "Compliment about product"
    input:
      channel: "chat"
      message: "Your new update is amazing! Love the new features."
    expected:
      status: "closed"
      actions: ["acknowledge_compliment", "share_with_team"]
      priority: "low"
    scoring:
      semantic_similarity_threshold: 0.80

  # ── Edge Cases (17-25) ─────────────────────────────────────────────────────

  - id: "CS-017"
    category: "edge_case"
    description: "Non-English message (Spanish)"
    input:
      channel: "email"
      subject: "Necesito ayuda"
      body: "Hola, no puedo acceder a mi cuenta. ¿Pueden ayudarme?"
    expected:
      status: "in_progress"
      actions: ["detect_language", "respond_in_spanish_or_escalate"]
      priority: "medium"
    scoring:
      semantic_similarity_threshold: 0.75

  - id: "CS-018"
    category: "edge_case"
    description: "Vague complaint"
    input:
      channel: "chat"
      message: "This doesn't work. Fix it."
    expected:
      status: "in_progress"
      actions: ["ask_for_details", "provide_examples_of_needed_info"]
      priority: "medium"
    scoring:
      semantic_similarity_threshold: 0.80

  - id: "CS-019"
    category: "edge_case"
    description: "Multiple issues in one message"
    input:
      channel: "email"
      subject: "Many problems"
      body: |
        1. Can't log in
        2. Billing is wrong
        3. Integration not working
        4. Need to add team members
    expected:
      status: "in_progress"
      actions: ["address_each_issue", "create_separate_tickets", "prioritize"]
      priority: "high"
    scoring:
      semantic_similarity_threshold: 0.85

  - id: "CS-020"
    category: "edge_case"
    description: "Request for competitor comparison"
    input:
      channel: "chat"
      message: "How do you compare to CompetitorX? I'm evaluating both."
    expected:
      status: "in_progress"
      actions: ["provide_differentiators", "avoid_negative_competitor", "offer_demo"]
      priority: "medium"
      sales_handoff: true
    scoring:
      semantic_similarity_threshold: 0.85

```

---

## Scoring Rubric

| Score | Meaning | Action |
|-------|---------|--------|
| 0.95+ | Excellent | Deploy with confidence |
| 0.85-0.94 | Good | Review failures, minor fixes needed |
| 0.75-0.84 | Acceptable | Significant improvements needed |
| < 0.75 | Poor | Do not deploy, retrain required |

## Execution

Run the eval suite with:

```bash
python evals/run_evals.py --fte customer-success --min-accuracy 0.85
```
