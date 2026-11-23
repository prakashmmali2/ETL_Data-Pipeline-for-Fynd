# ETL workflow test plan

## Contract

The source CSV must contain exactly these columns (column order may vary):
`order_id`, `customer_id`, `sku`, `quantity`, `unit_price`,
`order_timestamp`, and `updated_at`. A missing or added column fails the
contract before the target is modified.

## Expected data behavior

- Trim surrounding whitespace and normalize SKU values to uppercase.
- Require quantity to be a finite positive integer; accept the lower boundary
  of 1 and larger values.
- Require unit price to be finite and non-negative; zero is a valid boundary.
- Reject blank required fields, fractional or non-positive quantities,
  negative or non-numeric prices, and invalid timestamps.
- Accept parseable timezone offsets and store timestamps normalized to UTC.
- Write rejected records to a CSV with exactly one rejection reason per row.
- For repeated SKUs, retain the record with the latest `updated_at`; if times
  tie, retain the later source record.
- Upsert by SKU so running the same batch more than once does not grow the
  target or change the resulting records.
- Preserve the row-accounting invariant:
  `rows_read = rows_rejected + duplicates_removed + rows_loaded`.

## Generated fixture

`python -m src.generate_data --output data/orders.csv` creates 20,020 rows:
15 rejected records, 5 duplicate records removed, and 20,000 unique records
loaded. The duplicate updates are deliberately out of source order. Five valid
boundary records cover quantity 1 and 1,000, zero and one-cent prices,
a large price, and timestamps with positive and negative UTC offsets.

Run tests with `python -m pytest -q --junitxml=test-results\pytest-results.xml`.
The JUnit XML report is saved at `test-results\pytest-results.xml`.

## Business context and harness scope

Fynd's public overview describes unified commerce, including connecting orders
and inventory across stores and sales channels:
[Fynd company overview](https://www.fynd.com/about-us). That public description
is context, not a production integration contract. This repository is a
synthetic CSV-to-SQLite harness, not Fynd's real system. Its deliberate
corruption tests verify that the release gate rejects duplicate SKUs, blank
required values, and invalid quantity ranges. The current source contract does
not model channel IDs, store/location IDs, inventory movements, returns, or a
streaming event feed; no production compatibility is claimed. The optional
CSV watcher is only a local near-real-time demo: it reruns the full batch when
the file changes and has no defined latency SLA or durable event checkpoint.

The watcher integration test appends a valid record and verifies it becomes
queryable in SQLite. This proves the demo detects an append; it does not certify
Fynd compatibility or prove behavior under production load.

## Assumptions, gaps, and not tested

- The input is a local CSV with the exact seven-column contract above, and SKU
  is the key used to deduplicate and upsert orders.
- The fixture is synthetic. No Fynd API, production database, credentials, or
  private challenge data are used.
- The challenge-specific use case is provided after registration. This project
  has not been checked against that private prompt or an unpublished rubric;
  adapt it to the actual prompt before submitting.
- No production-scale performance, concurrent writers, durable event
  processing, or recovery after process/machine failure is tested. The watcher
  is a local full-batch rerun demo, not a streaming service.
- Store/channel identifiers, inventory movements, returns, authentication,
  authorization, and integration behavior are outside the current model.

## Release gate

Run `python -m src.report --database data/orders.sqlite` after loading. The
command exits non-zero if the table is missing, empty, has missing required
columns, contains blank/null required values, has duplicate SKUs, or violates
numeric value constraints. Its acceptance criteria require numeric, finite,
positive integral quantities and numeric, finite, non-negative prices. Quantity
1 and a zero price are valid boundaries.

## SDET Intern evidence

The role description shared for this project emphasizes manual and automated
testing, defect documentation, and build validation. This demo shows those
skills; it does not claim to implement an unpublished hackathon use case or
scoring rubric.

| Responsibility | Project evidence |
|---|---|
| Design and run automated tests | `tests/test_etl_pipeline.py` covers the source contract, transformations, rejects, persistence, watcher, and release gate. |
| Validate a build before release | The CI workflow runs the test suite, reloads the generated fixture, and runs the release gate. |
| Review and share test results | Pytest writes a JUnit XML report that CI uploads as an artifact. |
| Document defects | `docs/defect-log-template.md` is available for recording reproducible findings. The corrupted-target cases are intentional negative tests, not claims of production defects. |

### Manual smoke checklist

1. Generate the fixture and confirm that it contains 20,020 source rows.
2. Run the ETL command and confirm 15 rejects, 5 duplicates removed, 20,000
   rows loaded, and the accounting invariant holds.
3. Run the release gate and confirm every check passes.
4. Inspect `data/rejects.csv` and confirm each rejected row has one reason.
5. Run pytest and confirm the JUnit report is written to
   `test-results/pytest-results.xml`.
