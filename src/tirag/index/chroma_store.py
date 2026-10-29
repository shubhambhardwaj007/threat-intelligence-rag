import chromadb
import numpy as np

BATCH = 4000   # Chroma caps how many records one call accepts


class ChromaStore:
    def __init__(self, path: str, collection: str = "tirag"):
        self.client = chromadb.PersistentClient(path=path)
        self.col = self.client.get_or_create_collection(
            collection,
            configuration={"hnsw": {"space": "cosine", "ef_construction": 200,"ef_search": 200, "max_neighbors": 32}})

    def upsert(self, ids, vectors: np.ndarray, texts, metadatas) -> None:
        for i in range(0, len(ids), BATCH):
            self.col.upsert(ids=ids[i:i + BATCH],
                            embeddings=vectors[i:i + BATCH].astype(np.float32).tolist(),
                            documents=texts[i:i + BATCH],
                            metadatas=metadatas[i:i + BATCH])

    def search(self, query_vector: np.ndarray, k: int = 10, where: dict | None = None) -> list[dict]:
        r = self.col.query(query_embeddings=[query_vector.tolist()], n_results=k, where=where)
        return [{"chunk_id": cid, "text": doc, "metadata": md, "score": 1 - dist}
                for cid, doc, md, dist in zip(r["ids"][0], r["documents"][0],
                                              r["metadatas"][0], r["distances"][0])]

    def count(self) -> int:
        return self.col.count()