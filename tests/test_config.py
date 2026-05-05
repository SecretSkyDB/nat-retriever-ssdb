"""Validation behavior for ``SSDBRetrieverConfig`` (Pydantic v2)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from nat_retriever_ssdb import SSDBRetrieverConfig


def test_minimal_config_defaults() -> None:
    cfg = SSDBRetrieverConfig(uri="http://localhost:8000")
    assert str(cfg.uri).startswith("http://localhost:8000")
    assert cfg.collection_name == "default"
    assert cfg.top_k == 4
    assert cfg.timeout_s == 30.0
    assert cfg.output_fields is None
    assert cfg.license_token is None


def test_top_k_bounds() -> None:
    with pytest.raises(ValidationError):
        SSDBRetrieverConfig(uri="http://x", top_k=0)
    with pytest.raises(ValidationError):
        SSDBRetrieverConfig(uri="http://x", top_k=51)
    SSDBRetrieverConfig(uri="http://x", top_k=50)


def test_timeout_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        SSDBRetrieverConfig(uri="http://x", timeout_s=0)


def test_uri_must_be_http_url() -> None:
    with pytest.raises(ValidationError):
        SSDBRetrieverConfig(uri="not a url")


def test_extra_fields_allowed_for_forward_compat() -> None:
    # ``extra='allow'`` from the compat base — keeps YAML schemas non-fragile
    # against future bridge fields.
    cfg = SSDBRetrieverConfig(uri="http://x", extra_unknown="ignored")
    assert getattr(cfg, "extra_unknown") == "ignored"
