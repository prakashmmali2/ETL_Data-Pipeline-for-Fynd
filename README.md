# Fynd Order ETL Demo

This project is a small, runnable ETL example built around synthetic order
data. It reads a CSV file, validates and cleans each row, writes invalid rows
to a rejects file, and loads valid orders into SQLite.

It is a local demo, not a connection to Fynd's production systems.

## Run it

Use Python 3.10 or later. From the project folder:

```powershell
python -m pip install -r requirements.txt
python -m src.generate_data --output data/orders.csv
python -m src.etl_pipeline data/orders.csv --database data/orders.sqlite --rejects data/rejects.csv
python -m src.report --database data/orders.sqlite
python -m pytest -q --junitxml=test-results\pytest-results.xml
```

The generated sample has 20,020 rows. A normal run reads all rows, rejects 15,
removes 5 duplicate SKUs, and loads 20,000 orders. The pipeline checks that
every input row is accounted for:

```text
rows_read = rows_rejected + duplicates_removed + rows_loaded
```

The fixture includes valid boundary values such as quantity 1, a zero price,
and timestamps with different UTC offsets. Accepted timestamps are stored in
UTC. Invalid rows and their rejection reasons are written to `data/rejects.csv`.

## Checks and tests

The release check verifies the SQLite table schema, row count, required values,
SKU uniqueness, and numeric ranges. It exits with an error if a check fails.
The test suite covers the CSV contract, transformations, duplicate handling,
upserts, rejects, quality checks, and the optional watcher.

## Watch mode

To try the local append demo:

```powershell
python -m src.etl_pipeline data/orders.csv --database data/orders.sqlite --rejects data/rejects.csv --watch
```

Append complete CSV rows while it is running. The watcher reruns the full
batch when the file changes; it is not an incremental stream processor or a
production latency guarantee. Stop it with Ctrl+C.

## Project files

- `src/generate_data.py` creates the deterministic sample CSV.
- `src/etl_pipeline.py` validates, transforms, and loads orders.
- `src/dq_checks.py` contains the SQLite quality checks.
- `src/report.py` runs the release check.
- `tests/` contains the automated tests.
- `docs/test-plan.md` describes the expected behavior and criteria.
- `.github/workflows/ci.yml` runs tests and the release check on GitHub.
