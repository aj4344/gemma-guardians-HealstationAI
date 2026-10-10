#!/usr/bin/env python3
"""SPIKE-03 — OCR quality for lab reports (eng+hin+mar) on this machine.

No real (de-identified) reports are available in the build container, so this
spike renders 20 synthetic reports in the layouts common in Indian labs
(English test names, Hindi/Marathi headers and labels), degrades them like a
phone photo or a cheap scan, and measures how many numeric results Tesseract
recovers exactly. Re-run it on real de-identified reports before release.

Usage: python scripts/spikes/spike03_ocr.py [--json out.json]
"""

from __future__ import annotations

import argparse
import io
import json
import random
import re
import statistics
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

FONT_DIR = Path(__file__).resolve().parents[2] / "healstation" / "assets" / "fonts"
LATIN = FONT_DIR / "NotoSans-Regular.ttf"
DEVA = FONT_DIR / "NotoSansDevanagari-Regular.ttf"

HEADERS = {
    "en": ("City Diagnostic Laboratory", "Patient: XXXX  Age/Sex: 45/M  Date: 12/03/2026"),
    "hi": ("सिटी पैथोलॉजी लैब", "रोगी: XXXX  आयु/लिंग: 45/पु  दिनांक: 12/03/2026"),
    "mr": ("सिटी पॅथॉलॉजी लॅब", "रुग्ण: XXXX  वय/लिंग: 45/पु  दिनांक: 12/03/2026"),
}
TESTS = [
    ("Haemoglobin", "g/dL", (6.0, 16.0), "13.0 - 17.0"),
    ("Total Leucocyte Count", "/cumm", (1500, 32000), "4000 - 11000"),
    ("Platelet Count", "lakh/cumm", (0.1, 4.5), "1.5 - 4.5"),
    ("Serum Potassium", "mmol/L", (2.5, 7.5), "3.5 - 5.1"),
    ("Serum Sodium", "mmol/L", (115, 165), "135 - 145"),
    ("Blood Sugar (Random)", "mg/dL", (45, 480), "70 - 140"),
    ("Serum Creatinine", "mg/dL", (0.5, 6.0), "0.7 - 1.3"),
]


def _value(low: float, high: float, rng: random.Random) -> str:
    value = rng.uniform(low, high)
    return f"{value:.0f}" if high > 100 else f"{value:.1f}"


def render_report(language: str, rng: random.Random, scale: float) -> tuple[Image.Image, list[str]]:
    width, height = int(1240 * scale), int(1000 * scale)
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    size = int(26 * scale)
    deva = ImageFont.truetype(str(DEVA), size)
    latin = ImageFont.truetype(str(LATIN), size)
    title, sub = HEADERS[language]
    head_font = deva if language != "en" else latin
    y = int(40 * scale)
    draw.text((int(60 * scale), y), title, font=head_font, fill=0)
    y += int(50 * scale)
    draw.text((int(60 * scale), y), sub, font=head_font, fill=0)
    y += int(70 * scale)
    expected = []
    for name, unit, (low, high), ref in TESTS:
        value = _value(low, high, rng)
        expected.append(value)
        for x, text in ((60, name), (560, value), (720, unit), (930, ref)):
            draw.text((int(x * scale), y), text, font=latin, fill=0)
        y += int(56 * scale)
    return image, expected


def degrade(image: Image.Image, rng: random.Random) -> Image.Image:
    image = image.rotate(rng.uniform(-1.5, 1.5), expand=True, fillcolor=255)
    image = image.filter(ImageFilter.GaussianBlur(rng.uniform(0.4, 1.0)))
    noisy = image.point(lambda p: max(0, min(255, p + rng.randint(-25, 25))))
    buffer = io.BytesIO()
    noisy.save(buffer, format="JPEG", quality=55)
    return Image.open(io.BytesIO(buffer.getvalue())).convert("L")


def preprocess(image: Image.Image, mode: str) -> Image.Image:
    if mode == "none":
        return image
    image = ImageOps.autocontrast(image)
    if mode == "binarize":
        histogram = image.histogram()
        total = sum(histogram)
        # Otsu threshold
        sum_all = sum(i * h for i, h in enumerate(histogram))
        weight_bg = sum_bg = 0
        best, threshold = 0.0, 128
        for i, count in enumerate(histogram):
            weight_bg += count
            if not weight_bg or weight_bg == total:
                continue
            sum_bg += i * count
            mean_bg = sum_bg / weight_bg
            mean_fg = (sum_all - sum_bg) / (total - weight_bg)
            between = weight_bg * (total - weight_bg) * (mean_bg - mean_fg) ** 2
            if between > best:
                best, threshold = between, i
        image = image.point(lambda p: 255 if p > threshold else 0)
    return image


def ocr(image: Image.Image, langs: str) -> tuple[str, float]:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    result = subprocess.run(
        ["tesseract", "stdin", "stdout", "-l", langs, "--psm", "6", "tsv"],
        input=buffer.getvalue(),
        capture_output=True,
        check=True,
    )
    words, confidences = [], []
    for line in result.stdout.decode("utf-8", "replace").splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) == 12 and parts[11].strip() and float(parts[10]) >= 0:
            words.append(parts[11])
            confidences.append(float(parts[10]))
    return " ".join(words), (statistics.mean(confidences) if confidences else 0.0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    languages = ["en"] * 7 + ["hi"] * 7 + ["mr"] * 6
    # scale 1.0 ~ 150 DPI for an A4-width page; 1.33 ~ 200 DPI; 2.0 ~ 300 DPI
    configs = [(scale, mode) for scale in (1.0, 1.33, 2.0) for mode in ("none", "autocontrast", "binarize")]
    report = {}
    for scale, mode in configs:
        rng = random.Random(42)
        hits = total = 0
        confidences, seconds = [], []
        for language in languages:
            image, expected = render_report(language, rng, scale)
            image = preprocess(degrade(image, rng), mode)
            start = time.perf_counter()
            text, confidence = ocr(image, "eng+hin+mar")
            seconds.append(time.perf_counter() - start)
            confidences.append(confidence)
            found = re.findall(r"\d+(?:\.\d+)?", text)
            for value in expected:
                total += 1
                hits += value in found
        key = f"dpi~{round(150 * scale)}/{mode}"
        report[key] = {
            "numeric_recall": round(hits / total, 3),
            "mean_word_confidence": round(statistics.mean(confidences), 1),
            "seconds_per_page_median": round(statistics.median(seconds), 2),
        }
        print(key, report[key], flush=True)
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
