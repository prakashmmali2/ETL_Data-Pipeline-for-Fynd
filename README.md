# Order ETL Data Pipeline - Test Automation & Quality Engineering

## Project overview

This project demonstrates the development and testing of a small ETL
(Extract, Transform, Load) pipeline using Python, CSV, and SQLite.

The pipeline reads order data from a CSV file, validates and transforms
records, handles duplicate SKUs, separates invalid records with rejection
reasons, and stores valid data in an SQLite database. The focus is software
testing, data quality, and release validation using practical SDET workflows.

This is a local practice project using synthetic data. It is not connected to
Fynd production systems or an official FyndHacks solution.

## Tech stack

| Area | Technology |
|---|---|
| Programming | Python 3.10+ |
| Database | SQLite |
| Data format | CSV |
| Testing | pytest |
| CI/CD | GitHub Actions |
| Test reporting | JUnit XML |

## Project workflow

1. Generate deterministic synthetic order data.
2. Read the CSV and validate its seven-column schema.
3. Normalize and validate each row.
4. Reject invalid rows with clear reasons.
5. Resolve duplicate SKUs deterministically, keeping the latest update.
6. Load valid records into SQLite using an upsert.
7. Check row accounting, data quality, and release readiness.
8. Run automated tests and produce a JUnit report.

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
uniqueness, and numeric ranges, including integral quantities and finite
prices. It exits with an error if a check fails. The tests cover the CSV
contract, transformations, duplicate handling, upserts, rejects, quality
checks, and the optional watcher. GitHub Actions runs the tests and release
check; the JUnit report is uploaded as a workflow artifact.

## Walkthrough video

The [animated project walkthrough](docs/Project%20Overview%20Video.mp4) uses
the original Indian-English narration and illustrates the ETL flow,
validation, duplicate resolution, SQLite upsert, row accounting, quality
checks, and test coverage. The original source video is retained.

Rebuild the animated video from the project directory with:

```powershell
python docs\generate_indian_walkthrough.py
```

The [test plan](docs/test-plan.md) describes expected behavior and manual
checks. The [defect log template](docs/defect-log-template.md) is provided for
recording findings. See the [submission checklist](docs/submission-checklist.md)
for evidence requirements and the walkthrough outline.

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
- `tests/` contains the automated tests.
- `docs/test-plan.md` describes the expected behavior and criteria.
- `docs/submission-checklist.md` lists submission steps and video topics.
- `.github/workflows/ci.yml` runs tests and the release check on GitHub.
