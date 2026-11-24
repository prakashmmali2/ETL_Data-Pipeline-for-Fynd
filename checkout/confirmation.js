"use strict";

const params = new URLSearchParams(window.location.search);
const orderId = params.get("order_id");
const loading = document.querySelector("#confirmation-loading");
const errorMessage = document.querySelector("#confirmation-error");
const confirmation = document.querySelector("#order-confirmation");
const itemsList = document.querySelector("#confirmed-items");

function formatPrice(priceCents) {
  return `$${(priceCents / 100).toFixed(2)}`;
}

function showError(message) {
  loading.hidden = true;
  errorMessage.textContent = message;
  errorMessage.hidden = false;
  document.querySelector("#back-home").hidden = false;
}

function renderOrder(order) {
  document.querySelector("#customer-name").textContent = order.customer_name;
  document.querySelector("#order-customer").textContent = order.customer_name;
  document.querySelector("#order-reference").textContent = order.order_id;
  document.querySelector("#order-date").textContent = new Date(order.order_timestamp).toLocaleString();
  document.querySelector("#confirmed-item-count").textContent =
    `${order.items.length} ${order.items.length === 1 ? "item" : "items"}`;
  document.querySelector("#confirmed-total").textContent = formatPrice(order.total_cents);

  for (const product of order.items) {
    const item = document.createElement("li");
    item.className = "confirmed-item";
    const thumb = document.createElement("span");
    thumb.className = `confirmed-thumb tone-${product.tone}`;
    thumb.setAttribute("aria-hidden", "true");
    thumb.textContent = product.icon;
    const details = document.createElement("div");
    details.className = "confirmed-item-details";
    const name = document.createElement("strong");
    name.textContent = product.name;
    const quantity = document.createElement("span");
    quantity.textContent = `${product.quantity} × ${formatPrice(product.unit_price_cents)}`;
    details.append(name, quantity);
    const lineTotal = document.createElement("strong");
    lineTotal.textContent = formatPrice(product.line_total_cents);
    item.append(thumb, details, lineTotal);
    itemsList.append(item);
  }
  loading.hidden = true;
  confirmation.hidden = false;
}

async function loadOrder() {
  if (!orderId) {
    showError("There’s no order reference in this link. Place an order first to see its details.");
    return;
  }
  try {
    const response = await fetch(`/api/orders/${encodeURIComponent(orderId)}`);
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "We couldn’t find that order.");
    }
    renderOrder(result);
  } catch (error) {
    showError(error.message);
  }
}

loadOrder();
