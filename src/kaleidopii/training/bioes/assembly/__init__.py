"""BIOES corpus assembly seam shared by local and Modal adapters."""

from kaleidopii.training.bioes.assembly.mix import (
    AssemblyGateError,
    AssemblyResult,
    assemble_bioes_v2_corpus,
    discover_assembly_source_files,
    parse_waiver_cells,
)
from kaleidopii.training.bioes.data.mixed_build import (
    DEFAULT_ENTROPY_TARGETS,
    DEFAULT_LABEL_FLOORS,
)

__all__ = [
    "DEFAULT_ENTROPY_TARGETS",
    "DEFAULT_LABEL_FLOORS",
    "AssemblyGateError",
    "AssemblyResult",
    "assemble_bioes_v2_corpus",
    "discover_assembly_source_files",
    "parse_waiver_cells",
]
