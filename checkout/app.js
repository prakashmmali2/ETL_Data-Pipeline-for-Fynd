"use strict";

const products = [
  { id: "tote", name: "Canvas Tote", priceCents: 2450 },
  { id: "mug", name: "Stoneware Mug", priceCents: 1200 },
];

const cart = new Map();
const cartList = document.querySelector("#cart-items");
const emptyCartMessage = document.querySelector("#empty-cart");
const orderTotal = document.querySelector("#order-total");
const checkoutForm = document.querySelector("#checkout-form");
const nameInput = document.querySelector("#customer-name");
const errorMessage = document.querySelector("#checkout-error");
const placeOrderButton = document.querySelector("#place-order");
const confirmation = document.querySelector("#order-confirmation");
const confirmationTitle = document.querySelector("#confirmation-title");
const confirmationReference = document.querySelector("#confirmation-reference");
let orderPlaced = false;

function formatPrice(priceCents) {
  return `$${(priceCents / 100).toFixed(2)}`;
}

function getProduct(productId) {
  return products.find((product) => product.id === productId);
}

function renderCart() {
  cartList.replaceChildren();
  emptyCartMessage.hidden = cart.size !== 0;

  for (const [productId, quantity] of cart) {
    const product = getProduct(productId);
    const item = document.createElement("li");
    item.className = "cart-item";
    item.dataset.productId = product.id;

    const details = document.createElement("div");
    const name = document.createElement("div");
    name.className = "cart-item-name";
    name.textContent = product.name;
    const unitPrice = document.createElement("div");
    unitPrice.className = "cart-item-unit";
    unitPrice.textContent = `${formatPrice(product.priceCents)} each`;
    details.append(name, unitPrice);

    const lineTotal = document.createElement("span");
    lineTotal.className = "line-total";
    lineTotal.dataset.testid = `line-total-${product.id}`;
    lineTotal.textContent = formatPrice(product.priceCents * quantity);

    const controls = document.createElement("div");
    controls.className = "cart-controls";
    controls.append(
      makeQuantityButton("decrease", product, "−", quantity <= 1),
    );

    const quantityValue = document.createElement("span");
    quantityValue.className = "quantity-value";
    quantityValue.dataset.testid = `quantity-${product.id}`;
    quantityValue.textContent = String(quantity);
    controls.append(quantityValue);
    controls.append(makeQuantityButton("increase", product, "+"));

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "remove-button";
    removeButton.dataset.cartAction = "remove";
    removeButton.dataset.productId = product.id;
    removeButton.setAttribute("aria-label", `Remove ${product.name} from cart`);
    removeButton.textContent = "Remove";
    removeButton.disabled = orderPlaced;
    controls.append(removeButton);

    item.append(details, lineTotal, controls);
    cartList.append(item);
  }

  const totalCents = [...cart].reduce((sum, [productId, quantity]) => {
    return sum + getProduct(productId).priceCents * quantity;
  }, 0);
  orderTotal.textContent = formatPrice(totalCents);

  document.querySelectorAll("[data-add-product]").forEach((button) => {
    button.disabled = orderPlaced;
  });
}

function makeQuantityButton(action, product, text, disabled = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "quantity-button";
  button.dataset.cartAction = action;
  button.dataset.productId = product.id;
  button.setAttribute(
    "aria-label",
    `${action === "increase" ? "Increase" : "Decrease"} quantity of ${product.name}`,
  );
  button.textContent = text;
  button.disabled = orderPlaced || disabled;
  return button;
}

function showError(message, nameIsInvalid = false) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
  if (nameIsInvalid) {
    nameInput.setAttribute("aria-invalid", "true");
    nameInput.focus();
  }
}

function clearError() {
  errorMessage.textContent = "";
  errorMessage.hidden = true;
  nameInput.removeAttribute("aria-invalid");
}

document.querySelectorAll("[data-add-product]").forEach((button) => {
  button.addEventListener("click", () => {
    if (orderPlaced) {
      return;
    }

    const productId = button.dataset.addProduct;
    cart.set(productId, (cart.get(productId) ?? 0) + 1);
    clearError();
    renderCart();
  });
});

cartList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-cart-action]");
  if (!button || orderPlaced) {
    return;
  }

  const productId = button.dataset.productId;
  const quantity = cart.get(productId);
  if (button.dataset.cartAction === "remove" || (button.dataset.cartAction === "decrease" && quantity === 1)) {
    cart.delete(productId);
  } else if (button.dataset.cartAction === "increase") {
    cart.set(productId, quantity + 1);
  } else if (button.dataset.cartAction === "decrease") {
    cart.set(productId, quantity - 1);
  }

  clearError();
  renderCart();
});

nameInput.addEventListener("input", () => {
  if (nameInput.value.trim()) {
    clearError();
  }
});

checkoutForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (orderPlaced) {
    return;
  }

  if (cart.size === 0) {
    showError("Your cart is empty. Add at least one item before placing your order.");
    return;
  }

  const customerName = nameInput.value.trim();
  if (!customerName) {
    showError("Enter your name to place the order.", true);
    return;
  }

  orderPlaced = true;
  clearError();
  renderCart();
  nameInput.disabled = true;
  placeOrderButton.disabled = true;

  const reference = `ORD-${Date.now().toString(36).toUpperCase()}`;
  confirmationTitle.textContent = `Order confirmed for ${customerName}.`;
  confirmationReference.textContent = `Reference: ${reference}`;
  confirmation.hidden = false;
});

renderCart();
