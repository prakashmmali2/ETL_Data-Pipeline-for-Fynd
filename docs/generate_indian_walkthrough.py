from __future__ import annotations

import asyncio
import bisect
import math
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
from edge_tts.exceptions import NoAudioReceived


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = DOCS / "Project Overview Video.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = "en-IN-PrabhatNeural"
VOICE_RATE = "+3%"

W, H = 1280, 720
FPS = 12
OUTPUT_FPS = 24
INK = "#26362F"
MUTED = "#747B70"
PAPER = "#F6F4ED"
PANEL = "#FFFEFA"
LINE = "#E4E1D6"
GREEN = "#526A50"
GREEN_DARK = "#334B39"
GREEN_SOFT = "#E5EBDD"
CLAY = "#B9785F"
CLAY_SOFT = "#F0E2D8"
GOLD = "#D6A75F"
BLUE = "#668597"
DARK = "#101925"
DARK_PANEL = "#182535"
DARK_LINE = "#304052"
WHITE = "#F7F6F0"
MINT = "#81C7A6"
RED = "#CA7269"

SECTIONS = [
    (
        "Project overview",
        "Welcome. This project has two connected views of order data. First, a small online shop lets a customer choose products and confirm an order. Second, an ETL pipeline extracts order lines from CSV, validates and transforms them, then loads clean records into SQLite. The shop creates synthetic orders; ETL checks that they are safe to store. A generated batch also tests larger volumes and deliberate bad records. Together, these parts show both the customer journey and the data quality behind it. It is also a software testing exercise: normal paths, boundaries, and failures are checked before trusting the output. This is a local practice example, not a Fynd production integration, payment system, or official challenge solution.",
    ),
    (
        "A considered storefront",
        "The storefront offers six fixed-price products: a canvas tote, stoneware mug, cedar candle, field notebook, socks, and a botanical soap set. Product names and prices come from one shared catalog used by both the browser and Python service. Add an item and the bag count, quantity, line total, and subtotal update. Change the quantity or remove an item and the total recalculates in cents. The page has a clear empty-bag state, required name field, and helpful validation. It adapts to smaller screens and provides descriptive controls. The aim is a believable, easy-to-test shop, not a complete retail platform. Products are synthetic, prices are fixed, and the page does not collect payment details.",
    ),
    (
        "Checkout and server-side trust",
        "Checkout requires at least one product and a non-blank name. If something is missing, a message explains what to fix and preserves the cart and entered name. After submission, the page blocks repeat interaction so a rapid second click cannot create another confirmation. The browser sends product IDs, quantities, and the name to Python. The service checks each product against the shared catalog and calculates the price itself; browser-supplied prices are not trusted. It creates an order reference and synthetic guest ID, then makes one order-line record per product. Payment, accounts, delivery, and external services are deliberately out of scope.",
    ),
    (
        "The order-to-confirmation path",
        "The local service appends each new order line to a raw CSV with order ID, guest ID, customer name, SKU, quantity, unit price, order timestamp, and update timestamp. It runs the ETL pipeline, checks the SQLite table, then returns the saved order. The browser opens a separate confirmation page and retrieves the order using its reference. The page shows the customer, reference, placed time, products, quantities, line amounts, and total. The order has been extracted, validated, transformed, and loaded before confirmation appears. The service stores data locally and is a learning bridge, not a production order platform.",
    ),
    (
        "ETL: extract, transform, validate",
        "The standalone fixture contains twenty thousand and twenty synthetic rows. Its CSV contract has eight fields; column order may vary, but missing or unexpected fields fail before loading. Values are read as text, trimmed, and SKUs become uppercase. Quantities must be finite positive integers; prices must be finite and non-negative, so zero is valid. Timestamps with different offsets are normalized to UTC. Invalid rows go to a rejects CSV with one reason, such as a missing name or invalid quantity. Rejected data stays visible for investigation. The same rules process shop orders and the larger generated fixture.",
    ),
    (
        "Order identity and safe loading",
        "A SKU is not a unique order: different customers can buy the same product. The order-line key is the pair order ID plus SKU. If that same pair repeats, keep the latest update; for equal timestamps, keep the later source row. The same SKU in different orders remains separate. Browser tests verify that two mug orders both survive in SQLite. The table uses this composite primary key, and upserts only apply newer or equal updates. Existing databases with the older SKU-only key are migrated while preserving their rows. This models order lines, not product inventory.",
    ),
    (
        "Accounting and release quality",
        "Every input row is accounted for. Of twenty thousand and twenty generated rows, fifteen are rejected, five duplicate order lines are removed, and twenty thousand are loaded. Read equals rejected plus duplicates removed plus loaded. The release gate checks the SQLite schema, non-empty row count, required values, unique order-line keys, and quantity and price ranges. Quantities must stay positive and integral; prices must remain finite and non-negative. A failure exits non-zero. A clean fixture run loads twenty thousand rows and passes. Shop orders use a separate local folder, so they do not overwrite the standalone ETL example.",
    ),
    (
        "Tests as evidence",
        "Automation covers both layers. ETL tests check the source contract, normalization, rejects, timestamps, order-line keys, upserts, legacy migration, accounting, quality rules, and the CSV watcher. Chromium tests use a temporary store and a fresh cart. They verify saved confirmation details, missing-name and empty-cart validation, exact totals, removal, a rapid double-click, fixed server prices, and the same SKU across separate orders. The current suite has forty-seven passing tests: thirty-nine ETL and eight browser checks. These are automated results; manual smoke checks are documented but not claimed as run. All evidence describes this local build only.",
    ),
    (
        "Putting both scales together",
        "The complete flow is simple: browse, check out, save order lines, validate them through ETL, load SQLite, and retrieve the confirmation. A separate generated batch demonstrates larger-scale quality checks. Start the shop service and open its local address. Generate the sample CSV, run ETL and the report, or install Chromium and run pytest. The README gives the commands and the test plan explains the risks. There is no payment handling, login, production Fynd connection, or real customer data. This is an end-to-end learning project, not an ecommerce system ready for deployment. Thank you for watching.",
    ),
]

