import json
from pathlib import Path
import numpy as np
from tirag.config import get_settings
from tirag.index.embed_store import embeddings_dir


def _flat(md: dict) -> dict:
    """Chroma metadata must be str/int/float/bool: lists become strings, None is dropped."""
    out = {}
    for k, v in md.items():
        if v is None:
            continue
        if isinstance(v, list):
            v = ",".join(map(str, v))
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
    return out


def build_index(store, model_name: str) -> int:
    path = Path(get_settings().data_dir) / "processed" / "chunks.jsonl"
    chunks = {}
    with open(path) as f:
        for line in f:
            c = json.loads(line)
            chunks[c["chunk_id"]] = c

    for shard in sorted(embeddings_dir(model_name).glob("shard_*.npz")):
        if ".part" in shard.name:
            continue
        data = np.load(shard)
        ids = data["ids"].tolist()
        store.upsert(ids, data["vecs"],
                     [chunks[i]["text"] for i in ids],
                     [_flat({**chunks[i]["metadata"], "doc_id": chunks[i]["doc_id"],
                             "source": chunks[i]["source"]}) for i in ids])
        print(f"{shard.name}: total {store.count()}")
    return store.count()