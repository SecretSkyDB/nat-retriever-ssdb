"""Opt-in end-to-end test against a real SSDB bridge.

Skipped unless ``SSDB_BRIDGE_URL`` is exported. Used by the rag-blueprint-ssdb
demo / CI; not part of the default ``pytest`` run.
"""
from __future__ import annotations

import os

import pytest

from nat_retriever_ssdb import SSDBRetriever


pytestmark = pytest.mark.asyncio

SSDB_BRIDGE_URL = os.getenv("SSDB_BRIDGE_URL", "").strip()


@pytest.mark.skipif(not SSDB_BRIDGE_URL, reason="SSDB_BRIDGE_URL not set")
async def test_known_answer_query_against_real_bridge() -> None:
    r = SSDBRetriever(uri=SSDB_BRIDGE_URL, top_k=4)
    out = await r.search("red flags chronic care")
    assert out.items, "real bridge returned no results — corpus not ingested?"
