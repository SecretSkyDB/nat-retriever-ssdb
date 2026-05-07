"""Async ``httpx`` client over the SSDB bridge's ``/api/v1/retrieve`` endpoint.

The client deliberately knows nothing about embedding, secret sharing, or
share-holder topology: those live behind the bridge's trust boundary. It
implements only:

* HTTP POST to ``{uri}/api/v1/retrieve`` with ``{query, top_k, collection}``;
* Optional ``X-SSDB-License`` header forwarding;
* Mapping the ``ok=true`` response to ``RetrieverOutput`` / ``RetrievedItem``.

Versioning: the canonical contract path is ``/api/v1/retrieve``. The legacy
``/api/retrieve`` (no version segment) is still served by both the new
``ssdb-sql-rag`` service and the old ``ssdb_nemoclaw`` bridge as an alias,
so older deployments keep working while you migrate.

Re-exports ``RetrievedItem`` and ``RetrieverOutput`` so callers that don't have
the NeMo Agent Toolkit installed still get well-typed return values.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx

from ._compat import RetrievedItem, RetrieverOutput

try:  # pragma: no cover - the real ABC only matters when the toolkit is around
    from nat.retriever.interface import Retriever as _ToolkitRetriever  # type: ignore
except Exception:
    class _ToolkitRetriever:  # minimal stand-in so subclassing works either way
        """Local stub of ``nat.retriever.interface.Retriever``."""

        async def search(self, query: str, **kwargs: Any) -> "RetrieverOutput":  # noqa: D401
            raise NotImplementedError


class SSDBRetriever(_ToolkitRetriever):
    """Pure async HTTP client. Constructed by ``ssdb_retriever_client`` at
    runtime, but also instantiable directly for demos and tests.
    """

    def __init__(
        self,
        uri: str,
        collection_name: str = "default",
        top_k: int = 4,
        timeout_s: float = 30.0,
        output_fields: Optional[list[str]] = None,
        description: Optional[str] = None,
        license_token: Optional[str] = None,
        **_: Any,
    ) -> None:
        self._base = str(uri).rstrip("/")
        self._collection = collection_name
        self._top_k = top_k
        self._timeout_s = timeout_s
        self._output_fields = output_fields
        self._description = description or (
            "SecretSkyDB encrypted-nearest-neighbor retriever "
            "(post-quantum secret-shared vector store on Postgres + ssdbpgvector)."
        )
        self._headers: dict[str, str] = {}
        if license_token:
            self._headers["X-SSDB-License"] = license_token

    @property
    def description(self) -> str:
        return self._description

    async def search(self, query: str, **kwargs: Any) -> RetrieverOutput:
        top_k = int(kwargs.get("top_k") or self._top_k)
        payload: dict[str, Any] = {
            "query": query,
            "top_k": top_k,
            "collection": self._collection,
        }
        # Power users (e.g. a downstream reranker that has already embedded
        # the query) can pass ``vector`` to bypass the service's embedder.
        if kwargs.get("vector") is not None:
            payload["vector"] = list(kwargs["vector"])
        async with httpx.AsyncClient(timeout=self._timeout_s) as cx:
            resp = await cx.post(
                f"{self._base}/api/v1/retrieve",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"SSDB bridge error: {data.get('error', 'unknown')}")

        # `nvidia-nat==1.6` renamed `RetrievedItem.content` to `Document.page_content`
        # to match the langchain Document convention, AND renamed
        # `RetrieverOutput.items` to `RetrieverOutput.results`. Detect both at
        # runtime so we work against both the legacy schema and the 1.6+ schema.
        _content_field = "page_content" if "page_content" in RetrievedItem.model_fields else "content"
        _items_field = "results" if "results" in RetrieverOutput.model_fields else "items"

        items: list[RetrievedItem] = []
        for h in data.get("results", []):
            metadata = {
                "title":  h.get("title", ""),
                "source": h.get("source", ""),
                "score":  float(h.get("score", 0.0)),
            }
            if self._output_fields is not None:
                metadata = {k: v for k, v in metadata.items() if k in self._output_fields}
            items.append(RetrievedItem(**{_content_field: h.get("content", ""), "metadata": metadata}))
        return RetrieverOutput(**{_items_field: items})


__all__ = ["SSDBRetriever", "RetrievedItem", "RetrieverOutput"]
