from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
WORK = OUT / "indian-walkthrough-work"
FFPROBE = Path.home() / "AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.1-full_build/bin/ffprobe.exe"
FFMPEG = FFPROBE.with_name("ffmpeg.exe")

W, H = 1920, 1080
NAVY = "#0B1020"
PANEL = "#151C31"
CYAN = "#37C8FF"
GREEN = "#63E6BE"
WHITE = "#F7F9FC"
MUTED = "#AEB7CA"
AMBER = "#FFCC66"
RED = "#FF7A90"


SECTIONS = [
    (
        "1  Project goal",
        "Goal and scope",
        [
            "SDET Intern practice project",
            "Synthetic order data",
            "CSV in  ->  validation  ->  SQLite + rejects",
            "Automated release-quality gate",
        ],
        'Namaste. This is a practice SDET project built around an order data ETL pipeline. The input is synthetic order data from a CSV file. The pipeline reads each row, cleans and validates it, sends invalid rows to a rejects file, and loads valid orders into SQLite. The purpose is to show how test design, data quality checks, and an automated release gate work together. Most importantly, this is a local practice implementation, not an integration with Fynd production systems, and no real customer data is involved.',
    ),
    (
        "2  Source contract",
        "CSV input and schema contract",
        [
            "ORDER_COLUMNS",
            "order_id  customer_id  sku",
            "quantity  unit_price",
            "order_timestamp  updated_at",
        ],
        "The source contract is defined in etl pipeline dot py. It expects exactly seven columns: order ID, customer ID, SKU, quantity, unit price, order timestamp, and updated timestamp. The code checks the actual column set before processing. Extra columns or missing columns are rejected before any data is loaded. Reading the CSV as strings first is deliberate, because it gives us a chance to validate raw values instead of allowing pandas to silently convert bad data.",
    ),
    (
        "3  Validation",
        "Transform: validate and clean",
        [
            "strip text and uppercase SKU",
            "quantity > 0 and integral",
            "unit_price >= 0",
            "timestamps must parse in UTC",
        ],
        "The transform step creates a source row number and normalizes text. It removes leading and trailing spaces and converts every SKU to upper case. Quantity must be a positive whole number. Unit price must be numeric and cannot be negative. Both timestamps are parsed with UTC handling and then stored in a consistent format. Each rejected row receives one clear reason, such as missing quantity or invalid timestamp, so a tester can quickly diagnose the exact failure.",
    ),
    (
        "4  Deduplication",
        "Duplicate-SKU resolution",
        [
            "sort by updated_at",
            "stable sorting by source row",
            "keep the latest row",
            "count duplicates removed",
        ],
        "After validation, the pipeline resolves duplicate SKUs. It sorts rows by update time and then by source row, using stable sorting. The latest update is intended to win. If two rows have exactly the same timestamp, the later source row wins. The older duplicate is removed and the duplicate count is reported. The final SQLite target therefore contains only one row for each SKU.",
    ),
    (
        "5  Loading",
        "SQLite load and upsert",
        [
            "orders table",
            "SKU is the primary key",
            "NOT NULL constraints",
            "ON CONFLICT  ...  DO UPDATE",
        ],
        "The clean rows are loaded into SQLite by an upsert. The orders table uses SKU as the primary key and also defines required columns and numeric constraints. If a SKU already exists, the insert statement updates the order only when the incoming updated timestamp is newer or equal to the stored timestamp. This makes repeated runs and append-based watch mode deterministic and prevents an older update from overwriting newer data.",
    ),
    (
        "6  Accounting",
        "Every row must be accounted for",
        [
            "rows_read",
            "= rows_rejected",
            "+ duplicates_removed",
            "+ rows_loaded",
        ],
        "Before loading, the pipeline applies a row accounting invariant. Rows read must equal rejected rows, plus duplicates removed, plus rows loaded. This is a simple but powerful audit check. If the equation fails, the program raises an error instead of quietly producing an incomplete result. For testers, this gives a direct way to prove that every source row has one of the three valid outcomes: loaded, rejected, or removed as a duplicate.",
    ),
    (
        "7  Quality checks",
        "Release gate",
        [
            "table exists and schema is correct",
            "row count is positive",
            "required values are not blank",
            "SKU uniqueness and numeric ranges",
        ],
        "The data quality module checks the loaded table after the ETL run. It verifies that the table and required columns exist, the row count is positive, required values are not null or blank, SKU values are unique, and quantity and price satisfy numeric constraints. The report module acts as the release gate. It prints each check separately and exits with an error if any check fails.",
    ),
    (
        "8  Tests",
        "Automated test coverage",
        [
            "CSV contract tests",
            "boundary and negative cases",
            "duplicate resolution",
            "upsert and release checks",
        ],
        "The pytest suite covers the CSV contract, transformations, boundary values, invalid values, duplicate handling, upserts, rejects, watch mode, and release checks. It includes positive tests for valid orders, negative tests for bad quantities and prices, and boundary tests for values such as zero price and quantity one. This mix gives confidence that normal behaviour and likely failure cases have both been considered.",
    ),
    (
        "9  Run evidence",
        "Commands and expected evidence",
        [
            "python -m src.etl_pipeline ...",
            "20,020 rows read",
            "15 rejected  |  5 duplicates",
            "20,000 rows loaded",
        ],
        "The normal documented run reads twenty thousand and twenty rows. It rejects fifteen rows, removes five duplicate SKUs, and loads twenty thousand orders. pytest produces a JUnit XML report. The release gate prints pass results for schema, row count, null handling, uniqueness, and value ranges. This evidence makes the result easy to review because the command output, database state, rejects file, and test report agree with each other.",
    ),
    (
        "10  Close",
        "Limitations and submission",
        [
            "Do not claim production integration",
            "Keep challenge material private",
            "Use synthetic or supplied data",
            "Upload an unlisted, verified video",
        ],
        "Before submission, I would clearly separate this practice evidence from the actual challenge use case. The project has no production integration, no real scale testing, and no credentials. I would adapt the pipeline and test cases to the registered track, document assumptions and known limitations, verify the JUnit report and release gate, and remove or isolate any temporary files. Finally, I would review the video with captions where required and upload it as unlisted.",
    ),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_round_rect(draw: ImageDraw.ImageDraw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def make_slide(index: int, title: str, bullets: list[str]) -> Path:
    image = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, W, 18), fill=CYAN)
    draw.text((90, 65), title, font=font(58, True), fill=WHITE)
    draw.text((90, 150), SECTIONS[index][0], font=font(26), fill=CYAN)

    draw.line((90, 205, 1830, 205), fill="#27324E", width=2)

    panel_box = (90, 250, 1830, 920)
    draw_round_rect(draw, panel_box, 28, PANEL)

    code_font = font(43)
    y = 320
    for i, bullet in enumerate(bullets):
        color = GREEN if i % 2 == 0 else AMBER
        draw.rounded_rectangle((145, y - 8, 178, y + 25), radius=12, fill=color)
        draw.text((215, y - 16), bullet, font=code_font, fill=WHITE)
        y += 145

    draw.text((90, 990), f"{index + 1:02d} / {len(SECTIONS):02d}", font=font(24), fill=MUTED)
    draw.text((1530, 990), "Fynd ETL  |  SDET Practice", font=font(24), fill=MUTED)

    path = WORK / f"slide-{index:02d}.png"
    image.save(path)
    return path


