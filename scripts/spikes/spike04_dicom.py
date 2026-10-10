#!/usr/bin/env python3
"""SPIKE-04 — which DICOM transfer syntaxes decode with the installed handlers.

Uses the sample files that ship inside the pydicom wheel (no download needed)
and reports, per file, whether the pixel data decodes and how long it takes.

Usage: python scripts/spikes/spike04_dicom.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

import pydicom
from pydicom.data import get_testdata_file

SAMPLES = [
    "CT_small.dcm",                    # CT, explicit VR little endian (uncompressed)
    "MR_small_implicit.dcm",           # implicit VR little endian
    "MR_small_bigendian.dcm",          # explicit VR big endian (retired, still seen)
    "MR_small_RLE.dcm",                # RLE lossless
    "MR_small_jpeg_ls_lossless.dcm",   # JPEG-LS lossless
    "MR_small_jp2klossless.dcm",       # JPEG 2000 lossless
    "JPEG2000.dcm",                    # JPEG 2000 (lossy)
    "JPEG-lossy.dcm",                  # JPEG extended (process 2/4)
    "SC_rgb_jpeg_dcmtk.dcm",           # JPEG baseline, RGB secondary capture
    "image_dfl.dcm",                   # deflated explicit VR little endian
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    results = {"platform": platform.platform(), "pydicom": pydicom.__version__, "files": {}}
    for name in SAMPLES:
        path = get_testdata_file(name)
        if path is None:
            results["files"][name] = {"decoded": False, "reason": "sample not bundled"}
            continue
        dataset = pydicom.dcmread(path)
        entry = {"transfer_syntax": dataset.file_meta.TransferSyntaxUID.name, "modality": str(dataset.get("Modality", ""))}
        start = time.perf_counter()
        try:
            array = dataset.pixel_array
            entry.update(decoded=True, shape=list(array.shape), dtype=str(array.dtype))
        except Exception as error:
            entry.update(decoded=False, reason=f"{type(error).__name__}: {str(error)[:120]}")
        entry["ms"] = round((time.perf_counter() - start) * 1000, 1)
        results["files"][name] = entry
        print(name, entry, flush=True)
    if args.json:
        args.json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
