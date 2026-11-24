"use strict";

const cart = new Map();
const products = new Map();
const productList = document.querySelector("#product-list");
const productCount = document.querySelector("#product-count");
const catalogError = document.querySelector("#catalog-error");
const cartList = document.querySelector("#cart-items");
const emptyCartMessage = document.querySelector("#empty-cart");
const orderTotal = document.querySelector("#order-total");
const checkoutForm = document.querySelector("#checkout-form");
const nameInput = document.querySelector("#customer-name");
const errorMessage = document.querySelector("#checkout-error");
const placeOrderButton = document.querySelector("#place-order");
const bagCount = document.querySelector("#bag-count");
const bagLink = document.querySelector(".bag-link");
let orderInProgress = false;

function formatPrice(priceCents) {
  return `$${(priceCents / 100).toFixed(2)}`;
}

function showError(element, message) {
  element.textContent = message;
  element.hidden = false;
}

function clearCheckoutError() {
  errorMessage.textContent = "";
  errorMessage.hidden = true;
  nameInput.removeAttribute("aria-invalid");
}

function makeProductCard(product) {
  const article = document.createElement("article");
  article.className = "product-card";
  article.dataset.productId = product.id;

  const art = document.createElement("div");
  art.className = `product-art tone-${product.tone}`;
  art.setAttribute("aria-hidden", "true");
  const tag = document.createElement("span");
  tag.className = "product-tag";
  tag.textContent = product.tag;
  const illustration = document.createElement("span");
  illustration.className = "product-illustration";
  illustration.textContent = product.icon;
  const artNumber = document.createElement("span");
  artNumber.className = "art-number";
  artNumber.textContent = String(products.size).padStart(2, "0");
  art.append(tag, illustration, artNumber);

  const info = document.createElement("div");
  info.className = "product-info";
  const category = document.createElement("p");
  category.className = "product-category";
  category.textContent = product.category;
  const titleRow = document.createElement("div");
  titleRow.className = "product-title-row";
  const title = document.createElement("h3");
  title.textContent = product.name;
  const price = document.createElement("span");
  price.className = "product-price";
  price.textContent = formatPrice(product.price_cents);
  titleRow.append(title, price);
  const description = document.createElement("p");
  description.className = "product-description";
  description.textContent = product.description;
  const addButton = document.createElement("button");
  addButton.className = "add-button";
  addButton.type = "button";
  addButton.dataset.addProduct = product.id;
  addButton.setAttribute("aria-label", `Add ${product.name} to cart`);
  const buttonText = document.createElement("span");
  buttonText.textContent = "Add to bag";
  const plus = document.createElement("span");
  plus.className = "add-icon";
  plus.setAttribute("aria-hidden", "true");
  plus.textContent = "+";
  addButton.append(buttonText, plus);
  info.append(category, titleRow, description, addButton);
  article.append(art, info);
  return article;
}

function getItemCount() {
  return [...cart.values()].reduce((sum, quantity) => sum + quantity, 0);
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
  button.disabled = disabled || orderInProgress;
  return button;
}

