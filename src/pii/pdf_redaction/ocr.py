"""OCR geometry and runtime facade."""

from pii.pdf_redaction.ocr_backends import (
    RapidOcrEngineFactory,
    SubprocessTesseractRunner,
)
from pii.pdf_redaction.ocr_geometry import RapidOcrAdapter, TesseractTsvAdapter
from pii.pdf_redaction.ocr_types import (
    GeometryOcr,
    OcrAdapterError,
    OpenVinoPerformanceHint,
    PixelToPageTransform,
    RapidOcrBackend,
    RapidOcrModelTier,
    RapidOcrRuntimeConfig,
    RasterPage,
    TesseractRunner,
)

__all__ = [
    "GeometryOcr",
    "OcrAdapterError",
    "OpenVinoPerformanceHint",
    "PixelToPageTransform",
    "RapidOcrAdapter",
    "RapidOcrBackend",
    "RapidOcrEngineFactory",
    "RapidOcrModelTier",
    "RapidOcrRuntimeConfig",
    "RasterPage",
    "SubprocessTesseractRunner",
    "TesseractRunner",
    "TesseractTsvAdapter",
]
