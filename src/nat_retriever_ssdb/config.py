"""Pydantic config for the SSDB retriever (binds to ``_type: ssdb_retriever``)."""
from __future__ import annotations

from typing import Optional

from pydantic import Field, HttpUrl

from ._compat import RetrieverBaseConfig


class SSDBRetrieverConfig(RetrieverBaseConfig, name="ssdb_retriever"):
    """SecretSkyDB retriever — encrypted nearest-neighbor over secret-shared,
    finite-field integer vectors stored in Postgres + ssdbpgvector shareholders.

    Notably absent: ``embedding_model``. Embedding lives next to the SSDB proxy
    inside the trust boundary so float vectors never cross it. See
    ``ssdb_nemo_plugin_design.pdf`` §10 for the rationale.
    """

    uri: HttpUrl = Field(
        description="Base URL of the SSDB bridge (the /api/retrieve endpoint is appended).",
    )
    collection_name: str = Field(
        default="default",
        description="Logical SSDB table/collection (reserved for multi-corpus support).",
    )
    top_k: int = Field(
        default=4,
        gt=0,
        le=50,
        description="Maximum number of documents to return.",
    )
    timeout_s: float = Field(
        default=30.0,
        gt=0,
        description="Per-request HTTP timeout, in seconds.",
    )
    output_fields: Optional[list[str]] = Field(
        default=None,
        description="Subset of result fields to expose (title, source, content, score). None = all.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional tool description used when the retriever is exposed to an agent.",
    )
    license_token: Optional[str] = Field(
        default=None,
        description="Optional X-SSDB-License header. The server enforces; client only forwards.",
    )
