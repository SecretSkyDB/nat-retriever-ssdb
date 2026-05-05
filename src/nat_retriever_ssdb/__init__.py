"""nat-retriever-ssdb — SecretSkyDB retriever provider for the NVIDIA NeMo Agent Toolkit.

Public surface:

* ``SSDBRetrieverConfig`` — Pydantic config bound to the YAML key
  ``ssdb_retriever`` when registered with the toolkit.
* ``SSDBRetriever`` — async ``httpx`` client over the SSDB bridge's
  ``/api/v1/retrieve`` endpoint. Usable standalone (no toolkit install
  required) for demos, smoke tests, and direct embedding in other Python
  services.

Importing the toolkit registration module is gated behind ``nvidia-nat`` being
installed (extras ``[toolkit]``); ``register.py`` is auto-loaded by the toolkit
through the ``nat.plugins`` entry-point declared in ``pyproject.toml``.
"""
from ._version import __version__
from .config import SSDBRetrieverConfig
from .retriever import RetrievedItem, RetrieverOutput, SSDBRetriever

__all__ = [
    "__version__",
    "SSDBRetrieverConfig",
    "SSDBRetriever",
    "RetrievedItem",
    "RetrieverOutput",
]