SECTION_TITLES = [
    "A shop, and the data behind it",
    "Six thoughtful products",
    "The cart stays honest",
    "An order becomes a saved record",
    "Extract, transform, validate",
    "A SKU is not an order",
    "Every row accounted for",
    "Tests verify what customers see",
    "One connected learning flow",
]

PRODUCTS = [
    ("Canvas Tote", "$24.50", "bag", "#DDE6D5"),
    ("Stoneware Mug", "$12.00", "mug", "#EFE0D4"),
    ("Cedar Candle", "$18.50", "candle", "#EFE7D2"),
    ("Field Notebook", "$9.50", "book", "#DCE7E8"),
    ("Everyday Socks", "$14.00", "socks", "#EEDFDB"),
    ("Botanical Soap", "$16.00", "soap", "#DDE9DF"),
]


@lru_cache(maxsize=None)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, box, fill: str, radius: int = 16, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, point, value: str, size: int = 18, color: str = INK, bold: bool = False):
    draw.text(point, value, font=font(size, bold), fill=color)


def centered(draw: ImageDraw.ImageDraw, x: int, y: int, value: str, size: int = 18, color: str = INK, bold: bool = False):
    selected = font(size, bold)
    box = draw.textbbox((0, 0), value, font=selected)
    draw.text((x - (box[2] - box[0]) / 2, y - (box[3] - box[1]) / 2), value, font=selected, fill=color)


def wrapped(draw: ImageDraw.ImageDraw, point, value: str, width: int, size: int = 16, color: str = MUTED, line_gap: int = 7):
    selected = font(size)
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=selected)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    x, y = point
    for line in lines:
        draw.text((x, y), line, font=selected, fill=color)
        y += size + line_gap
    return y


def arrow(draw: ImageDraw.ImageDraw, start, end, color: str = GREEN, width: int = 3):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    direction = 1 if x2 >= x1 else -1
    draw.polygon(((x2, y2), (x2 - 11 * direction, y2 - 7), (x2 - 11 * direction, y2 + 7)), fill=color)


def dot(draw: ImageDraw.ImageDraw, x: float, y: float, color: str, radius: int = 6):
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def product_icon(draw: ImageDraw.ImageDraw, kind: str, cx: int, cy: int, scale: float = 1.0, color: str = GREEN):
    s = scale
    stroke = max(2, round(3 * s))
    if kind == "bag":
        draw.arc((cx - 20 * s, cy - 25 * s, cx + 20 * s, cy + 18 * s), 180, 360, fill=color, width=stroke)
        draw.rounded_rectangle((cx - 28 * s, cy - 8 * s, cx + 28 * s, cy + 36 * s), radius=int(7 * s), fill=color, outline=GREEN_DARK, width=stroke)
        draw.line((cx - 14 * s, cy + 3 * s, cx + 14 * s, cy + 3 * s), fill="#F6F4ED", width=max(1, stroke - 1))
    elif kind == "mug":
        draw.rounded_rectangle((cx - 25 * s, cy - 22 * s, cx + 18 * s, cy + 30 * s), radius=8 * s, fill=color, outline=GREEN_DARK, width=stroke)
        draw.arc((cx + 11 * s, cy - 10 * s, cx + 42 * s, cy + 18 * s), 270, 90, fill=GREEN_DARK, width=stroke)
        draw.line((cx - 15 * s, cy - 8 * s, cx + 8 * s, cy - 8 * s), fill="#F6F4ED", width=stroke)
    elif kind == "candle":
        draw.rounded_rectangle((cx - 22 * s, cy - 7 * s, cx + 22 * s, cy + 33 * s), radius=6 * s, fill=color, outline=GREEN_DARK, width=stroke)
        draw.line((cx, cy - 7 * s, cx, cy - 19 * s), fill=GREEN_DARK, width=stroke)
        draw.ellipse((cx - 7 * s, cy - 35 * s, cx + 7 * s, cy - 17 * s), fill=GOLD)
    elif kind == "book":
        draw.rounded_rectangle((cx - 27 * s, cy - 32 * s, cx + 24 * s, cy + 33 * s), radius=4 * s, fill=color, outline=GREEN_DARK, width=stroke)
        draw.line((cx - 16 * s, cy - 27 * s, cx - 16 * s, cy + 29 * s), fill="#F6F4ED", width=stroke)
        for row in range(3):
            draw.line((cx - 8 * s, cy - 8 * s + row * 10 * s, cx + 14 * s, cy - 8 * s + row * 10 * s), fill=GREEN_DARK, width=max(1, stroke - 1))
    elif kind == "socks":
        draw.line((cx - 15 * s, cy - 26 * s, cx - 15 * s, cy + 8 * s), fill=color, width=15 * stroke)
        draw.line((cx - 15 * s, cy + 8 * s, cx - 32 * s, cy + 20 * s), fill=color, width=15 * stroke)
        draw.line((cx + 16 * s, cy - 26 * s, cx + 16 * s, cy + 8 * s), fill=BLUE, width=15 * stroke)
        draw.line((cx + 16 * s, cy + 8 * s, cx + 31 * s, cy + 20 * s), fill=BLUE, width=15 * stroke)
    else:
        for offset in (-15, 15):
            draw.rounded_rectangle((cx + offset * s - 14 * s, cy - 22 * s, cx + offset * s + 14 * s, cy + 23 * s), radius=12 * s, fill=color, outline=GREEN_DARK, width=stroke)
        draw.line((cx - 4 * s, cy - 4 * s, cx + 4 * s, cy - 4 * s), fill="#F6F4ED", width=stroke)


