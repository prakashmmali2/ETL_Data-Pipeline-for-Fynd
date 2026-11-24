from __future__ import annotations

import re
import sqlite3
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest
from playwright.sync_api import Browser, Page, expect, sync_playwright

from src.store_server import create_handler


@pytest.fixture(scope="session")
def checkout_server(tmp_path_factory):
    data_directory = tmp_path_factory.mktemp("checkout-store")
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(data_directory))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/", data_directory
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def checkout_page(browser: Browser, checkout_server):
    checkout_url, _ = checkout_server
    context = browser.new_context()
    page = context.new_page()
    page.goto(checkout_url)
    expect(page.get_by_text("Your bag is waiting for something lovely.")).to_be_visible()
    expect(page.get_by_test_id("order-total")).to_have_text("$0.00")
    expect(page.locator(".product-card")).to_have_count(6)
    yield page
    context.close()


def place_order(page: Page, name: str, product: str = "Canvas Tote") -> None:
    page.get_by_role("button", name=f"Add {product} to cart").click()
    page.get_by_role("textbox", name="Name for your order").fill(name)
    page.get_by_role("button", name="Place your order").click()
    expect(page).to_have_url(re.compile(r"/confirmation\.html\?order_id=ORD-"))


def test_valid_checkout_shows_persisted_order_details_and_reference(
    checkout_page: Page, checkout_server
):
    _, data_directory = checkout_server
    place_order(checkout_page, "Jordan Lee", "Canvas Tote")

    expect(checkout_page.get_by_role("heading", name="Thank you, Jordan Lee.")).to_be_visible()
    expect(checkout_page.get_by_test_id("order-reference")).to_have_text(
        re.compile(r"^ORD-[A-F0-9]{12}$")
    )
    expect(checkout_page.get_by_text("Canvas Tote")).to_be_visible()
    expect(checkout_page.get_by_text("1 × $24.50")).to_be_visible()
    expect(checkout_page.get_by_test_id("confirmed-total")).to_have_text("$24.50")
    with sqlite3.connect(data_directory / "store_orders.sqlite") as db:
        stored_order = db.execute(
            "SELECT customer_name, sku, quantity, unit_price FROM orders WHERE customer_name = ?",
            ("Jordan Lee",),
        ).fetchone()
    assert stored_order == ("Jordan Lee", "TOTE", 1, 24.5)


def test_missing_name_blocks_checkout_and_preserves_cart(checkout_page: Page):
    checkout_page.get_by_role("button", name="Add Stoneware Mug to cart").click()
    checkout_page.get_by_role("button", name="Place your order").click()

    expect(checkout_page.get_by_role("alert")).to_have_text(
        "Enter your name so we can make out your order."
    )
    expect(checkout_page.get_by_role("textbox", name="Name for your order")).to_have_value("")
    expect(checkout_page.get_by_test_id("quantity-mug")).to_have_text("1")
    expect(checkout_page.get_by_test_id("order-total")).to_have_text("$12.00")
    expect(checkout_page).to_have_url(re.compile(r"/$"))


def test_quantity_change_updates_exact_line_and_order_totals(checkout_page: Page):
    checkout_page.get_by_role("button", name="Add Canvas Tote to cart").click()
    increase = checkout_page.get_by_role("button", name="Increase quantity of Canvas Tote")
    increase.click()
    increase.click()

    expect(checkout_page.get_by_test_id("quantity-tote")).to_have_text("3")
    expect(checkout_page.get_by_test_id("line-total-tote")).to_have_text("$73.50")
    expect(checkout_page.get_by_test_id("order-total")).to_have_text("$73.50")


def test_removing_a_product_recalculates_remaining_total(checkout_page: Page):
    checkout_page.get_by_role("button", name="Add Canvas Tote to cart").click()
    checkout_page.get_by_role("button", name="Add Stoneware Mug to cart").click()
    expect(checkout_page.get_by_test_id("order-total")).to_have_text("$36.50")
    checkout_page.get_by_role("button", name="Remove Stoneware Mug from cart").click()

    expect(checkout_page.get_by_test_id("quantity-tote")).to_have_text("1")
    expect(checkout_page.get_by_test_id("order-total")).to_have_text("$24.50")
    expect(checkout_page.get_by_test_id("quantity-mug")).to_have_count(0)


def test_order_api_uses_fixed_catalog_price(checkout_page: Page, checkout_server):
    checkout_url, _ = checkout_server
    response = checkout_page.request.post(
        f"{checkout_url}api/orders",
        data={
            "customer_name": "Price Check",
            "items": [{"product_id": "tote", "quantity": 1, "unit_price_cents": 1}],
        },
    )

    assert response.status == 201
    assert response.json()["total_cents"] == 2450


def test_empty_cart_blocks_checkout_and_preserves_name(checkout_page: Page):
    checkout_page.get_by_role("textbox", name="Name for your order").fill("Taylor Reed")
    checkout_page.get_by_role("button", name="Place your order").click()

    expect(checkout_page.get_by_role("alert")).to_have_text(
        "Your bag is empty. Add something lovely before checking out."
    )
    expect(checkout_page.get_by_role("textbox", name="Name for your order")).to_have_value(
        "Taylor Reed"
    )
    expect(checkout_page.get_by_test_id("order-total")).to_have_text("$0.00")
    expect(checkout_page).to_have_url(re.compile(r"/$"))


def test_rapid_double_click_creates_one_confirmation_and_order(checkout_page: Page, checkout_server):
    _, data_directory = checkout_server
    checkout_page.get_by_role("button", name="Add Field Notebook to cart").click()
    checkout_page.get_by_role("textbox", name="Name for your order").fill("Morgan Ellis")
    checkout_page.get_by_role("button", name="Place your order").dblclick(force=True)

    expect(checkout_page).to_have_url(re.compile(r"/confirmation\.html\?order_id=ORD-"))
    expect(checkout_page.locator("#order-confirmation")).to_be_visible()
    expect(checkout_page.get_by_test_id("order-reference")).to_have_count(1)
    with sqlite3.connect(data_directory / "store_orders.sqlite") as db:
        count = db.execute(
            "SELECT COUNT(DISTINCT order_id) FROM orders WHERE customer_name = ?",
            ("Morgan Ellis",),
        ).fetchone()[0]
    assert count == 1


def test_same_product_is_kept_for_two_separate_customer_orders(checkout_page: Page, browser: Browser, checkout_server):
    checkout_url, data_directory = checkout_server
    place_order(checkout_page, "Customer One", "Stoneware Mug")

    second_context = browser.new_context()
    second_page = second_context.new_page()
    second_page.goto(checkout_url)
    expect(second_page.locator(".product-card")).to_have_count(6)
    place_order(second_page, "Customer Two", "Stoneware Mug")

    expect(second_page.get_by_text("1 × $12.00")).to_be_visible()
    with sqlite3.connect(data_directory / "store_orders.sqlite") as db:
        rows = db.execute(
            "SELECT customer_name, sku FROM orders "
            "WHERE customer_name IN (?, ?) ORDER BY customer_name",
            ("Customer One", "Customer Two"),
        ).fetchall()
    second_context.close()
    assert rows == [("Customer One", "MUG"), ("Customer Two", "MUG")]
