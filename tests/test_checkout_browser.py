from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from playwright.sync_api import Browser, Page, expect, sync_playwright


CHECKOUT_DIRECTORY = Path(__file__).resolve().parents[1] / "checkout"


class QuietRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass


@pytest.fixture(scope="session")
def checkout_url():
    handler = partial(QuietRequestHandler, directory=str(CHECKOUT_DIRECTORY))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
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
def checkout_page(browser: Browser, checkout_url: str):
    context = browser.new_context()
    page = context.new_page()
    page.goto(checkout_url)
    expect(page.get_by_text("Your cart is empty. Add something you love.")).to_be_visible()
    expect(page.get_by_test_id("order-total")).to_have_text("$0.00")
    yield page
    context.close()


def test_valid_checkout_shows_one_confirmation_and_reference(checkout_page: Page):
    checkout_page.get_by_role("textbox", name="Your name").fill("Jordan Lee")
    checkout_page.get_by_role("button", name="Add Canvas Tote to cart").click()
    checkout_page.get_by_role("button", name="Place order").click()

    status = checkout_page.get_by_role("status")
    expect(status).to_be_visible()
    expect(status).to_contain_text("Order confirmed for Jordan Lee.")
    expect(status).to_contain_text("Reference: ORD-")
    expect(status).to_have_count(1)
    expect(checkout_page.get_by_role("button", name="Place order")).to_be_disabled()


def test_missing_name_blocks_checkout_and_preserves_cart(checkout_page: Page):
    checkout_page.get_by_role("button", name="Add Stoneware Mug to cart").click()
    checkout_page.get_by_role("button", name="Place order").click()

    expect(checkout_page.get_by_role("alert")).to_have_text("Enter your name to place the order.")
    expect(checkout_page.get_by_role("textbox", name="Your name")).to_have_value("")
    expect(checkout_page.get_by_test_id("quantity-mug")).to_have_text("1")
    expect(checkout_page.get_by_test_id("order-total")).to_have_text("$12.00")
    expect(checkout_page.locator("#order-confirmation")).to_be_hidden()


def test_quantity_change_updates_exact_line_and_order_totals(checkout_page: Page):
    checkout_page.get_by_role("button", name="Add Canvas Tote to cart").click()
    increase = checkout_page.get_by_role("button", name="Increase quantity of Canvas Tote")
    increase.click()
    increase.click()

    expect(checkout_page.get_by_test_id("quantity-tote")).to_have_text("3")
    expect(checkout_page.get_by_test_id("line-total-tote")).to_have_text("$73.50")
    expect(checkout_page.get_by_test_id("order-total")).to_have_text("$73.50")