function renderCart() {
  cartList.replaceChildren();
  emptyCartMessage.hidden = cart.size !== 0;
  let totalCents = 0;

  for (const [productId, quantity] of cart) {
    const product = products.get(productId);
    if (!product) {
      continue;
    }
    const lineTotalCents = product.price_cents * quantity;
    totalCents += lineTotalCents;
    const item = document.createElement("li");
    item.className = "cart-item";
    item.dataset.productId = product.id;

    const thumb = document.createElement("span");
    thumb.className = `cart-thumb tone-${product.tone}`;
    thumb.setAttribute("aria-hidden", "true");
    thumb.textContent = product.icon;
    const details = document.createElement("div");
    details.className = "cart-item-details";
    const name = document.createElement("span");
    name.className = "cart-item-name";
    name.textContent = product.name;
    const unitPrice = document.createElement("span");
    unitPrice.className = "cart-item-unit";
    unitPrice.textContent = `${formatPrice(product.price_cents)} each`;
    details.append(name, unitPrice);

    const lineTotal = document.createElement("span");
    lineTotal.className = "line-total";
    lineTotal.dataset.testid = `line-total-${product.id}`;
    lineTotal.textContent = formatPrice(lineTotalCents);
    const controls = document.createElement("div");
    controls.className = "cart-controls";
    controls.append(makeQuantityButton("decrease", product, "−", quantity <= 1));
    const quantityValue = document.createElement("span");
    quantityValue.className = "quantity-value";
    quantityValue.dataset.testid = `quantity-${product.id}`;
    quantityValue.textContent = String(quantity);
    controls.append(quantityValue, makeQuantityButton("increase", product, "+"));

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "remove-button";
    removeButton.dataset.cartAction = "remove";
    removeButton.dataset.productId = product.id;
    removeButton.setAttribute("aria-label", `Remove ${product.name} from cart`);
    removeButton.textContent = "Remove";
    removeButton.disabled = orderInProgress;
    controls.append(removeButton);
    item.append(thumb, details, lineTotal, controls);
    cartList.append(item);
  }

  const count = getItemCount();
  bagCount.textContent = String(count);
  bagLink.setAttribute("aria-label", `Your bag, ${count} item${count === 1 ? "" : "s"}`);
  document.querySelector("#bag-heading-count").textContent = `(${count})`;
  orderTotal.textContent = formatPrice(totalCents);
  productList.querySelectorAll("button[data-add-product]").forEach((button) => {
    button.disabled = orderInProgress;
  });
}

async function loadProducts() {
  try {
    const response = await fetch("/api/products");
    if (!response.ok) {
      throw new Error("The collection could not be loaded. Please refresh to try again.");
    }
    const catalog = await response.json();
    if (!Array.isArray(catalog) || catalog.length === 0) {
      throw new Error("The collection is currently empty.");
    }
    catalog.forEach((product) => {
      products.set(product.id, product);
      productList.append(makeProductCard(product));
    });
    productCount.textContent = `${catalog.length} thoughtful finds`;
    renderCart();
  } catch (error) {
    showError(catalogError, error.message);
    productCount.textContent = "Collection unavailable";
  }
}

productList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-add-product]");
  if (!button || orderInProgress) {
    return;
  }
  const productId = button.dataset.addProduct;
  cart.set(productId, (cart.get(productId) || 0) + 1);
  clearCheckoutError();
  renderCart();
});

cartList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-cart-action]");
  if (!button || orderInProgress) {
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
  clearCheckoutError();
  renderCart();
});

nameInput.addEventListener("input", () => {
  if (nameInput.value.trim()) {
    clearCheckoutError();
  }
});

checkoutForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (orderInProgress) {
    return;
  }
  if (cart.size === 0) {
    showError(errorMessage, "Your bag is empty. Add something lovely before checking out.");
    return;
  }
  const customerName = nameInput.value.trim();
  if (!customerName) {
    showError(errorMessage, "Enter your name so we can make out your order.");
    nameInput.setAttribute("aria-invalid", "true");
    nameInput.focus();
    return;
  }

  orderInProgress = true;
  placeOrderButton.disabled = true;
  nameInput.disabled = true;
  placeOrderButton.querySelector("span:first-child").textContent = "Saving your order…";
  renderCart();
  try {
    const response = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        customer_name: customerName,
        items: [...cart].map(([productId, quantity]) => ({
          product_id: productId,
          quantity,
        })),
      }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Your order could not be saved. Please try again.");
    }
    window.location.assign(`confirmation.html?order_id=${encodeURIComponent(result.order_id)}`);
  } catch (error) {
    orderInProgress = false;
    placeOrderButton.disabled = false;
    nameInput.disabled = false;
    placeOrderButton.querySelector("span:first-child").textContent = "Place your order";
    renderCart();
    showError(errorMessage, error.message);
  }
});

renderCart();
loadProducts();
