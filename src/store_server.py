"""Serve the local shop and persist confirmed orders through the ETL pipeline."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from src.dq_checks import check_table
from src.etl_pipeline import ORDER_COLUMNS, run_pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_DIRECTORY = PROJECT_ROOT / "checkout"
CATALOG_PATH = CHECKOUT_DIRECTORY / "catalog.json"


def load_catalog() -> list[dict[str, Any]]:
    with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)
    if not isinstance(catalog, list) or not catalog:
        raise ValueError("The product catalog must contain at least one product")
    seen_ids: set[str] = set()
    for product in catalog:
        if (
            not isinstance(product, dict)
            or not isinstance(product.get("id"), str)
            or not product["id"]
            or product["id"] in seen_ids
            or not isinstance(product.get("price_cents"), int)
            or product["price_cents"] < 0
        ):
            raise ValueError("The product catalog contains an invalid or duplicate product")
        seen_ids.add(product["id"])
    return catalog


def create_handler(data_directory: str | Path):
    data_path = Path(data_directory)
    data_path.mkdir(parents=True, exist_ok=True)
    source_csv = data_path / "store_orders.csv"
    database = data_path / "store_orders.sqlite"
    rejects_csv = data_path / "store_rejects.csv"
    order_lock = threading.Lock()

    class StoreRequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(CHECKOUT_DIRECTORY), **kwargs)

        def log_message(self, format: str, *args) -> None:
            pass

        def do_GET(self) -> None:
            request_path = urlsplit(self.path).path
            if request_path == "/api/products":
                self._send_json(200, load_catalog())
                return
            if request_path.startswith("/api/orders/"):
                self._get_order(unquote(request_path.removeprefix("/api/orders/")))
                return
            super().do_GET()

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/api/orders":
                self._send_json(404, {"error": "Endpoint not found."})
                return
            try:
                order = self._create_order()
            except ValueError as error:
                self._send_json(400, {"error": str(error)})
                return
            except (OSError, sqlite3.Error, RuntimeError) as error:
                self._send_json(500, {"error": f"Order could not be saved: {error}"})
                return
            self._send_json(201, order)

        def _create_order(self) -> dict[str, Any]:
            content_length = self.headers.get("Content-Length")
            if content_length is None:
                raise ValueError("Request body is required.")
            try:
                body_length = int(content_length)
            except ValueError as error:
                raise ValueError("Invalid request length.") from error
            if body_length < 1 or body_length > 16_384:
                raise ValueError("Request body must be between 1 and 16 KB.")
            try:
                payload = json.loads(self.rfile.read(body_length))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                raise ValueError("Request body must be valid JSON.") from error
            if not isinstance(payload, dict):
                raise ValueError("Order details are invalid.")

            customer_name = payload.get("customer_name")
            if not isinstance(customer_name, str) or not customer_name.strip():
                raise ValueError("Enter your name to place the order.")
            customer_name = customer_name.strip()
            if len(customer_name) > 80:
                raise ValueError("Name must be 80 characters or fewer.")

            items = payload.get("items")
            if not isinstance(items, list) or not items or len(items) > 50:
                raise ValueError("Add between 1 and 50 product lines.")
            catalog = load_catalog()
            products_by_id = {product["id"]: product for product in catalog}
            normalized_items = []
            seen_ids: set[str] = set()
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError("One or more cart items are invalid.")
                product_id = item.get("product_id")
                quantity = item.get("quantity")
                if (
                    not isinstance(product_id, str)
                    or product_id not in products_by_id
                    or product_id in seen_ids
                ):
                    raise ValueError("One or more cart products are unknown or duplicated.")
                if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 99:
                    raise ValueError("Each quantity must be a whole number from 1 to 99.")
                seen_ids.add(product_id)
                normalized_items.append((products_by_id[product_id], quantity))

            order_id = f"ORD-{uuid.uuid4().hex[:12].upper()}"
            guest_id = f"GUEST-{uuid.uuid4().hex[:12].upper()}"
            timestamp = (
                datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
            with order_lock:
                file_exists = source_csv.exists() and source_csv.stat().st_size > 0
                with source_csv.open("a", newline="", encoding="utf-8") as order_file:
                    writer = csv.DictWriter(order_file, fieldnames=ORDER_COLUMNS)
                    if not file_exists:
                        writer.writeheader()
                    for product, quantity in normalized_items:
                        writer.writerow(
                            {
                                "order_id": order_id,
                                "customer_id": guest_id,
                                "customer_name": customer_name,
                                "sku": product["id"],
                                "quantity": quantity,
                                "unit_price": f'{product["price_cents"] / 100:.2f}',
                                "order_timestamp": timestamp,
                                "updated_at": timestamp,
                            }
                        )

                result = run_pipeline(source_csv, database, rejects_csv)
                failed_checks = [
                    check for check in check_table(database) if not check.passed
                ]
                if failed_checks:
                    details = "; ".join(
                        f"{check.name}: {check.details}" for check in failed_checks
                    )
                    raise RuntimeError(f"Order data quality checks failed: {details}")
                if result.rows_rejected:
                    raise RuntimeError(
                        f"ETL rejected {result.rows_rejected} order row(s); see {rejects_csv}"
                    )
                order = self._read_order(order_id, catalog)
                if order is None:
                    raise RuntimeError("The confirmed order was not found after ETL processing")
                return order

        def _get_order(self, order_id: str) -> None:
            if not order_id or len(order_id) > 40:
                self._send_json(404, {"error": "Order not found."})
                return
            with order_lock:
                order = self._read_order(order_id, load_catalog())
            if order is None:
                self._send_json(404, {"error": "Order not found."})
                return
            self._send_json(200, order)

        @staticmethod
        def _read_order(order_id: str, catalog: list[dict[str, Any]]) -> dict[str, Any] | None:
            products_by_sku = {product["id"].upper(): product for product in catalog}
            if not database.exists():
                return None
            with sqlite3.connect(database) as connection:
                exists = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'orders'"
                ).fetchone()
                if not exists:
                    return None
                rows = connection.execute(
                    """
                    SELECT order_id, customer_id, customer_name, sku, quantity,
                           unit_price, order_timestamp
                    FROM orders
                    WHERE order_id = ?
                    ORDER BY sku
                    """,
                    (order_id,),
                ).fetchall()
            if not rows:
                return None
            items = []
            for row in rows:
                product = products_by_sku.get(row[3])
                if product is None:
                    raise RuntimeError(f"Product {row[3]!r} is no longer in the catalog")
                items.append(
                    {
                        "product_id": row[3],
                        "name": product["name"],
                        "icon": product["icon"],
                        "tone": product["tone"],
                        "quantity": row[4],
                        "unit_price_cents": int(round(row[5] * 100)),
                        "line_total_cents": int(round(row[5] * 100)) * row[4],
                    }
                )
            return {
                "order_id": rows[0][0],
                "customer_id": rows[0][1],
                "customer_name": rows[0][2],
                "order_timestamp": rows[0][6],
                "items": items,
                "total_cents": sum(item["line_total_cents"] for item in items),
            }

        def _send_json(self, status_code: int, payload: Any) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

    return StoreRequestHandler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-dir", type=Path, default=Path("data/store"))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), create_handler(args.data_dir))
    print(f"Shop demo: http://{args.host}:{server.server_port}", flush=True)
    print(f"ETL order data: {args.data_dir.resolve()}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
