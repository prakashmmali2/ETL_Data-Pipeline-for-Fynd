# Order ETL Data Pipeline - Test Automation & Quality Engineering

## Project overview

This project demonstrates the development and testing of a small ETL
(Extract, Transform, Load) pipeline using Python, CSV, and SQLite.

The pipeline reads order lines from a CSV file, validates and transforms
records, handles duplicate order/SKU lines, separates invalid records with
rejection reasons, and stores valid data in an SQLite database. The focus is
software testing, data quality, and release validation using practical SDET
workflows.

The local shop demo also sends synthetic customer orders through the same ETL
validation and SQLite quality gate before showing an order confirmation. This
is a practice project; it is not connected to Fynd production systems or an
official FyndHacks solution.

## Tech stack

| Area | Technology |
|---|---|
| Programming | Python 3.10+ |
| Database | SQLite |
| Data format | CSV |
| Testing | pytest |
| Browser tests | Playwright + Chromium |
| CI/CD | GitHub Actions |
| Test reporting | JUnit XML |

## Project workflow

The generated ETL fixture and the local shop are two complementary input
workflows. The shop-to-ETL connection is local and synchronous for this demo.

### ETL data-quality workflow

1. Generate deterministic synthetic order data.
2. Read the CSV and validate its order-line schema.
3. Normalize and validate each row.
4. Reject invalid rows with clear reasons.
5. Resolve duplicate `(order_id, sku)` lines deterministically, keeping the
   latest update. The same SKU in different orders is preserved.
6. Load valid records into SQLite using a composite-key upsert.
7. Check row accounting, data quality, and release readiness.
8. Run automated tests and produce a JUnit report.

### Shop-to-ETL workflow

1. Load six fixed-price synthetic products from `checkout/catalog.json`.
2. Change quantities or remove items and verify the displayed totals.
3. Enter a required customer name. The local Python service rechecks products,
   quantities, and prices on the server; the browser never chooses the price.
4. Save order lines to `data/store/store_orders.csv`, run the ETL pipeline,
   and validate the resulting SQLite table.
5. Show a separate confirmation page using the order retrieved from SQLite.
6. Run isolated Playwright checks in Chromium.

The store service is a local learning demo, not a production order service:
orders are written to local files, there is no payment, login, shipping, or
cloud deployment, and the request handler is intended to run only on the
loopback interface.

## Setup and execution

Clone the repository and navigate to the project directory:

