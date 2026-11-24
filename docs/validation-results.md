# Validation results

Validation completed on 2026-11-24 with Python 3.12.10, Playwright 1.65.2,
and Chromium 159.

## Dataset

- Source records: 20,020
- Rejected records: 15
- Duplicate order/SKU lines removed: 5
- Rows loaded into SQLite: 20,000
- Duplicate order/SKU lines in target: 0
- Blank/null required values: 0
- Numeric value violations: 0
- Valid boundary records: quantity 1 and 1,000; unit prices 0, 0.01, and
  999,999.99; offset timestamps normalized to UTC.
- Numeric release-gate checks: fractional quantities, non-numeric values, and
  infinite values are rejected.

The checked-in sample database was refreshed from a clean fixture and contains
20,000 order/SKU rows. A focused migration test verifies that the earlier
SKU-primary-key schema can be upgraded without dropping its existing rows.

## Test report

- ETL test cases: 39 passed
- Checkout browser cases: 8 passed; see
  [checkout test plan and results](checkout-test-plan.md).
- Combined test suite: 47 passed
- JUnit report: `test-results/pytest-results.xml`
- Release gate: passed

The test suite includes deliberate-corruption checks, old-schema migration,
repeated SKUs across different customer orders, checkout persistence, and a
local CSV append watcher check. It also demonstrates that the fixture
accounting invariant holds and generated boundary records pass the quality
gate. The CI workflow uploads the JUnit report as a downloadable artifact.

This validates only the local synthetic-data practice project. It is not a
FyndHacks submission and has not been evaluated against a private challenge
prompt or scoring rubric.
