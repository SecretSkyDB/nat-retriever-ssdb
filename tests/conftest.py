"""Tests-only bootstrap.

Lets ``pytest nemo_trunk/nat-retriever-ssdb/tests`` work from a fresh
checkout without forcing ``pip install -e .`` first.

If ``nat_retriever_ssdb`` isn't already importable, we put the package's
``src/`` directory on ``sys.path``. This is a *tests-only* shim —
production code still has to install the package the normal way so
the ``nat.plugins`` entry-points wire up.

External test deps (``respx``, ``pytest-asyncio``) still need to be
installed; the individual test modules use ``pytest.importorskip`` so
collection produces a clear per-test skip instead of a stack-trace
when those are missing.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _ensure_package_importable() -> None:
    try:
        importlib.import_module("nat_retriever_ssdb")
        return
    except ImportError:
        pass
    pkg_src = Path(__file__).resolve().parents[1] / "src"
    if pkg_src.is_dir() and str(pkg_src) not in sys.path:
        sys.path.insert(0, str(pkg_src))


_ensure_package_importable()
