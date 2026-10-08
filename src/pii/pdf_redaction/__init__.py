"""Source-bound PDF PII preview, destructive writing, and verification."""

from pii.bioes_inference import create_default_detector
from pii.pdf_redaction.contracts import ReviewedRedaction
from pii.pdf_redaction.document import PdfiumDocumentAdapter
from pii.pdf_redaction.errors import (
    InputDocumentError,
    OutputPathError,
    PdfRedactionError,
    RedactionApplyError,
    VerificationError,
)
from pii.pdf_redaction.extraction import PdfiumExtractor
from pii.pdf_redaction.ocr import RapidOcrAdapter
from pii.pdf_redaction.pipeline import (
    PdfGeometryPreparer,
    PdfRedactionPipeline,
    PipelineVerificationError,
    PreparedDocument,
    RedactionPreview,
    VerifiedRedactionOutput,
)
from pii.pdf_redaction.verification import (
    IndependentPdfVerifier,
    VerificationToolchain,
)
from pii.pdf_redaction.writers import (
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
