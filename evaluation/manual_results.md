# Manual Evaluation Results

Tracks manual test runs of `AssessmentBuilder` against `test_cases.json`.
Fill in the **Actual** and **Pass/Fail** columns after running each case
through the app or a test script.

## Run Metadata

- **Date:**
- **Tester:**
- **App version / commit:**

## Results

| Test ID | Description | Expected | Actual | Pass/Fail | Notes |
|---------|-------------|----------|--------|-----------|-------|
| TC-001  | Mild, short-duration single symptom | low |  |  |  |
| TC-002  | Moderate attention symptom (fever) with short duration | moderate |  |  |  |
| TC-003  | High attention symptom (shortness of breath) | high |  |  |  |
| TC-004  | Long duration mild symptom escalates to moderate | moderate |  |  |  |
| TC-005  | Missing consent should raise a validation error | ValueError |  |  |  |
| TC-006  | Self-rated severe severity forces high urgency | high |  |  |  |
| TC-007  | No symptoms provided should raise a validation error | ValueError |  |  |  |

## Summary

- Total cases:
- Passed:
- Failed:
- Known issues / follow-ups:

## Notes on Safety Messaging

- [ ] Emergency banner visible on load
- [ ] Urgency alert copy matches urgency level returned by `AssessmentBuilder`
- [ ] Footer disclaimer present on every page render