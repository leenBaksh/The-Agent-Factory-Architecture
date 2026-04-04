---
name: code-review
description: "Perform systematic code review using checklist, architecture analysis, and best practices"
triggers: ["code review", "PR review", "pull request", "review code", "quality check"]
version: "1.0.0"
---

# Code Review Skill

## Overview
This skill teaches the Digital FTE how to perform systematic, thorough code reviews following enterprise engineering standards.

## Review Checklist

### 1. Correctness
- [ ] Does the code do what it's supposed to do?
- [ ] Are there edge cases not handled?
- [ ] Are error conditions handled properly?
- [ ] Are there off-by-one errors or boundary issues?
- [ ] Is the logic sound and free of bugs?

### 2. Security
- [ ] No hardcoded secrets or credentials
- [ ] Input validation on all external data
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] Authentication/authorization checks in place
- [ ] Sensitive data not logged or exposed

### 3. Performance
- [ ] No N+1 query patterns
- [ ] Database queries use appropriate indexes
- [ ] No unnecessary loops or redundant operations
- [ ] Caching used appropriately
- [ ] Memory usage reasonable for expected data volumes
- [ ] Async/await used correctly for I/O operations

### 4. Readability & Maintainability
- [ ] Function/method names clearly describe what they do
- [ ] Variables have meaningful names
- [ ] Functions are focused (single responsibility)
- [ ] Code is DRY (no unnecessary duplication)
- [ ] Comments explain WHY, not WHAT
- [ ] Complex logic has inline documentation

### 5. Architecture & Design
- [ ] Follows established project patterns
- [ ] Proper separation of concerns
- [ ] Dependencies are appropriate and minimal
- [ ] No circular dependencies
- [ ] Abstraction level is correct (not leaking implementation details)

### 6. Testing
- [ ] Unit tests cover happy path and edge cases
- [ ] Integration tests for external dependencies
- [ ] Test names describe what they're testing
- [ ] Tests are deterministic (no flaky tests)
- [ ] Test coverage meets project threshold (80%+)

### 7. API Design (if applicable)
- [ ] Endpoints follow RESTful conventions
- [ ] Request/response schemas are well-defined
- [ ] Error responses are consistent and informative
- [ ] Pagination implemented for list endpoints
- [ ] Rate limiting considered
- [ ] Versioning strategy followed

## Review Procedure

### Phase 1: Understand the Change
1. Read the PR description
2. Understand the problem being solved
3. Review associated tickets or specs
4. Note the scope of changes

### Phase 2: First Pass (Structure)
1. Review file-level changes
2. Check for architectural consistency
3. Identify major patterns used
4. Note any red flags

### Phase 3: Detailed Review (Line by Line)
1. Apply the review checklist above
2. Note specific line numbers for each finding
3. Categorize findings: Critical, Major, Minor, Suggestion

### Phase 4: Synthesize Feedback
Structure review output as:
```
# Code Review: [PR Title]

## Summary
[1-2 sentence overall assessment]

## Critical Issues (Must Fix)
- [ ] Line X: [Description + suggested fix]

## Major Issues (Should Fix)
- [ ] Line X: [Description + suggested fix]

## Minor Issues (Consider Fixing)
- [ ] Line X: [Description + suggested fix]

## Suggestions (Optional Improvements)
- [ ] Line X: [Description]

## Positive Notes
- [What was done well]

## Verdict: Approve / Request Changes / Comment
```

## Severity Definitions
| Severity | Definition | Action |
|----------|------------|--------|
| Critical | Bug, security vulnerability, data loss | Must fix before merge |
| Major | Performance issue, design flaw | Should fix before merge |
| Minor | Code smell, readability issue | Consider fixing |
| Suggestion | Nice-to-have improvement | Optional |

## Automated Checks
Before manual review, ensure:
- [ ] Linting passes (no style violations)
- [ ] Type checking passes (no type errors)
- [ ] All tests pass
- [ ] Build succeeds
- [ ] No merge conflicts

## Fallback Protocol
If review reveals critical issues:
1. Block merge with clear explanation
2. Provide specific fix suggestions
3. Offer to review the fix once submitted
4. Escalate to senior engineer if disagreement persists