def draw_pointer(draw: ImageDraw.ImageDraw, x: float, y: float, scale: float = 1.0):
    points = [(x, y), (x, y + 23 * scale), (x + 6 * scale, y + 17 * scale), (x + 11 * scale, y + 29 * scale), (x + 16 * scale, y + 27 * scale), (x + 11 * scale, y + 15 * scale), (x + 20 * scale, y + 15 * scale)]
    draw.polygon(points, fill=WHITE, outline=INK)


def draw_backdrop(index: int, timestamp: float) -> Image.Image:
    light = index in {0, 1, 2, 3, 8}
    base = PAPER if light else DARK
    image = Image.new("RGB", (W, H), base)
    draw = ImageDraw.Draw(image)
    drift = math.sin(timestamp * 0.12) * 18
    if light:
        draw.ellipse((900 + drift, -380, 1510 + drift, 235), fill="#E8ECDD")
        draw.ellipse((-380 - drift, 540, 250 - drift, 1160), fill="#F0E5D8")
        for x in range(30, W, 72):
            draw.line((x, 0, x, H), fill="#EFEEE7", width=1)
    else:
        draw.ellipse((875 + drift, -420, 1510 + drift, 225), fill="#162435")
        draw.ellipse((-380 - drift, 490, 260 - drift, 1100), fill="#142131")
        for x in range(30, W, 48):
            draw.line((x, 0, x, H), fill="#162333", width=1)
        for y in range(24, H, 48):
            draw.line((0, y, W, y), fill="#162333", width=1)
    return image


def draw_brand(draw: ImageDraw.ImageDraw, index: int, timestamp: float, total: float):
    light = index in {0, 1, 2, 3, 8}
    ink = INK if light else WHITE
    secondary = MUTED if light else "#A9B6C2"
    draw.ellipse((44, 27, 76, 59), fill=GREEN)
    centered(draw, 60, 43, "f", 21, WHITE, True)
    text(draw, (86, 29), "fieldnotes supply", 16, ink, True)
    text(draw, (86, 49), "ORDER DATA, END TO END", 8, secondary, True)
    rounded(draw, (1034, 29, 1227, 59), "#E9EEE4" if light else DARK_PANEL, 14)
    centered(draw, 1130, 44, "LOCAL PRACTICE DEMO", 9, GREEN if light else MINT, True)
    draw.line((44, 79, 1236, 79), fill=LINE if light else DARK_LINE, width=1)
    draw.line((44, 694, 1236, 694), fill=LINE if light else DARK_LINE, width=1)
    draw.line((44, 694, 44 + int(1192 * min(1.0, timestamp / max(total, 1))), 694), fill=GREEN, width=3)
    elapsed = f"{int(timestamp // 60):02d}:{int(timestamp % 60):02d}"
    remaining = f"{int(total // 60):02d}:{int(total % 60):02d}"
    text(draw, (47, 703), SECTION_TITLES[index].upper(), 9, secondary, True)
    text(draw, (1160, 703), f"{elapsed} / {remaining}", 9, secondary, True)


def draw_overview(draw: ImageDraw.ImageDraw, progress: float, time: float):
    text(draw, (57, 110), "A shop, and the", 47, INK, False)
    text(draw, (57, 162), "data behind it.", 47, GREEN_DARK, True)
    wrapped(draw, (61, 226), "One customer journey, one trustworthy order record, and one testable data pipeline.", 455, 17, MUTED, 8)

    rounded(draw, (55, 334, 558, 625), PANEL, 18, LINE, 1)
    rounded(draw, (55, 334, 558, 375), "#E8EDE2", 18)
    draw.rectangle((55, 354, 558, 375), fill="#E8EDE2")
    text(draw, (78, 348), "fieldnotes supply", 14, GREEN_DARK, True)
    text(draw, (482, 350), "BAG  2", 10, GREEN_DARK, True)
    for i, (name, price, kind, color) in enumerate(PRODUCTS[:3]):
        x = 78 + i * 151
        rounded(draw, (x, 396, x + 131, 571), color, 9)
        product_icon(draw, kind, x + 65, 452, 0.72)
        text(draw, (x + 8, 503), name, 10, INK, True)
        text(draw, (x + 8, 521), price, 10, GREEN_DARK, True)
        rounded(draw, (x + 8, 541, x + 122, 559), GREEN, 6)
        centered(draw, x + 65, 550, "ADD TO BAG", 7, WHITE, True)

    rounded(draw, (688, 179, 1218, 618), DARK, 22)
    text(draw, (722, 211), "THE SAME ORDER, AS DATA", 12, MINT, True)
    nodes = [
        ("SHOP", "customer"),
        ("CSV", "order lines"),
        ("ETL", "validate"),
        ("SQLITE", "save"),
    ]
    xs = [754, 887, 1019, 1149]
    for i, (name, detail) in enumerate(nodes):
        x = xs[i]
        pulse = math.sin(progress * 9 - i * 1.2) * 3
        draw.ellipse((x - 30 - pulse, 343 - pulse, x + 30 + pulse, 403 + pulse), fill="#284338" if i <= int(progress * 4) else DARK_PANEL, outline=GREEN if i <= int(progress * 4) else DARK_LINE, width=2)
        centered(draw, x, 372, name, 11, WHITE, True)
        centered(draw, x, 425, detail, 9, "#A9B6C2")
        if i < len(nodes) - 1:
            arrow(draw, (x + 38, 373), (xs[i + 1] - 39, 373), MINT, 2)
    rounded(draw, (723, 490, 1183, 563), "#E5EBDD", 13)
    centered(draw, 953, 514, "CUSTOMER VIEW + DATA QUALITY", 12, GREEN_DARK, True)
    centered(draw, 953, 541, "Connected locally. Kept deliberately synthetic.", 10, MUTED)

    phase = (progress * 5) % 1
    x = 792 + phase * 320
    dot(draw, x, 373, GOLD, 5)


