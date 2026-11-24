# Shop checkout test plan and results

## Scope and priorities

The local Fieldnotes Supply demo has six synthetic, fixed-price products. It
has no payment, shipping, account, or external-service integration. A small
Python service accepts an order, derives prices from the shared product
catalog, appends order lines to CSV, runs the ETL pipeline and release checks,
then supplies the saved order to a separate confirmation page.

| Priority | Risk |
|---|---|
| P1 | Wrong amount, tampered price, or a duplicate order on a rapid repeat click |
| P1 | An empty cart or missing name creates an order |
| P1 | Reusing a SKU in a later order overwrites an earlier customer order |
| P2 | Quantity, removal, or persistence errors show stale order details |

Every automated browser case opens a fresh browser context and verifies the
empty bag and `$0.00` total before starting. The server-side test data is kept
in a temporary directory.

## Automated cases

| ID | Scenario and steps | Expected result |
|---|---|---|
| CHK-01 | Add a Canvas Tote, enter a name, and place the order. | The separate confirmation page shows the customer, reference, saved product, quantity, and `$24.50`; SQLite contains the same ETL-loaded row. |
| CHK-02 | Add a Stoneware Mug and leave the name blank. | A clear name error appears; the mug, quantity, and `$12.00` remain; no order is submitted. |
| CHK-03 | Add a Canvas Tote and raise quantity to three. | Quantity is 3; line and order totals both equal `$73.50`. |
| CHK-04 | Enter a name, leave the bag empty, and place the order. | Empty-bag validation appears; the name remains, total stays `$0.00`, and no order is created. |
| CHK-05 | Add a Field Notebook, enter a name, and rapidly double-click Place Order. | One order/reference is persisted and one confirmation is shown. |
| CHK-06 | Place two separate orders for the Stoneware Mug. | Both customer orders remain in the database with the same SKU. |
| CHK-07 | Add two products, then remove one. | The removed product disappears and the total reflects only the remaining item. |
| CHK-08 | Submit an order with a forged client-side price. | The saved total uses the fixed catalog price, not the submitted value. |

Run the checkout checks after installing requirements and Chromium:

```powershell
python -m playwright install chromium
python -m pytest -q tests/test_checkout_browser.py
```

Run the complete ETL and checkout suite with:

```powershell
python -m pytest -q --junitxml=test-results/pytest-results.xml
```

## Manual checks

Start the integrated service from the project root:

```powershell
python -m src.store_server --host 127.0.0.1 --port 8000 --data-dir data/store
```

Open <http://127.0.0.1:8000>.

| ID | Steps | Expected result |
|---|---|---|
| MAN-01 | Enter a name, leave the bag empty, and click Place your order. | Empty-bag error; no confirmation; name remains and total is `$0.00`. |
| MAN-02 | Add a product, enter a name, and rapidly double-click Place your order. | One confirmation/reference and one saved order. |
| MAN-03 | Add two products, then remove one. | The removed product disappears and the total reflects only the remaining item. |
| MAN-04 | Complete an order and refresh its confirmation URL. | The same persisted order details and total are retrieved from SQLite. |

Manual checks above are documented for reproducibility; they are not reported
as manually run. Automated browser tests exercise the empty-bag, double-click,
removal/quantity, persistence, and same-SKU scenarios.

## Results

Executed on 2026-11-24 with Python 3.12.10, Playwright 1.65.2, and Chromium
159:

- Automated browser checks: **8 passed**.
- Full ETL and browser suite: **47 passed**.
- Confirmed checkout rows were visible on the separate page and present in the
  ETL-loaded SQLite database.
- Two separate customers ordering the same SKU remained separate order rows.
- Empty-cart and rapid double-click browser checks passed.
- Checkout defects observed in these checks: **None**.
- Manual desktop checks: **Not run**; use MAN-01 through MAN-04 to reproduce.

The checkout is a local learning demo and does not represent a production
payment/order system.
