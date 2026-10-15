import json
from pathlib import Path
import numpy as np
from tirag.config import get_settings


def _load_chunks() -> tuple[list[str], list[str]]:
    path = Path(get_settings().data_dir) / "processed" / "chunks.jsonl"
    ids, texts = [], []
    with open(path) as f:
        for line in f:
            c = json.loads(line)
            ids.append(c["chunk_id"])
            texts.append(c["embed_text"])
    return ids, texts


def embeddings_dir(model_name: str) -> Path:
    d = Path(get_settings().data_dir) / "embeddings" / model_name.replace("/", "__")
    d.mkdir(parents=True, exist_ok=True)
    return d


def embed_all(emb, shard_size: int = 10000) -> None:
    ids, texts = _load_chunks()
    out_dir = embeddings_dir(emb.name)
    shard_count = 0

    for start in range(0, len(ids), shard_size):
        shard_ids = ids[start:start + shard_size]
        shard = out_dir / f"shard_{shard_count}.npz"

        if shard.exists() and np.load(shard)["ids"].tolist() == shard_ids:
            print(f"skip shard {n}")
            continue

        vecs = emb.embed_documents(texts[start:start + shard_size])
        tmp = out_dir / f"shard_{shard_count}.part.npz"
        np.savez(tmp, ids=np.array(shard_ids), vecs=vecs.astype(np.float16))
        tmp.replace(shard)
        print(f"saved shard {shard_count}: {len(shard_ids)} chunks")
        shard_count = shard_count+1