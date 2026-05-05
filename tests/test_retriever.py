"""Async retriever tests against a mocked SSDB bridge using ``respx``.

Asserts that the plug-in calls the canonical ``/api/v1/retrieve`` URL — the
contract published by ``ssdb/sql/services/rag``.

Skipped (with a clear "install respx" message) when ``respx`` isn't
installed, instead of erroring at collection time.
"""
from __future__ import annotations

import httpx
import pytest

# respx is in [dev] extras. Skip the file (not the whole session) if missing,
# so `pytest nat-retriever-ssdb/tests` reports a clean skip instead of a
# collection-time stack-trace.
respx = pytest.importorskip(
    "respx",
    reason="respx is required for retriever HTTP-mock tests; "
           "install with: pip install -e 'nemo_trunk/nat-retriever-ssdb[dev]'",
)

from nat_retriever_ssdb import SSDBRetriever  # noqa: E402  — after skip


BRIDGE = "http://ssdb-bridge:8000"
RETRIEVE_URL = f"{BRIDGE}/api/v1/retrieve"


@pytest.mark.asyncio
@respx.mock
async def test_search_happy_path() -> None:
    route = respx.post(RETRIEVE_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "results": [
                    {
                        "title": "telehealth FAQ",
                        "source": "health_synthetic_01_telehealth_faq.md",
                        "content": "Red flags include chest pain ...",
                        "score": 0.91,
                    },
                    {
                        "title": "chronic care",
                        "source": "health_synthetic_05_chronic_care_narrative.md",
                        "content": "Patients should report any ...",
                        "score": 0.83,
                    },
                ],
            },
        )
    )
    r = SSDBRetriever(uri=BRIDGE, top_k=2)
    out = await r.search("red flags chronic-care patient")
    assert route.called
    sent = route.calls.last.request
    assert sent.headers["content-type"].startswith("application/json")
    assert b"\"top_k\":2" in sent.content
    assert b"\"collection\":\"default\"" in sent.content
    assert len(out.items) == 2
    assert out.items[0].metadata["title"] == "telehealth FAQ"
    assert out.items[0].metadata["score"] == pytest.approx(0.91)


@pytest.mark.asyncio
@respx.mock
async def test_top_k_override_and_collection() -> None:
    respx.post(RETRIEVE_URL).mock(
        return_value=httpx.Response(200, json={"ok": True, "results": []})
    )
    r = SSDBRetriever(uri=BRIDGE, collection_name="phi", top_k=4)
    out = await r.search("Q", top_k=8)
    assert len(out.items) == 0
    sent = respx.calls.last.request
    assert b"\"top_k\":8" in sent.content
    assert b"\"collection\":\"phi\"" in sent.content


@pytest.mark.asyncio
@respx.mock
async def test_license_token_header_forwarded() -> None:
    respx.post(RETRIEVE_URL).mock(
        return_value=httpx.Response(200, json={"ok": True, "results": []})
    )
    r = SSDBRetriever(uri=BRIDGE, license_token="lic-abc-123")
    await r.search("Q")
    headers = respx.calls.last.request.headers
    assert headers["x-ssdb-license"] == "lic-abc-123"


@pytest.mark.asyncio
@respx.mock
async def test_output_fields_filters_metadata() -> None:
    respx.post(RETRIEVE_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "results": [{
                    "title": "t", "source": "s", "content": "c", "score": 0.5,
                }],
            },
        )
    )
    r = SSDBRetriever(uri=BRIDGE, output_fields=["title"])
    out = await r.search("Q")
    md = out.items[0].metadata
    assert set(md.keys()) == {"title"}


@pytest.mark.asyncio
@respx.mock
async def test_bridge_error_raises_runtime() -> None:
    respx.post(RETRIEVE_URL).mock(
        return_value=httpx.Response(200, json={"ok": False, "error": "boom"})
    )
    r = SSDBRetriever(uri=BRIDGE)
    with pytest.raises(RuntimeError) as exc:
        await r.search("Q")
    assert "boom" in str(exc.value)


@pytest.mark.asyncio
@respx.mock
async def test_http_5xx_raises_status_error() -> None:
    respx.post(RETRIEVE_URL).mock(
        return_value=httpx.Response(503, text="upstream down")
    )
    r = SSDBRetriever(uri=BRIDGE)
    with pytest.raises(httpx.HTTPStatusError):
        await r.search("Q")


@pytest.mark.asyncio
@respx.mock
async def test_caller_supplied_vector_passthrough() -> None:
    """A caller that already embedded the query (e.g. a reranker) can bypass
    the service-side embedder by passing ``vector=`` to ``search``."""
    route = respx.post(RETRIEVE_URL).mock(
        return_value=httpx.Response(200, json={"ok": True, "results": []})
    )
    r = SSDBRetriever(uri=BRIDGE)
    await r.search("Q", vector=[1, 2, 3])
    assert route.called
    body = route.calls.last.request.content
    assert b"\"vector\":[1,2,3]" in body
