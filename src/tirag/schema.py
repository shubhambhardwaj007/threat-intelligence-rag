from pydantic import BaseModel, Field

class Document(BaseModel):
    id: str                                   # "CVE-2025-1234", "T1059", ...
    source: str                               # "nvd" | "attack" | "report"
    title: str
    text: str                                 # what gets embedded
    metadata: dict = Field(default_factory=dict)    # filterable: severity, dates, CWE
    structured: dict = Field(default_factory=dict)  # machine data, never embedded

class Chunk(BaseModel):
    chunk_id: str          # "CVE-2024-20683#0" — stable, so re-indexing overwrites instead of duplicating
    doc_id: str
    source: str
    text: str              # clean text, for display and citations
    embed_text: str        # header + text, what gets embedded
    metadata: dict = Field(default_factory=dict)