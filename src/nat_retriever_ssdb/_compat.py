"""Toolkit-compat shims.

The plugin is designed to register with the NVIDIA NeMo Agent Toolkit when the
toolkit is installed (extras ``[toolkit]``), but to remain importable and
testable on hosts that do not have the toolkit available (demos, CI smoke
tests, packaging checks).

This module exposes ``RetrieverBaseConfig``, ``RetrieverOutput``, and
``RetrievedItem`` symbols that prefer the real toolkit classes when present,
falling back to local Pydantic-based equivalents that share the same surface
(``items: list[RetrievedItem]``, ``content: str``, ``metadata: dict``).
"""
from __future__ import annotations

from typing import Any

try:  # pragma: no cover - exercised only when nvidia-nat is installed
    from nat.data_models.retriever import RetrieverBaseConfig as _ToolkitBase  # type: ignore
    from nat.retriever.models import (  # type: ignore
        RetrievedItem as _ToolkitItem,
        RetrieverOutput as _ToolkitOutput,
    )

    RetrieverBaseConfig = _ToolkitBase
    RetrievedItem = _ToolkitItem
    RetrieverOutput = _ToolkitOutput
    HAS_TOOLKIT = True
except Exception:  # ImportError or attribute drift across toolkit minors.
    from pydantic import BaseModel, ConfigDict, Field

    class RetrieverBaseConfig(BaseModel):  # type: ignore[no-redef]
        """Lightweight stand-in for ``nat.data_models.retriever.RetrieverBaseConfig``.

        The toolkit's real class accepts a ``name=`` class kwarg used to bind
        the YAML discriminator. We accept and silently store that here so the
        same source declares cleanly with or without the toolkit installed.
        """

        model_config = ConfigDict(extra="allow")
        _registered_name: str | None = None

        def __init_subclass__(cls, name: str | None = None, **kwargs: Any) -> None:
            super().__init_subclass__(**kwargs)
            if name is not None:
                cls._registered_name = name

    class RetrievedItem(BaseModel):  # type: ignore[no-redef]
        content: str = ""
        metadata: dict = Field(default_factory=dict)

    class RetrieverOutput(BaseModel):  # type: ignore[no-redef]
        items: list[RetrievedItem] = Field(default_factory=list)

        def __iter__(self):  # convenience for demo scripts
            return iter(self.items)

        def __len__(self) -> int:
            return len(self.items)

    HAS_TOOLKIT = False


__all__ = [
    "RetrieverBaseConfig",
    "RetrievedItem",
    "RetrieverOutput",
    "HAS_TOOLKIT",
]
