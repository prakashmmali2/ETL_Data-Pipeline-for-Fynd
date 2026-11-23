"""Generate a deterministic orders CSV with known quality defects."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from src.etl_pipeline import ORDER_COLUMNS


def generate_data(output_csv: str | Path) -> pd.DataFrame:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows: list[dict[str, object]] = []
    for index in range(19995):
        created = start + timedelta(minutes=index)
        rows.append(
            {
                "order_id": f"ORD-{index + 1:05d}",
                "customer_id": f"CUST-{index % 80 + 1:04d}",
                "sku": f"sku-{index + 1:05d}",
                "quantity": index % 8 + 1,
                "unit_price": round(4.99 + (index % 200) * 0.75, 2),
                "order_timestamp": created.isoformat(),
                "updated_at": created.isoformat(),
            }
        )

    # These arrive after the original records but carry newer update times.
    for index in range(5):
        row = rows[index].copy()
        newer = start + timedelta(days=2, minutes=index)
        row.update(
            {
                "order_id": f"ORD-LATE-{index + 1:03d}",
                "quantity": 20 + index,
                "updated_at": newer.isoformat(),
            }
        )
        rows.append(row)

    boundary_orders = [
        {
            "order_id": "ORD-EDGE-001",
            "customer_id": "CUST-EDGE-001",
            "sku": "sku-edge-001",
            "quantity": 1,
            "unit_price": 0.0,
            "order_timestamp": "2026-01-04T00:00:00+05:30",
            "updated_at": "2026-01-04T00:00:00+05:30",
        },
        {
            "order_id": "ORD-EDGE-002",
            "customer_id": "CUST-EDGE-002",
            "sku": "sku-edge-002",
            "quantity": 1000,
            "unit_price": 0.01,
            "order_timestamp": "2026-01-04T00:30:00-04:00",
            "updated_at": "2026-01-04T00:30:00-04:00",
        },
        {
            "order_id": "ORD-EDGE-003",
            "customer_id": "CUST-EDGE-003",
            "sku": "sku-edge-003",
            "quantity": 2,
            "unit_price": 999999.99,
            "order_timestamp": "2026-01-05T12:00:00Z",
            "updated_at": "2026-01-05T12:00:00Z",
        },
        {
            "order_id": "ORD-EDGE-004",
            "customer_id": "CUST-EDGE-004",
            "sku": "sku-edge-004",
            "quantity": 500,
            "unit_price": 12.5,
            "order_timestamp": "2026-01-05T09:00:00-07:00",
            "updated_at": "2026-01-05T09:00:00-07:00",
        },
        {
            "order_id": "ORD-EDGE-005",
            "customer_id": "CUST-EDGE-005",
            "sku": "sku-edge-005",
            "quantity": 10,
            "unit_price": 0.5,
            "order_timestamp": "2026-01-06T00:00:00Z",
            "updated_at": "2026-01-06T00:00:00Z",
        },
    ]
    rows.extend(boundary_orders)

    defects = [
        {"sku": " bad-001 ", "quantity": ""},
        {"sku": "BAD-002", "quantity": "zero"},
        {"sku": "BAD-003", "quantity": "-2"},
        {"sku": "BAD-004", "unit_price": "NaN"},
        {"sku": "BAD-005", "unit_price": "-1"},
        {"sku": "BAD-006", "order_timestamp": "not-a-date"},
        {"sku": "BAD-007", "updated_at": "yesterday-ish"},
        {"sku": "BAD-008", "customer_id": ""},
        {"sku": "BAD-009", "order_id": ""},
        {"sku": "BAD-010", "sku": ""},
        {"sku": "BAD-011", "quantity": "1.5"},
        {"sku": "BAD-012", "unit_price": ""},
        {"sku": "BAD-013", "order_timestamp": ""},
        {"sku": "BAD-014", "updated_at": ""},
        {"sku": "BAD-015", "quantity": "inf"},
    ]
    for index, defect in enumerate(defects):
        created = start + timedelta(days=3, minutes=index)
        row = {
            "order_id": f"ORD-BAD-{index + 1:03d}",
            "customer_id": "CUST-9999",
            "sku": f"bad-{index + 1:03d}",
            "quantity": 1,
            "unit_price": 9.99,
            "order_timestamp": created.isoformat(),
            "updated_at": created.isoformat(),
        }
        row.update(defect)
        rows.append(row)

    frame = pd.DataFrame(rows, columns=ORDER_COLUMNS)
    path = Path(output_csv)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/orders.csv"))
    args = parser.parse_args()
    frame = generate_data(args.output)
    print(f"Wrote {len(frame)} source rows to {args.output}")


if __name__ == "__main__":
    main()
