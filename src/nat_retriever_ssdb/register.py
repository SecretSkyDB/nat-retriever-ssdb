"""NVIDIA NeMo Agent Toolkit registration entry point.

Auto-loaded by the toolkit on boot via the ``nat.plugins`` entry-point group
declared in ``pyproject.toml``. The actual decorator imports happen lazily so
``import nat_retriever_ssdb`` and unit tests don't require the toolkit.
"""
from __future__ import annotations


def _register() -> None:
    """Bind config + client to the toolkit's component registry.

    Kept as a function (not module-level decorators) so that importing this
    module without the toolkit installed is a quick no-op rather than an
    ImportError.
    """
    try:
        from nat.builder.builder import Builder  # type: ignore
        from nat.cli.register_workflow import (  # type: ignore
            register_retriever_client,
            register_retriever_provider,
        )
        from nat.data_models.retriever import RetrieverProviderInfo  # type: ignore
    except Exception:  # toolkit not installed — nothing to register
        return

    from .config import SSDBRetrieverConfig

    @register_retriever_provider(config_type=SSDBRetrieverConfig)
    async def ssdb_retriever_provider(  # noqa: D401
        retriever_config: SSDBRetrieverConfig, builder: Builder
    ):
        yield RetrieverProviderInfo(
            config=retriever_config,
            description=(
                retriever_config.description
                or "SecretSkyDB retriever: encrypted nearest-neighbor over "
                   "secret-shared, post-quantum-protected vector shards stored in "
                   "Postgres + ssdbpgvector shareholders."
            ),
        )

    @register_retriever_client(config_type=SSDBRetrieverConfig, wrapper_type=None)
    async def ssdb_retriever_client(config: SSDBRetrieverConfig, builder: Builder):
        from .retriever import SSDBRetriever
        yield SSDBRetriever(**config.model_dump())


# Best-effort eager registration so that simply importing this module from the
# toolkit's plugin loader is enough.
_register()
