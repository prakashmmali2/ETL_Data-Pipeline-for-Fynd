# Validation results

Validated on 2026-11-23 with Python 3.12.10.

## Dataset

- Source records: 20,020
- Rejected records: 15
- Duplicate SKUs removed: 5
- Rows loaded into SQLite: 20,000
- Duplicate SKUs in target: 0
- Blank/null required values: 0
- Numeric value violations: 0
- Valid boundary records: quantity 1 and 1,000; unit prices 0, 0.01, and
  999,999.99; offset timestamps normalized to UTC.

## Test report

- Test suite: 32 passed
- JUnit report: `test-results/pytest-results.xml`
- Release gate: passed

The test suite includes deliberate-corruption checks and a local CSV append
watcher check. It also demonstrates that the fixture accounting invariant
holds and generated boundary records pass the quality gate.
