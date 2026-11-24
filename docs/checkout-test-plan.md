# Mini checkout test plan and results

## Scope and priorities

The standalone checkout demo has two fixed-price products: Canvas Tote at
$24.50 and Stoneware Mug at $12.00. It has no payment flow, backend, database,
or external service.

| Priority | Risk |
|---|---|
| P1 | Wrong line/order total or a duplicate order confirmation |
| P1 | Checkout proceeds with an empty cart or missing name |
| P2 | Quantity or remove controls lose cart state or show stale totals |

Each automated case uses a fresh browser context and first verifies an empty
cart and a `$0.00` order total.

## Automated cases

| ID | Scenario and steps | Expected customer-visible result |
|---|---|---|
| CHK-01 | Add a Canvas Tote, enter a name, and place the order. | One confirmation names the customer, includes an `ORD-` reference, and disables Place Order. |
| CHK-02 | Add a Stoneware Mug, leave the name blank, and place the order. | A clear name error appears; the mug, quantity, and `$12.00` total remain; no confirmation appears. |
| CHK-03 | Add a Canvas Tote and increase its quantity to three. | Quantity is 3 and both its line total and order total are exactly `$73.50`. |

Run the checkout checks after installing project requirements and Chromium:

```powershell
python -m playwright install chromium
python -m pytest -q tests/test_checkout_browser.py
```

Run the complete ETL and checkout suite with:

```powershell
python -m pytest -q --junitxml=test-results/pytest-results.xml
```

## Manual checks

Start the demo with `python -m http.server 8000 --directory checkout` and open
`http://127.0.0.1:8000`.

| ID | Steps | Expected result |
|---|---|---|
| MAN-01 | Enter a name, leave the cart empty, and click Place Order. | Empty-cart error; no confirmation; the name remains and total stays `$0.00`. |
| MAN-02 | Add a product, enter a name, and rapidly double-click Place Order. | Exactly one confirmation/reference; Place Order becomes disabled. |
| MAN-03 | Add both products, then remove the Canvas Tote. | Only the mug remains and the total is `$12.00`. |

## Results

Executed on 2026-11-24 using Python 3.11.9 and Playwright Chromium 159 on the
local demo:

- Automated: **3 passed** (`tests/test_checkout_browser.py`).
- MAN-01: **Passed**. The empty-cart message appeared, the entered name
  remained, the total was `$0.00`, and no confirmation was shown.
- MAN-02: **Passed**. One confirmation and reference appeared; Place Order was
  disabled.
- MAN-03: **Passed**. Removing the tote left the mug and a `$12.00` total.
- Checkout defects observed: **None** in these checks.

The automated assertions and the results above are the reproducible evidence.
These checks cover this local demo only, not a payment system or production
checkout.
