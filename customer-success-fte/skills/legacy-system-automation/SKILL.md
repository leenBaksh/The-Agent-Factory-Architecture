---
name: legacy-system-automation
description: "Automate legacy systems via GUI automation, screen scraping, and RPA patterns"
triggers: ["legacy", "GUI", "desktop", "screen", "RPA", "automation", "mainframe"]
version: "1.0.0"
---

# Legacy System Automation Skill

## Overview
This skill teaches the Digital FTE how to automate legacy systems that lack modern APIs, using Computer Use (GUI automation), screen scraping, and RPA patterns.

## Prerequisites
- Claude Agent SDK with Computer Use enabled
- Agent Sandbox (gVisor) for secure execution
- Screen resolution: 1920x1080 minimum

## Core Procedures

### 1. System Discovery
Before automating any legacy system:
1. **Identify the application**: Name, version, access method (RDP, Citrix, local)
2. **Map the workflow**: Document each screen, field, and navigation path
3. **Identify entry points**: How to launch the application
4. **Document expected states**: What each screen should look like when ready

### 2. Screen Recognition Pattern
Use visual verification at each step:
```
1. Take screenshot
2. Identify UI elements (buttons, fields, menus)
3. Verify expected state matches actual state
4. If mismatch → retry screenshot, then flag for human review
```

### 3. Data Entry Procedure
For each field to populate:
1. **Navigate**: Click/tab to the correct field
2. **Verify**: Confirm cursor is in the right place (screenshot)
3. **Enter**: Type the data
4. **Confirm**: Verify data appears correctly (screenshot)
5. **Proceed**: Tab/click to next field or submit

### 4. Error Handling
| Scenario | Action |
|----------|--------|
| Screen doesn't match expected state | Retry screenshot (2x), then flag |
| Field not found | Screenshot + flag for human review |
| Application crash | Restart app, resume from last checkpoint |
| Timeout (>30s per action) | Screenshot + flag, log error |
| Unexpected popup/dialog | Dismiss if safe, otherwise flag |

### 5. Checkpoint Strategy
Save state after each major step:
```json
{
  "step": "data_entry_complete",
  "timestamp": "ISO 8601",
  "screenshot_path": "/artifacts/screenshot_step3.png",
  "data_entered": {"field1": "value1", "field2": "value2"},
  "next_step": "submit_form"
}
```

### 6. Verification Protocol
After completing automation:
1. Take final screenshot
2. Compare against expected completion state
3. Extract confirmation number/message if present
4. Log success or failure with evidence

## Security Constraints
- **NEVER** store credentials in screenshots or logs
- **NEVER** automate systems containing PII without sandbox isolation
- **ALWAYS** use Agent Sandbox (gVisor) for execution
- **ALWAYS** mask sensitive fields in screenshots before storing

## Common Patterns

### Pattern 1: Form Filling
```
Launch App → Navigate to Form → Fill Fields → Submit → Confirm
```

### Pattern 2: Data Extraction
```
Launch App → Navigate to Report → Screenshot → Parse Data → Export
```

### Pattern 3: Multi-Step Workflow
```
Step 1 → Verify → Step 2 → Verify → ... → Final Step → Confirm
```

## Quality Metrics
- **Accuracy**: 99%+ field population accuracy
- **Speed**: Complete workflow within 2x human operator time
- **Reliability**: <1% failure rate requiring human intervention
- **Evidence**: Screenshot at every major step

## Fallback Protocol
If automation fails:
1. Capture final screenshot with error state
2. Log all steps completed and where failure occurred
3. Queue task for human operator with full context
4. Notify via Slack MCP with error summary
