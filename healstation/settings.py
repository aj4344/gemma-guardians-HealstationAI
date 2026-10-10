"""A snapshot of config.py values for the case store, ingestion and job system.

config.py stays the only place that reads the environment; this dataclass
lets tests build an isolated runtime (temporary data directory, test key)
without patching module globals.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path

import config

MB = 1024 * 1024


@dataclass
class Settings:
    deployment_mode: str = config.DEPLOYMENT_MODE
    data_dir: Path = config.DATA_DIR
    kek_env: str = config.HEALSTATION_KEK
    kek_file: Path | None = config.KEK_FILE
    kek_use_keyring: bool = config.KEK_USE_KEYRING
    kek_auto_create: bool = config.KEK_AUTO_CREATE

    case_retention_days: int = config.CASE_RETENTION_DAYS
    retain_raw_uploads: bool = config.RETAIN_RAW_UPLOADS
    sweep_interval_seconds: int = config.SWEEP_INTERVAL_SECONDS
    audio_retention_seconds: int = config.AUDIO_RETENTION_SECONDS

    max_audio_bytes: int = config.MAX_AUDIO_MB * MB
    max_audio_seconds: int = config.MAX_AUDIO_SECONDS
    max_image_bytes: int = config.MAX_IMAGE_MB * MB
    max_image_pixels: int = config.MAX_IMAGE_PIXELS
    image_max_edge_px: int = config.IMAGE_MAX_EDGE_PX
    max_pdf_bytes: int = config.MAX_PDF_MB * MB
    max_pdf_pages: int = config.MAX_PDF_PAGES
    max_ocr_pages: int = config.MAX_OCR_PAGES
    pdf_parser_cpu_seconds: int = config.PDF_PARSER_CPU_SECONDS
    pdf_parser_memory_mb: int = config.PDF_PARSER_MEMORY_MB
    max_dicom_upload_bytes: int = config.MAX_DICOM_UPLOAD_MB * MB
    max_dicom_files: int = config.MAX_DICOM_FILES
    max_dicom_uncompressed_bytes: int = config.MAX_DICOM_UNCOMPRESSED_MB * MB
    max_zip_ratio: int = config.MAX_ZIP_RATIO
    max_key_slices: int = config.MAX_KEY_SLICES
    max_attachments_per_case: int = config.MAX_ATTACHMENTS_PER_CASE
    max_recordings_per_case: int = config.MAX_RECORDINGS_PER_CASE

    max_queue_depth: int = config.MAX_QUEUE_DEPTH
    pools: dict[str, int] = field(
        default_factory=lambda: {
            "llm": config.POOL_LLM,
            "stt": config.POOL_STT,
            "ocr": config.POOL_OCR,
            "pdf": config.POOL_PDF,
            "imaging": config.POOL_IMAGING,
        }
    )
    timeout_llm_s: float = config.TIMEOUT_LLM_S
    timeout_ocr_page_s: float = config.TIMEOUT_OCR_PAGE_S
    timeout_imaging_s: float = config.TIMEOUT_IMAGING_S

    storage_quota_bytes: int = int(config.CASE_STORAGE_QUOTA_GB * 1024 * MB)
    min_free_disk_bytes: int = int(config.MIN_FREE_DISK_GB * 1024 * MB)

    @property
    def is_hub(self) -> bool:
        return self.deployment_mode == "hub"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "healstation.db"

    def replace(self, **changes) -> Settings:
        return dataclasses.replace(self, **changes)
