from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from kaleidopii.spans import CharSpan
    from kaleidopii.taxonomy import PiiLabel


class PiiAdapter(Protocol):
    name: str
    supported_labels: frozenset[PiiLabel]

    def load(self) -> None: ...

    def predict(self, texts: list[str]) -> list[list[CharSpan]]: ...
