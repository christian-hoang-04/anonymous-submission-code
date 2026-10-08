"""Full benchmark execution facade."""

from pii.pdf_redaction.benchmark.execution_matrix import execute_full_matrix
from pii.pdf_redaction.benchmark.execution_types import (
    FullMatrixExecution,
    FullMatrixInputs,
)

__all__ = ["FullMatrixExecution", "FullMatrixInputs", "execute_full_matrix"]