```powershell
git clone https://github.com/prakashmmali2/ETL_Data-Pipeline-for-Fynd.git
cd ETL_Data-Pipeline-for-Fynd
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Generate the sample data:

```powershell
python -m src.generate_data --output data/orders.csv
```

Run the ETL pipeline:

```powershell
python -m src.etl_pipeline data/orders.csv --database data/orders.sqlite --rejects data/rejects.csv
```

Generate the quality report:

```powershell
python -m src.report --database data/orders.sqlite
```

Install Playwright's Chromium browser once before running browser tests:

```powershell
python -m playwright install chromium
```

Run the automated tests and write a JUnit XML report:

```powershell
python -m pytest -q --junitxml=test-results/pytest-results.xml
```

## Data quality validation

The generated sample contains 20,020 rows. A normal run produces:

| Validation | Expected result |
|---|---:|
| Total records read | 20,020 |
| Rejected records | 15 |
| Duplicate records removed | 5 |
| Successfully loaded records | 20,000 |

Every input row must be accounted for:

```text
rows_read = rows_rejected + duplicates_removed + rows_loaded
```

The fixture includes valid boundary values such as quantity 1, a zero price,
and timestamps with different UTC offsets. Accepted timestamps are stored in
UTC. Invalid rows and their rejection reasons are written to
`data/rejects.csv`.

The release check verifies the SQLite schema, row count, required values, SKU
uniqueness within an order, and numeric ranges, including integral quantities
and finite prices. It exits with an error if a check fails. The tests cover
the CSV contract, transformations, duplicate handling, legacy-table
migration, upserts, rejects, quality checks, and the optional watcher.
GitHub Actions runs the tests and release check; the JUnit report is uploaded
as a workflow artifact.

## Local shop and checkout demo

The `checkout/` page has a responsive product collection, editable bag, name
validation, exact fixed-price totals, and an order-details confirmation page.
The Python service is the small bridge from the shop to ETL. Each accepted
order is appended to a raw CSV, validated and loaded into the composite-key
SQLite table, then read back for its confirmation page. The same product can
appear in many customer orders without overwriting earlier ones.

Start the shop service from the repository root:

```powershell
python -m src.store_server --host 127.0.0.1 --port 8000 --data-dir data/store
```

Open <http://127.0.0.1:8000> in a browser. Completed synthetic orders are
available in `data/store/store_orders.csv` and
`data/store/store_orders.sqlite`; that local runtime folder is git-ignored.
The catalog and prices are maintained in `checkout/catalog.json`.

Install Chromium as described in [Setup and execution](#setup-and-execution)
before running the checkout browser tests. The browser checks run the local
service with a temporary data directory:

```powershell
python -m pytest -q tests/test_checkout_browser.py
```

The automated cases cover successful saved orders, missing names, exact
quantity totals, empty carts, rapid repeat clicks, and the same SKU in separate
customer orders.

Run the ETL and checkout tests together and save their JUnit report:

```powershell
python -m pytest -q --junitxml=test-results/pytest-results.xml
```

The [checkout test plan and results](docs/checkout-test-plan.md) document
automated coverage and the manual empty-cart and rapid double-click checks.

## Walkthrough video

The [animated project walkthrough](docs/Project%20Overview%20Video.mp4) tells
the end-to-end story: overall project scope, the storefront, checkout,
order-to-ETL flow, transformation, composite order-line keys, SQLite,
accounting, quality checks, and browser/ETL tests. It uses a male
Indian-English neural voice in the requested style and animated illustrations
rather than static presentation slides. The original source video is retained.

Rebuild the animated video from the project directory with:

```powershell
python -m pip install -r requirements.txt
python docs\generate_indian_walkthrough.py
```

The video generator uses `en-IN-PrabhatNeural` through `edge-tts`; rebuilding
requires an internet connection to the speech service. The narration is
synthesized from the script in the generator. No project data or customer
records are sent for narration.

The [ETL test plan](docs/test-plan.md) describes expected behavior and manual
checks. The [checkout test plan and results](docs/checkout-test-plan.md) records
the browser and manual checkout outcomes. The
[validation results](docs/validation-results.md) summarize the dataset and
combined test runs. The [defect log template](docs/defect-log-template.md) is
provided for recording findings. See the
[submission checklist](docs/submission-checklist.md) for evidence requirements
and the walkthrough outline.

## Watch mode

To try the local append demo:

```powershell
python -m src.etl_pipeline data/orders.csv --database data/orders.sqlite --rejects data/rejects.csv --watch
```

Append complete CSV rows while it is running. The watcher reruns the full
batch when the file changes; it is not an incremental stream processor or a
production latency guarantee. Stop it with Ctrl+C.

## Before submitting to FyndHacks

This repository is a practice project, not a solution to an unpublished
FyndHacks use case. Read the use case provided for your registered track and
adapt the work to it before submitting. This project has not been evaluated
against the private challenge prompt. Review the walkthrough, upload it to
YouTube as Unlisted, add its URL to the submission form, and verify that
FyndHacks confirms the submission.

## Project files

- `src/generate_data.py` creates the deterministic sample CSV.
- `src/etl_pipeline.py` validates, transforms, and loads orders.
- `src/dq_checks.py` contains the SQLite quality checks.
- `src/report.py` runs the release check.
- `src/store_server.py` serves the demo shop and persists orders through ETL.
- `tests/` contains the automated tests.
- `docs/test-plan.md` describes the expected behavior and criteria.
- `checkout/` contains the product catalog, shop page, and confirmation page.
- `tests/test_checkout_browser.py` automates checkout behavior in Chromium.
- `docs/checkout-test-plan.md` records checkout risks, tests, and results.
- `docs/submission-checklist.md` lists submission steps and video topics.
- `.github/workflows/ci.yml` runs tests and the release check on GitHub.
