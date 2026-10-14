import json, re
from pathlib import Path
from tirag.config import get_settings
from tirag.schema import Document, Chunk


MAX_PRODUCTS = 5
def _products(doc: Document) -> list[str]:
    """'cpe:2.3:o:microsoft:windows_10:...' -> 'microsoft windows_10', unique, capped."""
    seen = []
    for m in doc.structured.get("cpe_matches", []):
        if not m.get("vulnerable"):
            continue
        parts = m["criteria"].split(":")
        name = f"{parts[3]} {parts[4]}"
        if name not in seen:
            seen.append(name)
    return seen[:MAX_PRODUCTS]

def header(doc: Document) -> str:
    md = doc.metadata

    if doc.source == "nvd":
        bits = [doc.id, ", ".join(md.get("cwe_ids", [])), f"CVSS {md['cvss_score']} {md['severity']}" if md.get("cvss_score") else "", ", ".join(_products(doc))]
    else:
        bits = [doc.title, md.get("attack_type", ""),
                "tactics: " + ", ".join(md.get("tactics", [])) if md.get("tactics") else "",
                "platforms: " + ", ".join(md.get("platforms", [])) if md.get("platforms") else ""]
    return " | ".join(b for b in bits if b)


def split_text(text: str, max_words: int) -> list[str]:
    """Whole if short; else pack sentences up to max_words, overlapping one sentence."""
    if len(text.split()) <= max_words:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], []
    for s in sentences:
        if current and len(" ".join(current + [s]).split()) > max_words:
            chunks.append(" ".join(current))
            current = current[-1:]          # overlap: carry the last sentence forward
        current.append(s)
    chunks.append(" ".join(current))
    return chunks

def chunk_document(doc: Document, max_words: int) -> list[Chunk]:
    h = header(doc)
    chunks = []
    for i, piece in enumerate(split_text(doc.text, max_words)):
        chunks.append(Chunk(chunk_id=f"{doc.id}#{i}", doc_id=doc.id, source=doc.source, text=piece, embed_text=f"{h}\n{piece}",
              metadata={**doc.metadata, "chunk_index": i}))
    return chunks

def build_chunks() -> dict:
    s = get_settings()
    proc = Path(s.data_dir) / "processed"
    out_path = proc / "chunks.jsonl"
    tmp_path = out_path.with_suffix(".part")
    stats = {"docs": 0, "chunks": 0, "split_docs": 0}

    with open(tmp_path, "w") as out:
        for name in ["nvd.jsonl", "attack.jsonl"]:
            with open(proc / name) as f:
                for line in f:
                    doc = Document.model_validate_json(line)
                    chunks = chunk_document(doc, s.chunk_max_words)
                    stats["docs"] += 1
                    stats["chunks"] += len(chunks)
                    stats["split_docs"] += len(chunks) > 1
                    for c in chunks:
                        out.write(c.model_dump_json() + "\n")
    tmp_path.replace(out_path)
    return stats