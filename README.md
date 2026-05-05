# nat-retriever-ssdb

**SecretSkyDB (SSDB) retriever for the NVIDIA NeMo Agent Toolkit.**

A drop-in `_type: ssdb_retriever` for any toolkit-driven workflow,
including the
[NVIDIA RAG Blueprint](https://github.com/NVIDIA-AI-Blueprints/rag).
The plug-in is a thin async `httpx` client over the SSDB bridge's
`/api/v1/retrieve` endpoint. Embedding, secret-sharing, and shareholder
routing all live behind the bridge's trust boundary — vectors never
cross the wire in plaintext.

---

## Install

```bash
# Plug-in only (just the async client over /api/v1/retrieve):
pip install nat-retriever-ssdb

# With the NeMo Agent Toolkit so the registration entry-point fires on boot:
pip install "nat-retriever-ssdb[toolkit]"   # pulls nvidia-nat~=1.0
```

The toolkit discovers the plug-in via the standard `nat.plugins`
entry-point group declared in `pyproject.toml`
(see https://docs.nvidia.com/nemo/agent-toolkit/1.4/extend/plugins.html).

---

## Use from a workflow YAML

```yaml
retrievers:
  default_kb:
    _type: ssdb_retriever
    uri: http://ssdb-sql-rag:8080
    collection_name: nv_rag_documents
    top_k: 8
    description: >
      Encrypted nearest-neighbor retrieval over the SecretSkyDB-protected
      corpus. Vectors are post-quantum secret-shared across three
      independent Postgres + ssdbpgvector shareholders.

functions:
  search_kb:
    _type: nat.tool.retriever
    retriever: default_kb
    description: Search the secure corpus.

llms:
  my_llm:
    _type: nim
    model_name: nvidia/llama-3.3-nemotron-super-49b-v1.5

workflow:
  _type: react_agent
  llm: my_llm
  tool_names: [search_kb]
```

Run via the toolkit CLI:

```bash
nat run --config_file=workflow.yml --input "Telehealth FAQ?"
```

The agent picks `search_kb` via its description; nothing else in the
workflow has to change to swap Milvus for SSDB.

---

## Use directly (demo / CI / smoke test — no toolkit required)

```python
import asyncio
from nat_retriever_ssdb import SSDBRetriever

async def main():
    r = SSDBRetriever(uri="http://localhost:8080", top_k=4)
    out = await r.search("What red flags should a chronic-care patient report?")
    for item in out.items:
        print(item.metadata.get("title"), "->", item.content[:80])

asyncio.run(main())
```

For an even tighter "I want the embedding to come from elsewhere" path,
pass `vector=` to `search()` and the plug-in will skip server-side
embedding entirely.

---

## SSDB service contract

```http
POST /api/v1/retrieve
{ "query": "...", "k": 4, "collection": "default" }

200 OK
{ "ok": true,
  "results": [
    { "content": "...", "title": "...", "source": "...", "score": 0.0 }
  ]
}
```

(`/api/retrieve` is also accepted as a legacy alias.)

The plug-in honours the `output_fields` config to whitelist returned
metadata keys, and forwards an optional `X-SSDB-License` header that the
service can enforce.

---

## Versioning

* SemVer. Latest: **0.2.1**.
* Runtime deps: `httpx>=0.27`, `pydantic>=2`.
* Toolkit support tracked under the `[toolkit]` extra (`nvidia-nat~=1.0`).
* Test deps under `[dev]`: `pytest`, `pytest-asyncio`, `respx`.

---

## Repository & license

* Source: developed in the SSDB private mono-repo today as
  `nemo_trunk/nat-retriever-ssdb/`. Will be split into the public
  Apache-2.0 repo `SecretSkyDB/nat-retriever-ssdb` at the design-partner
  kickoff.
* PyPI: <https://pypi.org/project/nat-retriever-ssdb/> *(name reservation
  / placeholder today; functional v0.1.0 ships at kickoff)*.
* License: Apache-2.0

The proprietary SSDB server components (proxy + shareholders + service)
remain dual-licensed; this client is useless without them — same split
as Milvus/Zilliz, Pinecone, Weaviate, etc.

---

## Verified upstream pinning (May 2026)

* NeMo Agent Toolkit (`nat` CLI, `nvidia-nat` package): 1.6
* RAG Blueprint compatibility: tested against v2.5.0
  (`https://github.com/NVIDIA-AI-Blueprints/rag`)
* Plug-in entry-point group: `nat.plugins`
  (`https://docs.nvidia.com/nemo/agent-toolkit/1.4/extend/plugins.html`)