def draw_storefront(draw: ImageDraw.ImageDraw, progress: float, time: float):
    text(draw, (56, 103), "Little things for", 37, INK)
    text(draw, (56, 144), "the everyday.", 37, GREEN_DARK, True)
    text(draw, (898, 130), "6 PRODUCTS  /  FIXED PRICES", 10, MUTED, True)
    rounded(draw, (54, 194, 1226, 637), PANEL, 16, LINE)
    rounded(draw, (54, 194, 1226, 237), "#E8EDE2", 16)
    draw.rectangle((54, 218, 1226, 237), fill="#E8EDE2")
    text(draw, (79, 209), "FIELDNOTES SUPPLY", 11, GREEN_DARK, True)
    text(draw, (1004, 210), "YOUR BAG", 9, MUTED, True)
    count = min(3, max(0, int(progress * 5)))
    rounded(draw, (1112, 203, 1184, 228), GREEN, 12)
    centered(draw, 1148, 215, f"{count} ITEMS", 8, WHITE, True)

    selected = min(5, int(progress * 6))
    for i, (name, price, kind, color) in enumerate(PRODUCTS):
        col, row = i % 3, i // 3
        x, y = 78 + col * 371, 256 + row * 179
        active = i == selected
        bg = "#F4F2EA"
        rounded(draw, (x, y, x + 344, y + 163), bg, 10, GREEN if active else LINE, 2 if active else 1)
        rounded(draw, (x + 10, y + 10, x + 108, y + 103), color, 8)
        bob = math.sin(time * 2.4 + i) * 3
        product_icon(draw, kind, x + 59, int(y + 55 + bob), 0.72)
        text(draw, (x + 123, y + 17), f"0{i + 1}  /  FIELDNOTES", 7, MUTED, True)
        text(draw, (x + 123, y + 40), name, 13, INK, True)
        text(draw, (x + 123, y + 63), price, 12, GREEN_DARK, True)
        text(draw, (x + 123, y + 83), "Thoughtfully made.", 9, MUTED)
        rounded(draw, (x + 10, y + 119, x + 334, y + 151), GREEN if active else "#F9F8F3", 5, GREEN if active else LINE)
        centered(draw, x + 172, y + 135, "ADDED TO BAG  +" if active and progress > i / 6 else "ADD TO BAG  +", 9, WHITE if active else GREEN_DARK, True)
    cursor_x = 78 + (selected % 3) * 371 + 265
    cursor_y = 256 + (selected // 3) * 179 + 135
    draw_pointer(draw, cursor_x + math.sin(time * 1.8) * 10, cursor_y - 28 + math.cos(time * 1.8) * 7, 0.72)

    rounded(draw, (54, 651, 1226, 676), "#E6EBE0", 10)
    centered(draw, 640, 663, "Add  /  change quantity  /  remove  /  see the exact subtotal", 10, GREEN_DARK, True)


def draw_cart(draw: ImageDraw.ImageDraw, progress: float, time: float):
    text(draw, (57, 111), "Checkout, made clear.", 39, INK, True)
    wrapped(draw, (61, 164), "A good checkout protects the customer's choices and the order total.", 520, 16, MUTED)
    rounded(draw, (60, 254, 719, 627), "#E9ECDD", 20)
    text(draw, (95, 284), "YOUR BAG", 10, GREEN, True)
    text(draw, (95, 314), "A few good things.", 25, INK, True)
    items = [
        ("Canvas Tote", "1 x $24.50", "$24.50", "bag"),
        ("Stoneware Mug", "2 x $12.00", "$24.00", "mug"),
        ("Cedar Candle", "1 x $18.50", "$18.50", "candle"),
    ]
    for i, (name, detail, amount, kind) in enumerate(items):
        y = 369 + i * 68
        color = GREEN if progress > (i + 1) / 5 else LINE
        draw.ellipse((95, y, 143, y + 48), fill="#F8F7F1")
        product_icon(draw, kind, 119, y + 23, 0.42)
        text(draw, (162, y + 4), name, 13, INK, True)
        text(draw, (162, y + 27), detail, 10, MUTED)
        text(draw, (573, y + 14), amount, 13, INK, True)
        draw.line((95, y + 56, 680, y + 56), fill=color, width=1)
    text(draw, (95, 594), "SUBTOTAL", 10, MUTED, True)
    text(draw, (581, 583), "$67.00", 23, GREEN_DARK, True)

    rounded(draw, (779, 193, 1222, 604), PANEL, 18, LINE)
    text(draw, (814, 224), "MADE OUT TO", 9, MUTED, True)
    rounded(draw, (812, 251, 1188, 296), "#FBFAF6", 6, LINE)
    text(draw, (829, 265), "Alex Morgan", 13, INK)
    if progress < 0.23:
        rounded(draw, (812, 305, 1188, 345), "#FFF0ED", 6, "#EDCFC6")
        text(draw, (826, 317), "Add your name to continue", 10, RED, True)
    text(draw, (814, 374), "ORDER TOTAL", 9, MUTED, True)
    text(draw, (1070, 360), "$67.00", 25, INK, True)
    rounded(draw, (812, 425, 1188, 478), GREEN, 8)
    centered(draw, 1000, 452, "PLACE YOUR ORDER", 11, WHITE, True)
    text(draw, (814, 495), "One submission. One order reference.", 10, MUTED)
    if progress > 0.45:
        rounded(draw, (837, 521, 1172, 570), GREEN_SOFT, 7, "#C9D8C6")
        centered(draw, 1004, 545, "SAVING ORDER  ->  CONFIRMATION", 9, GREEN_DARK, True)
    draw_pointer(draw, 1065 + math.sin(time * 2) * 4, 431, 0.8)


def draw_order_flow(draw: ImageDraw.ImageDraw, progress: float, time: float):
    text(draw, (57, 111), "From click to confirmation.", 38, INK, True)
    text(draw, (61, 159), "The customer sees the order only after it has passed through ETL.", 14, MUTED)
    steps = [
        ("BROWSER", "product IDs", "and quantities"),
        ("PYTHON", "catalog price", "and validation"),
        ("RAW CSV", "one row per", "order line"),
        ("ETL", "clean, check", "and load"),
        ("SQLITE", "saved facts", "by order/SKU"),
        ("CONFIRM", "read saved", "order details"),
    ]
    x_starts = [52, 256, 460, 664, 868, 1072]
    cy = 355
    for i, (title, line1, line2) in enumerate(steps):
        x = x_starts[i]
        active = progress > i / 6
        draw.ellipse((x + 31, cy - 43, x + 107, cy + 33), fill=GREEN_SOFT if active else PANEL, outline=GREEN if active else LINE, width=3)
        if i == 0:
            rounded(draw, (x + 49, cy - 27, x + 90, cy + 18), GREEN if active else MUTED, 4)
            draw.line((x + 56, cy - 16, x + 83, cy - 16), fill=PANEL, width=2)
            draw.line((x + 56, cy - 7, x + 83, cy - 7), fill=PANEL, width=2)
        elif i == 1:
            centered(draw, x + 69, cy - 4, "PY", 17, GREEN_DARK if active else MUTED, True)
        elif i == 2:
            draw.polygon(((x + 50, cy - 24), (x + 84, cy - 24), (x + 93, cy - 14), (x + 93, cy + 20), (x + 50, cy + 20)), fill=PANEL, outline=GREEN if active else MUTED)
            for row in range(3):
                draw.line((x + 57, cy - 10 + row * 9, x + 84, cy - 10 + row * 9), fill=GREEN if active else MUTED, width=2)
        elif i == 3:
            centered(draw, x + 69, cy - 4, "ETL", 13, GREEN_DARK if active else MUTED, True)
        elif i == 4:
            draw.ellipse((x + 50, cy - 24, x + 94, cy - 8), fill=GREEN if active else MUTED)
            draw.rectangle((x + 50, cy - 16, x + 94, cy + 16), fill=GREEN if active else MUTED)
            draw.arc((x + 50, cy + 8, x + 94, cy + 25), 0, 180, fill=GREEN_DARK, width=2)
        else:
            centered(draw, x + 69, cy - 3, "OK", 15, GREEN_DARK if active else MUTED, True)
        centered(draw, x + 69, cy + 67, title, 10, GREEN_DARK if active else MUTED, True)
        centered(draw, x + 69, cy + 91, line1, 9, MUTED)
        centered(draw, x + 69, cy + 106, line2, 9, MUTED)
        if i < len(steps) - 1:
            arrow(draw, (x + 111, cy - 4), (x_starts[i + 1] + 25, cy - 4), GREEN if active else "#B9BDB2", 2)
    path = (progress * 6) % 1
    x = 161 + path * 856
    dot(draw, x, cy - 4 + math.sin(time * 3) * 2, CLAY, 7)
    rounded(draw, (150, 560, 1130, 624), "#EBEEE5", 12)
    centered(draw, 640, 581, "Local API  ->  store_orders.csv  ->  ETL  ->  store_orders.sqlite", 13, GREEN_DARK, True)
    centered(draw, 640, 604, "Confirmation details are retrieved from the saved order, not browser-only state.", 10, MUTED)


def draw_transform(draw: ImageDraw.ImageDraw, progress: float, time: float):
    text(draw, (57, 110), "Clean the record.", 41, WHITE, True)
    text(draw, (59, 162), "Keep the evidence.", 41, MINT)
    text(draw, (60, 220), "Eight fields enter. Every value gets a clear decision.", 14, "#A9B6C2")

    rounded(draw, (52, 280, 492, 626), DARK_PANEL, 16, DARK_LINE)
    text(draw, (78, 301), "SOURCE CSV", 10, MINT, True)
    headers = ["order_id", "customer_id", "customer_name", "sku", "quantity", "unit_price", "order_timestamp", "updated_at"]
    row_a = ["ORD-42", "GUEST-81", "Alex Morgan", " tote-01 ", "2", "24.50", "10:30-04:00", "10:32-04:00"]
    row_b = ["ORD-43", "GUEST-98", "", "MUG-02", "-1", "12.00", "not-a-time", "10:35Z"]
    for i, (head, value_a, value_b) in enumerate(zip(headers, row_a, row_b)):
        y = 331 + i * 33
        text(draw, (78, y), head, 9, "#9BAAB6", True)
        text(draw, (245, y), value_a, 9, WHITE)
        if progress > 0.48:
            text(draw, (375, y), value_b, 9, RED if i in {1, 3, 5} else "#BAC2C8")
    text(draw, (78, 602), "RAW VALUES FIRST", 8, "#82919F", True)

    rounded(draw, (531, 310, 839, 561), "#E8EDE2", 18)
    centered(draw, 685, 342, "VALIDATE + TRANSFORM", 13, GREEN_DARK, True)
    validations = ["trim text / uppercase SKU", "positive whole quantity", "finite, non-negative price", "parse timestamps as UTC", "record one reject reason"]
    for i, value in enumerate(validations):
        y = 380 + i * 31
        active = progress > (i + 1) / 7
        dot(draw, 567, y + 6, GREEN if active else "#B9C1B5", 5)
        text(draw, (583, y), value, 10, GREEN_DARK if active else MUTED, active)

    arrow(draw, (846, 431), (902, 431), MINT, 3)
    rounded(draw, (921, 291, 1228, 418), "#183C32", 15, "#3D8B68", 2)
    text(draw, (945, 313), "ACCEPTED", 9, MINT, True)
    text(draw, (945, 350), "TOTE-01  /  quantity 2", 11, WHITE, True)
    text(draw, (945, 380), "timestamp normalized to UTC", 9, "#B8D3C4")
    rounded(draw, (921, 440, 1228, 567), "#3B282B", 15, "#805051", 2)
    text(draw, (945, 461), "REJECTED", 9, "#F2A7A0", True)
    text(draw, (945, 495), "ORD-43  /  quantity -1", 11, WHITE, True)
    text(draw, (945, 526), "reason: invalid_quantity", 9, "#E4B8B4")
    rounded(draw, (52, 644, 1228, 676), "#1C2A36", 8)
    centered(draw, 640, 660, "Rejects stay visible in a separate CSV for follow-up.", 10, "#CFD6D8")


def draw_identity(draw: ImageDraw.ImageDraw, progress: float, time: float):
    text(draw, (57, 109), "A product is not an order.", 39, WHITE, True)
    text(draw, (60, 159), "Order identity comes from the pair:  order_id  +  sku", 15, MINT)
    left = (75, 235, 595, 475)
    right = (683, 235, 1205, 475)
    rounded(draw, left, DARK_PANEL, 18, DARK_LINE)
    rounded(draw, right, DARK_PANEL, 18, DARK_LINE)
    text(draw, (106, 259), "SAME SKU, DIFFERENT ORDERS", 10, "#AAB7C2", True)
    text(draw, (714, 259), "SAME ORDER + SKU, NEWER UPDATE", 10, "#AAB7C2", True)

    records = [
        (305, "ORD-1001", "MUG-02", "Customer A", MINT),
        (393, "ORD-1002", "MUG-02", "Customer B", GOLD),
    ]
    for y, order, sku, customer, color in records:
        rounded(draw, (105, y, 564, y + 61), "#1E3041", 9, color if progress > 0.35 else DARK_LINE, 2)
        text(draw, (125, y + 11), order, 11, WHITE, True)
        text(draw, (280, y + 11), sku, 11, MINT, True)
        text(draw, (397, y + 12), customer, 9, "#B7C0C5")
        if progress > 0.53:
            centered(draw, 530, y + 42, "KEEP BOTH", 7, color, True)

    rounded(draw, (715, 307, 1166, 373), "#3B2E2B", 9, "#9C6955", 2)
    text(draw, (737, 323), "ORD-2040    TOTE-01", 11, WHITE)
    text(draw, (1005, 323), "09:00", 10, "#E2B29A")
    rounded(draw, (715, 395, 1166, 461), "#1E3C34", 9, MINT if progress > 0.65 else DARK_LINE, 2)
    text(draw, (737, 410), "ORD-2040    TOTE-01", 11, WHITE, True)
    text(draw, (1005, 410), "10:15", 10, MINT, True)
    if progress > 0.68:
        rounded(draw, (1072, 426, 1148, 449), "#2D5143", 8)
        centered(draw, 1110, 438, "LATEST", 7, MINT, True)
    arrow(draw, (836, 382), (836, 390), GOLD, 2)

    rounded(draw, (121, 522, 1158, 623), "#E8EDE2", 14)
    text(draw, (153, 543), "SQLITE COMPOSITE PRIMARY KEY", 9, GREEN_DARK, True)
    text(draw, (153, 572), "PRIMARY KEY  (order_id, sku)", 20, INK, True)
    text(draw, (704, 548), "Same key? Latest update wins.", 11, GREEN_DARK, True)
    text(draw, (704, 575), "Different order? Preserve both.", 11, GREEN_DARK)
    pulse_x = 153 + (progress * 850) % 850
    draw.ellipse((pulse_x, 609, pulse_x + 7, 616), fill=CLAY)


def draw_quality(draw: ImageDraw.ImageDraw, progress: float, time: float):
    text(draw, (57, 107), "No row disappears.", 38, INK, True)
    text(draw, (60, 155), "The accounting invariant makes the batch auditable.", 14, MUTED)
    equation = [("READ", 20020, BLUE), ("REJECTED", 15, RED), ("DUPLICATES", 5, GOLD), ("LOADED", 20000, GREEN)]
    x_positions = [54, 355, 656, 957]
    for i, ((title, value, color), x) in enumerate(zip(equation, x_positions)):
        count = round(value * min(1, max(0, progress * 1.6 - i * 0.09)))
        rounded(draw, (x, 228, x + 265, 348), PANEL, 16, color, 2)
        centered(draw, x + 132, 259, title, 10, color, True)
        centered(draw, x + 132, 306, f"{count:,}", 28, INK, True)
        if i < 3:
            centered(draw, x + 284, 289, "=" if i == 0 else "+", 25, MUTED, True)
    rounded(draw, (204, 379, 1076, 449), "#E8EDE2", 13)
    centered(draw, 640, 414, "20,020  =  15  +  5  +  20,000", 23, GREEN_DARK, True)

    text(draw, (59, 491), "RELEASE GATE", 9, GREEN_DARK, True)
    checks = [
        ("Schema", "required columns"),
        ("Rows", "non-empty target"),
        ("Values", "no blanks"),
        ("Keys", "unique order / SKU"),
        ("Ranges", "quantity + price"),
    ]
    for i, (name, detail) in enumerate(checks):
        x = 58 + i * 238
        passed = progress > 0.38 + i * 0.095
        rounded(draw, (x, 520, x + 212, 605), GREEN_SOFT if passed else "#F0EEE6", 11, "#C9D8C6" if passed else LINE, 1)
        dot(draw, x + 23, 545, GREEN if passed else "#B9BDB2", 6)
        text(draw, (x + 38, 536), name, 11, GREEN_DARK if passed else MUTED, True)
        text(draw, (x + 17, 570), detail, 9, MUTED)
        if passed:
            centered(draw, x + 184, 544, "PASS", 7, GREEN, True)
    rounded(draw, (333, 622, 947, 660), DARK, 10)
    centered(draw, 640, 641, "FAILURES EXIT NON-ZERO  /  QUALITY GATE PASS", 10, MINT, True)


def draw_tests(draw: ImageDraw.ImageDraw, progress: float, time: float):
    text(draw, (57, 109), "Evidence, not guesswork.", 39, WHITE, True)
    text(draw, (60, 158), "The checks follow customer-visible outcomes and data contracts.", 14, "#A9B6C2")
    rounded(draw, (60, 224, 615, 619), DARK_PANEL, 18, DARK_LINE, 1)
    text(draw, (92, 250), "PYTEST  /  CHROMIUM", 10, MINT, True)
    checks = [
        "ETL source contract + validation",
        "Composite key + migration",
        "Store order saved to SQLite",
        "Missing name + empty bag",
        "Exact total + item removal",
        "Fixed price + rapid repeat",
        "Same SKU, separate orders",
    ]
    for i, item in enumerate(checks):
        y = 291 + i * 38
        current = min(len(checks) - 1, int(progress * len(checks)))
        color = MINT if i <= current else "#7B8996"
        if i <= current:
            draw.ellipse((94, y + 3, 108, y + 17), fill=color)
            draw.line((98, y + 9, 101, y + 12), fill=DARK, width=2)
            draw.line((101, y + 12, 105, y + 6), fill=DARK, width=2)
        else:
            draw.ellipse((94, y + 3, 108, y + 17), outline="#596979", width=1)
        text(draw, (121, y), item, 11, WHITE if i <= current else "#8996A1")

    rounded(draw, (650, 224, 1224, 619), "#F1EFE7", 18)
    text(draw, (685, 250), "CURRENT RUN", 9, GREEN, True)
    text(draw, (685, 283), "47", 60, INK, True)
    text(draw, (778, 316), "tests passed", 15, GREEN_DARK, True)
    draw.line((686, 364, 1188, 364), fill=LINE, width=2)
    text(draw, (687, 390), "39", 28, GREEN_DARK, True)
    text(draw, (735, 402), "ETL checks", 10, MUTED)
    text(draw, (948, 390), "8", 28, GREEN_DARK, True)
    text(draw, (984, 402), "browser journeys", 10, MUTED)
    rounded(draw, (686, 454, 1188, 509), "#E5EBDD", 9)
    centered(draw, 937, 481, "TEMPORARY TEST DATA  /  CLEAN BROWSER CONTEXTS", 9, GREEN_DARK, True)
    wrapped(draw, (687, 535), "Automated outcomes are reported. Manual smoke checks stay clearly labelled as not run.", 470, 10, MUTED, 5)


def draw_wrap(draw: ImageDraw.ImageDraw, progress: float, time: float):
    text(draw, (60, 110), "One connected", 46, INK)
    text(draw, (60, 162), "learning flow.", 46, GREEN_DARK, True)
    wrapped(draw, (63, 232), "A thoughtful storefront creates an order. A careful ETL pipeline makes that order trustworthy and easy to verify.", 525, 18, MUTED, 9)

    flow = [
        ("SHOP", "six products"),
        ("CHECKOUT", "fixed prices"),
        ("CSV", "order lines"),
        ("ETL", "quality checks"),
        ("SQLITE", "saved order"),
        ("DETAILS", "confirmation"),
    ]
    xs = [91, 307, 523, 739, 955, 1171]
    for i, (title, detail) in enumerate(flow):
        x = xs[i]
        active = progress > i / 6
        draw.ellipse((x - 37, 413 - 37, x + 37, 413 + 37), fill=GREEN if active else "#E8E7DE", outline=GREEN if active else "#C8C9BF", width=2)
        centered(draw, x, 413, title, 9, WHITE if active else MUTED, True)
        centered(draw, x, 468, detail, 8, MUTED)
        if i < len(flow) - 1:
            arrow(draw, (x + 43, 413), (xs[i + 1] - 46, 413), GREEN if active else "#B9BDB2", 2)
    particle_x = 91 + (progress * 5 % 1) * 1080
    dot(draw, particle_x, 413, CLAY, 6)

    rounded(draw, (610, 535, 1219, 627), "#E8EDE2", 14)
    text(draw, (639, 553), "LOCAL PRACTICE PROJECT", 9, GREEN_DARK, True)
    text(draw, (639, 578), "Synthetic records. No payments. No Fynd production link.", 10, INK)
    text(draw, (639, 602), "Reproduce it with the README and test plan.", 9, MUTED)
    text(draw, (61, 551), "PROJECT GOAL", 9, CLAY, True)
    wrapped(draw, (61, 575), "Clear customer feedback; traceable data quality.", 470, 13, INK, 5)


DRAWERS = [
    draw_overview,
    draw_storefront,
    draw_cart,
    draw_order_flow,
    draw_transform,
    draw_identity,
    draw_quality,
    draw_tests,
    draw_wrap,
]


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    import re

    match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not read media duration for {path}: {result.stderr}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


async def synthesize_narration(directory: Path) -> tuple[Path, list[float]]:
    pieces: list[Path] = []
    durations: list[float] = []
    for index, (title, narration) in enumerate(SECTIONS):
        piece = directory / f"narration-{index:02d}.mp3"
        print(f"Synthesizing narration {index + 1}/{len(SECTIONS)}: {title}", flush=True)
        for attempt in range(3):
            try:
                await edge_tts.Communicate(narration, VOICE, rate=VOICE_RATE).save(str(piece))
                break
            except NoAudioReceived as error:
                if attempt == 2:
                    raise RuntimeError(f"No narration audio received for scene {title!r}") from error
                await asyncio.sleep(2 ** attempt)
        pieces.append(piece)
        durations.append(probe_duration(piece))
        await asyncio.sleep(0.5)

    joined = directory / "narration.mp3"
    inputs = []
    for piece in pieces:
        inputs.extend(["-i", str(piece)])
    streams = "".join(f"[{index}:a:0]" for index in range(len(pieces)))
    filter_graph = f"{streams}concat=n={len(pieces)}:v=0:a=1[out]"
    subprocess.run(
        [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            filter_graph,
            "-map",
            "[out]",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(joined),
        ],
        check=True,
    )
    return joined, durations


def render_video(silent_video: Path, duration: float, starts: list[float]) -> None:
    command = [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{W}x{H}",
        "-framerate",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-r",
        str(OUTPUT_FPS),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "19",
        "-pix_fmt",
        "yuv420p",
        str(silent_video),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    section_starts = [0.0, *starts]
    section_ends = [*starts, duration]
    frame_count = round(duration * FPS)
    previous_frame: Image.Image | None = None
    try:
        for frame_number in range(frame_count):
            timestamp = frame_number / FPS
            index = bisect.bisect_right(section_starts, timestamp) - 1
            index = min(index, len(DRAWERS) - 1)
            section_duration = max(0.1, section_ends[index] - section_starts[index])
            progress = min(1.0, max(0.0, (timestamp - section_starts[index]) / section_duration))
            frame = draw_backdrop(index, timestamp)
            draw = ImageDraw.Draw(frame)
            DRAWERS[index](draw, progress, timestamp)
            draw_brand(draw, index, timestamp, duration)
            if previous_frame is not None and timestamp - section_starts[index] < 0.8:
                alpha = min(1.0, (timestamp - section_starts[index]) / 0.8)
                frame = Image.blend(previous_frame, frame, alpha)
            process.stdin.write(frame.tobytes())
            previous_frame = frame
        process.stdin.close()
        error = process.stderr.read()
        return_code = process.wait()
    except Exception:
        process.kill()
        process.wait()
        raise
    if return_code:
        raise RuntimeError(f"FFmpeg could not render the animation: {error.decode(errors='replace')}")


def main() -> None:
    if len(SECTIONS) != len(DRAWERS) or len(SECTIONS) != len(SECTION_TITLES):
        raise RuntimeError("Each narration section must have a matching visual scene.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fieldnotes-walkthrough-") as temp_name:
        temp_directory = Path(temp_name)
        narration, section_durations = asyncio.run(synthesize_narration(temp_directory))
        duration = probe_duration(narration)
        if not 420 <= duration <= 480:
            total_words = sum(len(script.split()) for _, script in SECTIONS)
            raise RuntimeError(
                f"Narration is {duration / 60:.2f} minutes, outside the 7-8 minute target "
                f"({total_words} words at {VOICE_RATE}). Adjust the script or TTS rate."
            )
        starts = []
        cursor = 0.0
        for segment_duration in section_durations[:-1]:
            cursor += segment_duration
            starts.append(cursor)

        silent_video = temp_directory / "animated-silent.mp4"
        rendered_video = temp_directory / "overview-final.mp4"
        render_video(silent_video, duration, starts)
        subprocess.run(
            [
                FFMPEG,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(silent_video),
                "-i",
                str(narration),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-t",
                f"{duration:.3f}",
                "-movflags",
                "+faststart",
                str(rendered_video),
            ],
            check=True,
        )
        rendered_video.replace(OUTPUT)

    words = sum(len(script.split()) for _, script in SECTIONS)
    print(f"Created: {OUTPUT}")
    print(f"Duration: {duration / 60:.2f} minutes ({duration:.1f} seconds)")
    print(f"Narration: {VOICE} male Indian-English neural voice; {words} words.")
    print("Visuals: nine animated scenes following the storefront, order API, ETL, SQLite, and tests.")


if __name__ == "__main__":
    main()
