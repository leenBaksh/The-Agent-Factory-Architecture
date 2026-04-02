# Skills Registry

This directory contains the skills registry for the Customer Success Digital FTE.

## What are Skills?

Skills are domain-specific capabilities that extend the base functionality of the AI agent. Each skill is defined by:

1. **SKILL.md** - Skill definition, triggers, and capabilities
2. **Implementation** - Python code implementing the skill logic
3. **Tools** - Functions the skill can invoke
4. **Knowledge** - Domain-specific knowledge base articles

## Skill Structure

```
skills/
├── SKILL_REGISTRY.md       # This file - registry of all skills
├── customer-support/
│   ├── SKILL.md            # Customer support skill definition
│   └── tools.py            # Support-specific tools
├── billing/
│   ├── SKILL.md            # Billing skill definition
│   └── tools.py            # Billing-specific tools
├── technical/
│   ├── SKILL.md            # Technical support skill definition
│   └── tools.py            # Technical tools
└── sales/
    ├── SKILL.md            # Sales skill definition
    └── tools.py            # Sales tools
```

## Skill Lifecycle

1. **Discovery**: Agent identifies which skill is needed based on user input
2. **Activation**: Skill is activated and given context
3. **Execution**: Skill tools are invoked to complete tasks
4. **Handoff**: If needed, skill can handoff to another skill or FTE

## Creating a New Skill

1. Create a new directory under `skills/`
2. Add `SKILL.md` with the skill definition
3. Implement tools in `tools.py`
4. Register the skill in this file
5. Add tests under `tests/skills/`

## Skill Priority

Skills are prioritized as follows:
1. **Critical**: Security, legal, compliance issues
2. **High**: Billing, refunds, account access
3. **Medium**: Technical issues, feature requests
4. **Low**: General inquiries, how-to questions
