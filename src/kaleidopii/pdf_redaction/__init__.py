"""Source-bound PDF PII preview, destructive writing, and verification."""

from kaleidopii.bioes_inference import create_default_detector
from kaleidopii.pdf_redaction.contracts import ReviewedRedaction
from kaleidopii.pdf_redaction.document import PdfiumDocumentAdapter
from kaleidopii.pdf_redaction.errors import (
    InputDocumentError,
    OutputPathError,
    PdfRedactionError,
    RedactionApplyError,
    VerificationError,
)
from kaleidopii.pdf_redaction.extraction import PdfiumExtractor
from kaleidopii.pdf_redaction.ocr import RapidOcrAdapter
from kaleidopii.pdf_redaction.pipeline import (
    PdfGeometryPreparer,
    PdfRedactionPipeline,
    PipelineVerificationError,
    PreparedDocument,
    RedactionPreview,
    VerifiedRedactionOutput,
)
from kaleidopii.pdf_redaction.verification import (
    IndependentPdfVerifier,
    VerificationToolchain,
)
from kaleidopii.pdf_redaction.writers import (
    RasterRebuildWriter,
)

__all__ = (
    "IndependentPdfVerifier",
    "InputDocumentError",
    "OutputPathError",
    "PdfGeometryPreparer",
    "PdfRedactionError",
    "PdfRedactionPipeline",
    "PdfiumDocumentAdapter",
    "PdfiumExtractor",
    "PipelineVerificationError",
    "PreparedDocument",
    "RapidOcrAdapter",
    "RasterRebuildWriter",
    "RedactionApplyError",
    "RedactionPreview",
    "ReviewedRedaction",
    "VerificationError",
    "VerificationToolchain",
    "VerifiedRedactionOutput",
    "create_default_detector",
)
