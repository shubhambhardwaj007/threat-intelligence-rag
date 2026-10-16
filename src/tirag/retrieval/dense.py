def dense_search(query: str, emb, store, k: int = 5, where: dict | None = None) -> list[dict]:
    return store.search(emb.embed_query(query), k=k, where=where)