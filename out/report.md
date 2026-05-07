# Socratix alert-investigation eval (mini)

- Agent: `baseline_rules_v1`
- Cases: `12`
- Escalate metrics (treating `escalate` as positive): precision=1.00, recall=0.80, f1=0.89

## Case-by-case

### A-001: Card testing burst on new device
- Expected: `escalate` | Predicted: `escalate` | Risk: `0.50` (medium)
- Evidence used: device_new, velocity_spike, card_testing_pattern
  - Pattern match: card testing + velocity spike → escalate.
  - New device
  - Velocity spike (x1.0)
  - Card-testing pattern

### A-002: Login anomaly + geo mismatch (possible ATO)
- Expected: `escalate` | Predicted: `escalate` | Risk: `0.52` (medium)
- Evidence used: device_new, ip_geo_mismatch, multiple_failed_logins
  - Pattern match: ATO-style login anomaly (fails + geo mismatch + new device) → escalate.
  - New device
  - IP geo mismatch
  - Multiple failed logins

### A-003: High amount, known device, no other risk
- Expected: `review` | Predicted: `close` | Risk: `0.14` (low)
- Evidence used: amount_usd
  - High amount ($2,600)

### A-004: Chargeback history + medium amount
- Expected: `escalate` | Predicted: `escalate` | Risk: `0.24` (low)
- Evidence used: chargeback_history, amount_usd
  - Pattern match: chargeback history + meaningful amount → escalate.
  - Chargeback history
  - Medium amount ($780)

### A-005: Synthetic ID indicators on fresh account
- Expected: `escalate` | Predicted: `escalate` | Risk: `0.28` (low)
- Evidence used: email_age_low, synthetic_id_signal
  - Pattern match: synthetic ID indicators on fresh identity → escalate.
  - Low email age
  - Synthetic identity signal

### A-006: Low-risk repeat purchase
- Expected: `close` | Predicted: `close` | Risk: `0.00` (low)
- Evidence used: (none)
  - No strong risk signals triggered in baseline rules.

### A-007: High-risk merchant + geo mismatch
- Expected: `review` | Predicted: `close` | Risk: `0.32` (low)
- Evidence used: ip_geo_mismatch, merchant_risk_high
  - IP geo mismatch
  - High-risk merchant/category

### A-008: Velocity spike but tiny amounts (could be benign)
- Expected: `review` | Predicted: `close` | Risk: `0.14` (low)
- Evidence used: velocity_spike
  - Velocity spike (x0.8)

### A-009: Possible mule behavior + new device + medium amount
- Expected: `escalate` | Predicted: `review` | Risk: `0.38` (medium)
- Evidence used: device_new, mule_activity_signal, amount_usd
  - New device
  - Possible mule activity
  - Medium amount ($650)

### A-010: Geo mismatch only, low amount
- Expected: `review` | Predicted: `close` | Risk: `0.20` (low)
- Evidence used: ip_geo_mismatch
  - IP geo mismatch

### A-011: New device only, low amount
- Expected: `review` | Predicted: `close` | Risk: `0.22` (low)
- Evidence used: device_new
  - New device

### A-012: Multiple weak signals, no single smoking gun
- Expected: `review` | Predicted: `review` | Risk: `0.35` (medium)
- Evidence used: velocity_spike, email_age_low, merchant_risk_high
  - Velocity spike (x0.5)
  - Low email age
  - High-risk merchant/category
