# Fynd Order ETL and Checkout Demo

A local practice project that connects a small online shop to a tested order
data pipeline. It demonstrates how to validate order data, reject bad rows,
load reliable records into SQLite, and verify that a customer sees the order
that was actually saved.

## Watch the project overview

<video controls preload="metadata" width="100%">
  <source src="https://raw.githubusercontent.com/prakashmmali2/ETL_Data-Pipeline-for-Fynd/main/docs/Project%20Overview%20Video.mp4" type="video/mp4">
  Your browser does not support embedded video.
</video>

[Open or download the video](docs/Project%20Overview%20Video.mp4)

This is a synthetic-data learning project. It is not connected to Fynd
production systems or an unpublished FyndHacks challenge.

## Goal

Show two complementary workflows:

1. **ETL quality workflow:** take a CSV of order lines, validate and transform
   it, explain rejected rows, load valid rows to SQLite, and check the result.
2. **Customer checkout workflow:** add products in a browser, submit an order
   to a local Python service, pass it through the same ETL and SQLite checks,
   then display a confirmation from the saved data.

## How it works

```text
Sample CSV ----------------------> ETL -> rejects.csv
                                      -> SQLite -> release checks

Browser shop -> local Python API -> order CSV -> ETL -> SQLite
                                                   -> saved-order confirmation
```

The shop and sample CSV are separate input paths into the pipeline. Both use
the same order validation and SQLite storage rules.

### ETL steps

1. Generate or read order-line records from CSV.
2. Check the required columns and normalize values, including timestamps.
3. Reject invalid rows with reasons in a separate CSV.
4. Resolve duplicate `(order_id, sku)` lines by keeping the latest update.
   The same SKU in different orders remains separate.
5. Upsert valid rows into SQLite using `(order_id, sku)` as the identity.
6. Run data-quality checks and reconcile every input row:

   ```text
   rows_read = rows_rejected + duplicates_removed + rows_loaded
   ```

### Checkout steps

1. The browser loads six synthetic products and fixed prices from
   `checkout/catalog.json`.
2. A customer edits quantities, removes products, and enters a required name.
3. The local service validates the request and gets prices from the catalog;
   it does not trust prices supplied by the browser.
4. The service appends order lines to CSV, runs ETL and SQLite quality checks,
   then reads the saved order back from SQLite.
5. The confirmation page shows the saved order reference, products, quantities,
   and total.

## Quick start

Requires Python 3.10 or later. From the repository directory, install the
dependencies:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Run the sample ETL pipeline

These commands regenerate the sample CSV and update the database and rejects
files in `data/`:

```powershell
python -m src.generate_data --output data/orders.csv
python -m src.etl_pipeline data/orders.csv --database data/orders.sqlite --rejects data/rejects.csv
python -m src.report --database data/orders.sqlite
```

The release check prints each result and exits with an error if a quality
check fails.

### Run the shop

Start the local service from the repository directory:

```powershell
python -m src.store_server --host 127.0.0.1 --port 8000 --data-dir data/store
```

Open <http://127.0.0.1:8000>. Place a test order to see it pass through ETL and
open its saved-order confirmation. Runtime order files are written under
`data/store/`, which is git-ignored. Stop the service with Ctrl+C.

### Publish a free evaluator demo

The repository includes [`render.yaml`](render.yaml) for a Render Free web
service. To publish it:

1. Sign in to Render and choose **New > Blueprint**.
2. Connect `prakashmmali2/ETL_Data-Pipeline-for-Fynd` and deploy the Blueprint.
3. When the deploy is live, open the public `onrender.com` URL shown in the
   Render dashboard and share that link.

The service binds to Render's assigned port and stores demo orders under
`/tmp/fynd-etl-store`. Render Free services sleep after 15 minutes without
traffic, and the first request after sleep can take about a minute to wake the
service. Local CSV and SQLite changes are erased when the service sleeps,
restarts, or redeploys. The shop can still be tested by placing a fresh order
after it wakes, but this setup is not for retaining order history or real
customer data.

## Tests and recorded results

Run all ETL and browser tests:

```powershell
python -m pytest -q --junitxml=test-results/pytest-results.xml
```

To run only the browser checks:

```powershell
python -m pytest -q tests/test_checkout_browser.py
```

The browser tests use fresh contexts and temporary order data. They cover
successful checkout, missing-name and empty-cart validation, exact quantity
totals, item removal, repeat clicks, fixed-price enforcement, persistence,
and reuse of a SKU across separate orders.

The latest recorded validation (2026-11-24) reports:

| Result | Count |
|---|---:|
| Generated sample input rows | 20,020 |
| Invalid rows rejected | 15 |
| Duplicate order lines removed | 5 |
| Rows loaded into SQLite | 20,000 |
| ETL tests passed | 39 |
| Checkout browser tests passed | 8 |
| Combined tests passed | 47 |

The release gate passed. No checkout defects were observed in the automated
checks. Manual checks are documented but were **not run**; see the checkout
test plan for steps and expected outcomes.

## Project map

| Path | Purpose |
|---|---|
| `checkout/` | Product catalog, shop page, and order confirmation page |
| `src/store_server.py` | Local web/API service connecting checkout to ETL |
| `src/generate_data.py` | Deterministic synthetic ETL fixture generator |
| `src/etl_pipeline.py` | CSV validation, transformation, deduplication, and SQLite load |
| `src/dq_checks.py` | SQLite data-quality and release checks |
| `src/report.py` | Command-line release gate |
| `render.yaml` | Free Render web-service configuration |
| `data/` | Sample CSV, rejects, and SQLite output |
| `tests/` | ETL and Playwright browser tests |
| `docs/checkout-test-plan.md` | Checkout risks, cases, and manual test status |
| `docs/test-plan.md` | ETL test plan |
| `docs/validation-results.md` | Detailed recorded test and data results |
| `docs/Project Overview Video.mp4` | 7:39 animated walkthrough with a male Indian-English neural voice |

## Scope and limitations

- The shop, API, CSV files, and SQLite database run locally; the service binds
  to loopback by default.
- There are no payments, user accounts, shipping, cloud deployment, or
  production integrations.
- All products, customers, and orders are synthetic.
- Rebuilding the walkthrough video requires internet access for the
  `edge-tts` speech service. The narration is generated from the project
  script; no order or customer data is sent for narration.

See the [checkout test plan](docs/checkout-test-plan.md), [ETL test plan](docs/test-plan.md),
[validation details](docs/validation-results.md), and
[submission checklist](docs/submission-checklist.md) for more information.