def duration(path: Path) -> float:
    result = subprocess.run(
        [str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


async def synthesize(index: int, text: str) -> tuple[Path, float]:
    mp3 = WORK / f"audio-{index:02d}.mp3"
    communicate = edge_tts.Communicate(text, "en-IN-PrabhatNeural", rate="-14%", pitch="-2Hz")
    await communicate.save(str(mp3))
    return mp3, duration(mp3)


def render_segment(index: int, slide: Path, audio: Path, seconds: float) -> Path:
    video = WORK / f"segment-{index:02d}.mp4"
    subprocess.run(
        [
            str(FFMPEG), "-y", "-loop", "1", "-i", str(slide),
            "-i", str(audio), "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k", "-r", "30", "-pix_fmt", "yuv420p",
            "-t", f"{seconds + 4.2:.3f}", "-shortest", str(video),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    return video


async def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    segments = []
    for index, (_, title, bullets, narration) in enumerate(SECTIONS):
        slide = make_slide(index, title, bullets)
        audio, seconds = await synthesize(index, narration)
        segments.append(render_segment(index, slide, audio, seconds))
        print(f"Rendered section {index + 1}/{len(SECTIONS)}: {seconds:.1f} seconds")

    concat = WORK / "concat.txt"
    concat.write_text("\n".join(f"file '{path.as_posix()}'" for path in segments), encoding="utf-8")
    final = OUT / "project-walkthrough-indian.mp4"
    subprocess.run(
        [
            str(FFMPEG), "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat), "-c", "copy", str(final),
        ],
        check=True,
    )
    print(f"Created {final}")
    print(f"Duration: {duration(final):.1f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
