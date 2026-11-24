from __future__ import annotations

import bisect
import re
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE = DOCS / "project-walkthrough-indian.mp4"
OUTPUT = DOCS / "Project Overview Video.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

W, H = 1280, 720
FPS = 12
VIDEO_FPS = 24
BG = "#080D1C"
GRID = "#10192C"
PANEL = "#121D33"
PANEL_LIGHT = "#192943"
WHITE = "#F5F8FF"
MUTED = "#9EACC5"
CYAN = "#54D7FF"
GREEN = "#58E2B2"
AMBER = "#FFC66D"
RED = "#FF758F"

SECTIONS = [
    ("Goal and scope", "PROJECT OVERVIEW", "A synthetic-data practice project"),
    ("CSV input and schema contract", "SOURCE CONTRACT", "Seven fields. One clear contract."),
    ("Transform: validate and clean", "DATA TRANSFORM", "Clean valid rows. Explain rejected rows."),
    ("Duplicate-SKU resolution", "DEDUPLICATION", "Keep the latest update, deterministically."),
    ("SQLite load and upsert", "TARGET LOAD", "Upsert safely by SKU."),
    ("Every row must be accounted for", "AUDIT INVARIANT", "No source row disappears."),
    ("Release gate", "DATA QUALITY", "Check the target before release."),
    ("Automated test coverage", "TEST STRATEGY", "Exercise normal, boundary, and failure paths."),
    ("Commands and expected evidence", "RUN EVIDENCE", "Reconcile the run from input to target."),
    ("Limitations and submission", "CLOSE", "Be precise about scope and evidence."),
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


FONTS = {
    (size, bold): font(size, bold)
    for size in (12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 40)
    for bold in (False, True)
}


def rounded(draw: ImageDraw.ImageDraw, box, fill: str, radius: int = 18, outline=None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def label(draw: ImageDraw.ImageDraw, point, value: str, size: int = 19, color: str = WHITE, bold: bool = False):
    selected = FONTS.get((size, bold), font(size, bold))
    draw.text(point, value, font=selected, fill=color)


def centered(draw: ImageDraw.ImageDraw, x: int, y: int, value: str, size: int = 19, color: str = WHITE, bold: bool = False):
    selected = FONTS.get((size, bold), font(size, bold))
    box = draw.textbbox((0, 0), value, font=selected)
    draw.text((x - (box[2] - box[0]) / 2, y - (box[3] - box[1]) / 2), value, font=selected, fill=color)


def arrow(draw: ImageDraw.ImageDraw, start, end, color: str = MUTED, width: int = 3):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    draw.polygon(((x2, y2), (x2 - 11, y2 - 7), (x2 - 11, y2 + 7)), fill=color)


def dot(draw: ImageDraw.ImageDraw, x: float, y: float, color: str, radius: int = 7):
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)


def make_background() -> Image.Image:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    for x in range(30, W, 48):
        draw.line((x, 0, x, H), fill=GRID, width=1)
    for y in range(25, H, 48):
        draw.line((0, y, W, y), fill=GRID, width=1)
    draw.ellipse((-380, 240, 260, 880), fill="#0C1830")
    draw.ellipse((1030, -300, 1600, 260), fill="#0C1830")
    return image


BACKGROUND = make_background()


def draw_header(draw: ImageDraw.ImageDraw, index: int):
    title, chapter, _ = SECTIONS[index]
    draw.rectangle((0, 0, W, 5), fill=CYAN)
    label(draw, (52, 23), "F Y N D   /   DATA QUALITY", 17, CYAN, True)
    label(draw, (52, 58), f"{index + 1:02d}   {chapter}", 14, MUTED, True)
    label(draw, (52, 80), title, 32, WHITE, True)
    rounded(draw, (1010, 30, 1227, 68), PANEL, 18)
    centered(draw, 1118, 49, "SYNTHETIC DATA", 13, GREEN, True)
    draw.line((52, 134, 1228, 134), fill="#26344F", width=2)


def draw_footer(draw: ImageDraw.ImageDraw, index: int, progress: float):
    draw.line((52, 676, 1228, 676), fill="#26344F", width=2)
    draw.line((52, 676, 52 + int(1176 * ((index + progress) / len(SECTIONS))), 676), fill=CYAN, width=3)
    label(draw, (52, 686), "SDET PRACTICE WALKTHROUGH", 13, MUTED, True)
    label(draw, (1154, 686), f"{index + 1:02d} / {len(SECTIONS):02d}", 13, MUTED, True)


def draw_pipeline(draw: ImageDraw.ImageDraw, progress: float):
    names = [("CSV", "Synthetic orders"), ("VALIDATE", "Clean + check"), ("SQLITE", "Accepted rows"), ("REJECTS", "With reasons")]
    xs = [70, 365, 660, 955]
    colors = [CYAN, GREEN, CYAN, RED]
    active = min(int(progress * len(names)), len(names) - 1)
    for i, (name, detail) in enumerate(names):
        x = xs[i]
        rounded(draw, (x, 280, x + 250, 435), PANEL_LIGHT if i == active else PANEL, 20, colors[i] if i == active else "#26344F", 2)
        draw.ellipse((x + 22, 303, x + 54, 335), fill=colors[i])
        centered(draw, x + 140, 361, name, 23, WHITE, True)
        centered(draw, x + 140, 399, detail, 16, MUTED)
        if i < len(names) - 1:
            arrow(draw, (x + 258, 357), (xs[i + 1] - 12, 357))
    for i in range(3):
        start = xs[i] + 258
        end = xs[i + 1] - 12
        phase = (progress * 3 - i) % 1
        dot(draw, start + (end - start) * phase, 357, CYAN, 5)
    rounded(draw, (365, 505, 915, 570), "#10283A", 18, "#225169")
    centered(draw, 640, 537, "A local practice pipeline - not a production integration", 18, CYAN, True)


def draw_schema(draw: ImageDraw.ImageDraw, progress: float):
    fields = ["order_id", "customer_id", "sku", "qty", "unit_price", "order_ts", "updated_at"]
    values = ["ORD-42", "CUS-18", "SKU-7", "2", "19.99", "10:30Z", "10:32Z"]
    x0, y0, cw = 64, 250, 112
    rounded(draw, (52, 218, 854, 492), PANEL, 20)
    for i, (field, value) in enumerate(zip(fields, values)):
        x = x0 + i * cw
        active = i == min(int(progress * len(fields)), len(fields) - 1)
        if active:
            rounded(draw, (x - 3, y0 - 8, x + cw - 5, 457), "#193349", 10)
        label(draw, (x, y0), field, 13, CYAN if active else MUTED, True)
        draw.line((x, y0 + 34, x + cw - 12, y0 + 34), fill="#33415D", width=1)
        label(draw, (x, y0 + 56), value, 14, WHITE)
        label(draw, (x, y0 + 103), value, 14, WHITE)
        label(draw, (x, y0 + 150), value, 14, WHITE)
    label(draw, (82, 451), "CSV ROWS", 12, MUTED, True)
    rounded(draw, (890, 218, 1228, 492), PANEL, 20)
    label(draw, (920, 244), "CONTRACT CHECK", 16, CYAN, True)
    checks = ["exactly 7 columns", "no missing fields", "no extra fields", "read raw values first"]
    for i, value in enumerate(checks):
        y = 294 + i * 44
        dot(draw, 928, y + 9, GREEN if progress >= (i + 1) / 5 else "#3A4B67", 6)
        label(draw, (946, y), value, 16, WHITE if progress >= (i + 1) / 5 else MUTED)
    rounded(draw, (52, 526, 1228, 592), "#10283A", 18, "#225169")
    centered(draw, 640, 559, "Seven required columns are checked before any row is loaded.", 18, WHITE)


def draw_validation(draw: ImageDraw.ImageDraw, progress: float):
    rounded(draw, (58, 233, 352, 505), PANEL, 20)
    label(draw, (84, 255), "RAW CSV ROW", 15, AMBER, True)
    label(draw, (84, 307), 'sku: " sku-104 "', 18, WHITE)
    label(draw, (84, 350), "quantity: 2", 18, WHITE)
    label(draw, (84, 393), "unit_price: 19.99", 18, WHITE)
    label(draw, (84, 436), "timestamp: offset", 18, WHITE)
    arrow(draw, (368, 366), (468, 366), CYAN, 4)
    dot(draw, 375 + 82 * progress, 366, WHITE, 6)
    rounded(draw, (480, 266, 780, 468), PANEL_LIGHT, 22, CYAN, 2)
    centered(draw, 630, 306, "TRANSFORM + VALIDATE", 17, CYAN, True)
    for i, text in enumerate(["trim + uppercase SKU", "positive whole quantity", "non-negative price", "parse timestamps as UTC"]):
        y = 346 + i * 31
        dot(draw, 515, y + 7, GREEN if progress > (i + 1) / 5 else MUTED, 5)
        label(draw, (531, y), text, 14, WHITE)
    arrow(draw, (797, 366), (870, 366), MUTED, 3)
    rounded(draw, (890, 242, 1228, 357), "#102D2A", 18, "#267A68", 2)
    label(draw, (916, 260), "VALID ROW", 14, GREEN, True)
    label(draw, (916, 296), "SKU-104  |  qty 2", 17, WHITE, True)
    rounded(draw, (890, 389, 1228, 505), "#321C2A", 18, "#79344A", 2)
    label(draw, (916, 407), "INVALID ROW", 14, RED, True)
    label(draw, (916, 443), "quantity: -2", 17, WHITE, True)
    label(draw, (916, 476), "reject + reason", 14, MUTED)
    rounded(draw, (58, 540, 1228, 594), PANEL, 16)
    centered(draw, 643, 567, "Bad values are recorded with a clear rejection reason.", 17, MUTED)


def draw_dedup(draw: ImageDraw.ImageDraw, progress: float):
    label(draw, (78, 216), "EXAMPLE SKU: SKU-104", 15, CYAN, True)
    rows = [
        (258, "ORD-101", "SKU-104", "2026-01-07 09:00 UTC", AMBER),
        (370, "ORD-205", "SKU-104", "2026-01-08 12:00 UTC", GREEN),
    ]
    for i, (y, order, sku, updated, color) in enumerate(rows):
        winner = i == 1
        opacity_color = color if progress > (0.25 if i == 0 else 0.6) else "#66738A"
        rounded(draw, (78, y, 754, y + 82), PANEL_LIGHT if winner else PANEL, 16, opacity_color if winner else "#26344F", 2)
        label(draw, (105, y + 15), order, 16, WHITE, True)
        label(draw, (265, y + 15), sku, 16, CYAN)
        label(draw, (421, y + 15), "updated_at", 12, MUTED)
        label(draw, (421, y + 42), updated, 15, WHITE)
        if winner and progress > 0.72:
            rounded(draw, (654, y + 20, 731, y + 59), "#164338", 15)
            centered(draw, 692, y + 39, "KEEP", 13, GREEN, True)
    rounded(draw, (825, 257, 1205, 345), "#30291D", 18, "#725B2E")
    centered(draw, 1015, 281, "STABLE SORT", 16, AMBER, True)
    centered(draw, 1015, 315, "updated_at, then source row", 15, WHITE)
    arrow(draw, (824, 412), (934, 412), CYAN, 4)
    rounded(draw, (953, 370, 1205, 464), "#102D2A", 18, "#267A68")
    centered(draw, 1079, 399, "LATEST UPDATE WINS", 16, GREEN, True)
    centered(draw, 1079, 432, "one SKU remains", 15, WHITE)
    label(draw, (78, 510), "Equal timestamps? The later source row wins.", 17, MUTED)
    rounded(draw, (78, 557, 1205, 603), PANEL, 14)
    centered(draw, 642, 580, "Older duplicates are removed and included in the run accounting.", 16, WHITE)


def draw_loading(draw: ImageDraw.ImageDraw, progress: float):
    rounded(draw, (58, 268, 353, 455), PANEL, 20)
    label(draw, (86, 290), "INCOMING ORDER", 14, MUTED, True)
    label(draw, (86, 338), "SKU-104", 24, WHITE, True)
    label(draw, (86, 380), "updated_at  12:00Z", 16, CYAN)
    arrow(draw, (370, 360), (480, 360), CYAN, 4)
    rounded(draw, (496, 254, 778, 475), PANEL_LIGHT, 22, CYAN, 2)
    centered(draw, 637, 298, "UPSERT", 20, CYAN, True)
    centered(draw, 637, 340, "ON CONFLICT (sku)", 15, WHITE)
    centered(draw, 637, 374, "compare updated_at", 15, MUTED)
    centered(draw, 637, 414, "newer or equal -> update", 14, GREEN)
    arrow(draw, (795, 360), (876, 360), MUTED, 3)
    rounded(draw, (894, 235, 1220, 489), PANEL, 22)
    draw.ellipse((894, 235, 1220, 291), fill="#1B2A42", outline="#33445F", width=2)
    draw.rectangle((894, 263, 1220, 460), fill=PANEL)
    draw.line((894, 263, 894, 460), fill="#33445F", width=2)
    draw.line((1220, 263, 1220, 460), fill="#33445F", width=2)
    draw.ellipse((894, 432, 1220, 489), fill=PANEL, outline="#33445F", width=2)
    centered(draw, 1057, 286, "ORDERS TABLE", 16, WHITE, True)
    for i, (sku, stamp) in enumerate([("SKU-021", "09:15Z"), ("SKU-104", "12:00Z"), ("SKU-330", "10:42Z")]):
        y = 329 + i * 43
        selected = i == 1 and progress > 0.5
        if selected:
            rounded(draw, (914, y - 6, 1200, y + 29), "#153F38", 10)
        label(draw, (930, y), sku, 15, GREEN if selected else WHITE, selected)
        label(draw, (1112, y), stamp, 14, MUTED)
    rounded(draw, (58, 530, 1220, 590), "#10283A", 16)
    centered(draw, 639, 560, "SKU is the primary key; constraints protect required values.", 17, WHITE)


def draw_accounting(draw: ImageDraw.ImageDraw, progress: float):
    parts = [
        (70, "ROWS READ", 20020, CYAN),
        (365, "REJECTED", 15, RED),
        (660, "DUPLICATES", 5, AMBER),
        (955, "ROWS LOADED", 20000, GREEN),
    ]
    positions = [218, 335, 628, 921]
    for i, (x, title, total, color) in enumerate(parts):
        value = round(total * min(1.0, max(0.0, (progress * 1.35 - i * 0.1))))
        rounded(draw, (x, 300, x + 255, 430), PANEL_LIGHT if progress > i / 4 else PANEL, 20, color, 2)
        centered(draw, x + 127, 333, title, 15, color, True)
        centered(draw, x + 127, 386, f"{value:,}", 32, WHITE, True)
    centered(draw, 315, 365, "=", 31, MUTED, True)
    centered(draw, 608, 365, "+", 31, MUTED, True)
    centered(draw, 901, 365, "+", 31, MUTED, True)
    rounded(draw, (149, 493, 1131, 567), "#102D2A", 18, "#267A68", 2)
    centered(draw, 640, 530, "20,020 = 15 + 5 + 20,000", 25, GREEN, True)
    centered(draw, 640, 602, "Rejected  +  duplicate removals  +  loaded  =  every input row", 16, MUTED)


def draw_quality(draw: ImageDraw.ImageDraw, progress: float):
    checks = [
        ("TABLE", "exists + schema is correct"),
        ("COUNT", "row count is positive"),
        ("VALUES", "required values are present"),
        ("UNIQUE", "SKU keys are unique"),
        ("RANGES", "quantity + price are valid"),
    ]
    positions = [(66, 244), (484, 244), (902, 244), (275, 411), (693, 411)]
    for i, ((name, detail), (x, y)) in enumerate(zip(checks, positions)):
        passed = progress > (i + 1) / (len(checks) + 1)
        color = GREEN if passed else "#3A4B67"
        rounded(draw, (x, y, x + 312, y + 122), PANEL_LIGHT if passed else PANEL, 18, color, 2)
        dot(draw, x + 30, y + 35, color, 9)
        label(draw, (x + 54, y + 18), name, 15, CYAN if passed else MUTED, True)
        label(draw, (x + 22, y + 66), detail, 15, WHITE)
        if passed:
            centered(draw, x + 275, y + 35, "PASS", 13, GREEN, True)
    rounded(draw, (260, 577, 1020, 619), "#102D2A", 16, "#267A68")
    centered(draw, 640, 598, "Any failed check blocks release with a non-zero exit.", 15, GREEN, True)


def draw_tests(draw: ImageDraw.ImageDraw, progress: float):
    rounded(draw, (65, 228, 496, 512), "#101725", 20, "#31405A", 2)
    rounded(draw, (65, 228, 496, 273), "#1C2940", 18)
    for i, color in enumerate([RED, AMBER, GREEN]):
        dot(draw, 91 + i * 25, 251, color, 6)
    label(draw, (91, 299), "python -m pytest -q", 18, CYAN, True)
    for i in range(5):
        y = 354 + i * 28
        label(draw, (93, y), f"test_{i + 1:02d}", 14, MUTED)
        if progress > (i + 1) / 6:
            label(draw, (360, y), "PASS", 13, GREEN, True)
    rounded(draw, (91, 490, 466, 535), "#102D2A", 14)
    centered(draw, 278, 512, "36 tests passed", 16, GREEN, True)
    cards = [
        ("CONTRACT", "missing / extra columns"),
        ("BOUNDARIES", "zero price, quantity one"),
        ("NEGATIVE", "bad values + timestamps"),
        ("BEHAVIOUR", "duplicates, upsert, release"),
    ]
    for i, (title, detail) in enumerate(cards):
        x = 550 + (i % 2) * 339
        y = 237 + (i // 2) * 143
        passed = progress > (i + 1) / 5
        rounded(draw, (x, y, x + 310, y + 117), PANEL_LIGHT if passed else PANEL, 18, GREEN if passed else "#26344F", 2)
        label(draw, (x + 20, y + 18), title, 14, CYAN, True)
        label(draw, (x + 20, y + 53), detail, 15, WHITE)
        if passed:
            dot(draw, x + 278, y + 84, GREEN, 7)
    centered(draw, 890, 554, "Positive + boundary + negative coverage", 16, MUTED)


def draw_evidence(draw: ImageDraw.ImageDraw, progress: float):
    metrics = [
        ("ROWS READ", 20020, CYAN),
        ("REJECTED", 15, RED),
        ("DUPLICATES", 5, AMBER),
        ("LOADED", 20000, GREEN),
    ]
    for i, (name, total, color) in enumerate(metrics):
        x = 62 + i * 296
        value = round(total * min(1.0, progress * 1.8))
        rounded(draw, (x, 252, x + 264, 385), PANEL, 20, color, 2)
        label(draw, (x + 22, 274), name, 14, color, True)
        label(draw, (x + 22, 317), f"{value:,}", 32, WHITE, True)
        label(draw, (x + 22, 359), "documented sample run", 13, MUTED)
    rounded(draw, (90, 445, 1190, 525), "#101725", 18, "#31405A", 2)
    label(draw, (118, 469), "python -m src.etl_pipeline ...", 16, CYAN, True)
    label(draw, (738, 469), "JUnit report  +  release gate", 16, MUTED)
    rounded(draw, (429, 557, 851, 609), "#102D2A", 17, "#267A68", 2)
    centered(draw, 640, 583, "RUN RECONCILED  /  QUALITY GATE PASS", 16, GREEN, True)


def draw_close(draw: ImageDraw.ImageDraw, progress: float):
    centered(draw, 640, 202, "Clear evidence. Honest boundaries.", 27, WHITE, True)
    cards = [
        (76, "PRACTICE ONLY", "No production integration", CYAN),
        (463, "SYNTHETIC DATA", "No real customer records", GREEN),
        (850, "ADAPT TO BRIEF", "Use the registered track", AMBER),
    ]
    for x, title, detail, color in cards:
        rounded(draw, (x, 267, x + 350, 412), PANEL, 20, color, 2)
        dot(draw, x + 32, 305, color, 10)
        label(draw, (x + 56, 287), title, 16, color, True)
        label(draw, (x + 24, 347), detail, 16, WHITE)
    steps = ["TEST", "DOCUMENT", "REVIEW", "SUBMIT"]
    for i, step in enumerate(steps):
        x = 155 + i * 260
        color = GREEN if progress > (i + 1) / 5 else "#52617A"
        rounded(draw, (x, 491, x + 174, 548), PANEL_LIGHT, 16, color, 2)
        centered(draw, x + 87, 520, step, 14, WHITE if color == GREEN else MUTED, True)
        if i < len(steps) - 1:
            arrow(draw, (x + 184, 520), (x + 247, 520), MUTED, 2)
    rounded(draw, (222, 582, 1058, 623), "#10283A", 15)
    centered(draw, 640, 602, "Review the video and verify the evidence before sharing.", 15, CYAN)


SCENE_DRAWERS = [
    draw_pipeline, draw_schema, draw_validation, draw_dedup, draw_loading,
    draw_accounting, draw_quality, draw_tests, draw_evidence, draw_close,
]


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    match = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", result.stderr)
    if not match:
        raise RuntimeError(f"Could not read video duration for {path}: {result.stderr}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def scene_boundaries(path: Path) -> list[float]:
    result = subprocess.run(
        [
            FFMPEG, "-v", "error", "-i", str(path),
            "-vf", "fps=1,scale=64:36,format=rgb24",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        capture_output=True,
        check=True,
    )
    frame_size = 64 * 36 * 3
    frame_count = len(result.stdout) // frame_size
    if frame_count < 2:
        raise RuntimeError(f"No usable video frames found in {path}")

    frames = [
        Image.frombytes("RGB", (64, 36), result.stdout[offset:offset + frame_size])
        for offset in range(0, frame_count * frame_size, frame_size)
    ]
    boundaries = []
    for second, (previous, current) in enumerate(zip(frames, frames[1:]), start=1):
        difference = ImageChops.difference(previous, current)
        delta = sum(ImageStat.Stat(difference).mean) / 3
        if delta > 1:
            boundaries.append(float(second))

    expected = len(SECTIONS) - 1
    if len(boundaries) != expected:
        raise RuntimeError(
            f"Expected {expected} narration scene changes, found {len(boundaries)}. "
            "Check that the source video still has its original section slides."
        )
    return boundaries


def render_video(silent_video: Path, duration: float, starts: list[float]) -> None:
    command = [
        FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24",
        "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
        "-an", "-r", str(VIDEO_FPS), "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        str(silent_video),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    section_starts = [0.0, *starts]
    section_ends = [*starts, duration]
    frame_count = round(duration * FPS)
    try:
        for frame_number in range(frame_count):
            timestamp = frame_number / FPS
            index = bisect.bisect_right(section_starts, timestamp) - 1
            index = min(index, len(SECTIONS) - 1)
            section_duration = section_ends[index] - section_starts[index]
            progress = (timestamp - section_starts[index]) / section_duration
            frame = BACKGROUND.copy()
            draw = ImageDraw.Draw(frame)
            draw_header(draw, index)
            SCENE_DRAWERS[index](draw, min(1.0, max(0.0, progress)))
            draw_footer(draw, index, min(1.0, max(0.0, progress)))
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        error = process.stderr.read()
        return_code = process.wait()
    except Exception:
        process.kill()
        process.wait()
        raise
    if return_code:
        raise RuntimeError(f"FFmpeg could not render the animated video: {error.decode(errors='replace')}")


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Source walkthrough not found: {SOURCE}")
    duration = probe_duration(SOURCE)
    starts = scene_boundaries(SOURCE)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="walkthrough-") as temp_dir:
        silent_video = Path(temp_dir) / "animated-silent.mp4"
        render_video(silent_video, duration, starts)
        subprocess.run(
            [
                FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(silent_video), "-i", str(SOURCE),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "copy",
                "-t", f"{duration:.3f}", "-movflags", "+faststart",
                str(OUTPUT),
            ],
            check=True,
        )

    print(f"Created: {OUTPUT}")
    print(f"Duration: {duration:.2f} seconds; narration preserved from source.")
    print("Scene starts: " + ", ".join(f"{start:.0f}s" for start in starts))


if __name__ == "__main__":
    main()
