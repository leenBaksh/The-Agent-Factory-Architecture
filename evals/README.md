# Agent Evals - Digital FTE Testing

This directory contains the evaluation infrastructure for testing Digital FTEs before deployment.

## Overview

Agent Evals test the reasoning and accuracy of a Digital FTE against a "Golden Dataset" of real-world scenarios. Every FTE must pass with 95%+ accuracy before deployment.

## Directory Structure

```
evals/
├── run_evals.py                    # Main evaluation runner
├── results.json                    # Generated after running evals
└── invoice-processor/
    └── golden_dataset.yaml         # 50 test scenarios
```

## Running Evaluations

### Basic Usage
```bash
# Run with default settings (95% threshold)
python evals/run_evals.py

# Custom accuracy threshold
python evals/run_evals.py --min-accuracy 0.90

# Specify scenario directory
python evals/run_evals.py --scenario-dir evals/invoice-processor

# Custom output file
python evals/run_evals.py --output evals/results.json
```

### CI/CD Integration
```bash
# In GitHub Actions or similar
python evals/run_evals.py --min-accuracy 0.95
# Exit code 0 = passed, 1 = failed
```

## Golden Dataset Format

Each scenario in `golden_dataset.yaml` follows this structure:

```yaml
scenarios:
  - id: "inv-001"
    description: "Standard invoice with matching PO"
    input:
      invoice_pdf: "samples/standard_invoice.pdf"
      po_number: "PO-2025-0042"
    expected:
      status: "approved"
      extracted_amount: 1250.00
      vendor_match: true
      confidence_score: 0.95
```

## Scoring

| Score | Status |
|-------|--------|
| 95%+ | ✅ Production Ready |
| 90-94% | ⚠️ Needs Improvement |
| < 90% | ❌ Not Ready |

## Adding New Scenarios

1. Add scenario to `golden_dataset.yaml`
2. Include edge cases, error conditions, and normal operations
3. Minimum 50 scenarios per FTE type
4. Run evals to verify new scenario works
