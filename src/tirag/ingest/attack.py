from pathlib import Path
from tirag.config import get_settings
from tirag.ingest.http import download_file
import json, re
from tirag.schema import Document

BASE_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/refs/heads/master"

def download_attack(force: bool = False) -> list[Path]:
    paths = []
    for attack_type,version in get_settings().attack_versions.items():
        out = Path(get_settings().data_dir) / "raw" / "attack" / f"{attack_type}-{version}.json"
        paths.append(download_file(f"{BASE_URL}/{attack_type}/{attack_type}-{version}.json", out, force))
    return paths



KEEP = {"attack-pattern": "technique", "intrusion-set": "group",
        "course-of-action": "mitigation", "malware": "software", "tool": "software",
        "campaign": "campaign"}


def _clean(text: str) -> str:
    text = re.sub(r"\(Citation: [^)]*\)", "", text)            # drop "(Citation: X)"
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)        # markdown link -> its text
    return re.sub(r"\s+", " ", text).strip()


def parse_object(obj: dict, domain: str) -> Document | None:
    kind = KEEP.get(obj.get("type"))
    if kind is None or obj.get("revoked") or obj.get("x_mitre_deprecated"):
        return None
    ref = next((r for r in obj.get("external_references", [])
                if r.get("source_name") == "mitre-attack"), None)
    if ref is None:
        return None

    name = obj["name"]
    return Document(
        id=ref["external_id"], source="attack",
        title=f'{ref["external_id"]}: {name}',
        text=f"{name}. {_clean(obj.get('description', ''))}",
        metadata={"domain": domain, "attack_type": kind,
                  "tactics": [p["phase_name"] for p in obj.get("kill_chain_phases", [])],
                  "platforms": obj.get("x_mitre_platforms", []),
                  "is_subtechnique": obj.get("x_mitre_is_subtechnique", False),
                  "url": ref.get("url")},
        structured={"stix_id": obj["id"]},
    )


def build_processed() -> dict:
    s = get_settings()
    out_path = Path(s.data_dir) / "processed" / "attack.jsonl"
    tmp_path = out_path.with_suffix(".part")
    stats = {"written": 0, "skipped": 0}

    with open(tmp_path, "w") as out:
        for domain in s.attack_index_domains:
            raw = Path(s.data_dir) / "raw" / "attack" / f"{domain}-{s.attack_versions[domain]}.json"
            objects = json.loads(raw.read_text())["objects"]
            for obj in objects:
                doc = parse_object(obj, domain)
                if doc is None:
                    stats["skipped"] += 1
                    continue
                out.write(doc.model_dump_json() + "\n")
                stats["written"] += 1

    tmp_path.replace(out_path)
    return stats