from pathlib import Path
import httpx
from tirag.config import get_settings
import gzip, json
from tirag.schema import Document

"""Collected from this page section: https://nvd.nist.gov/vuln/data-feeds#divJson20Feeds"""
FEED_URL = "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-{year}.json.gz"

def download_year(year: int, force_add: bool = False) -> Path:
    """Download one CVE year's feed into raw/nvd/. Skips if already present."""
    out_dir = Path(get_settings().data_dir) / "raw" / "nvd"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"nvdcve-2.0-{year}.json.gz"

    if out_path.exists() and not force_add:
        print(f"skipping {year}: already downloaded")
        return out_path

    tmp_path = out_path.with_suffix(".part")
    with httpx.stream("GET", FEED_URL.format(year=year), timeout=120, follow_redirects=True) as r:
        r.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)

    tmp_path.rename(out_path)
    print(f"done {year}: {out_path.stat().st_size / 1e6:.1f} MB")
    return out_path



CVSS_ORDER = ["cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]


def _pick_cvss(metrics: dict) -> tuple[float | None, str | None]:
    for key in CVSS_ORDER:
        entries = metrics.get(key, [])
        if not entries:
            continue
        best = next((e for e in entries if e.get("type") == "Primary"), entries[0])
        data = best["cvssData"]
        return data.get("baseScore"), data.get("baseSeverity") or best.get("baseSeverity")
    return None, None


def parse_cve(item: dict) -> Document | None:
    cve = item["cve"]
    if cve.get("vulnStatus") == "Rejected": return None

    desc = next((d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"), "")
    score, severity = _pick_cvss(cve.get("metrics", {}))

    cwes = sorted({d["value"] for w in cve.get("weaknesses", [])
                   for d in w.get("description", []) if d["value"].startswith("CWE-")})
    cpe_matches = [m for cfg in cve.get("configurations", [])
                   for node in cfg.get("nodes", []) for m in node.get("cpeMatch", [])]

    return Document(
        id=cve["id"], source="nvd", title=cve["id"], text=desc,
        metadata={"cvss_score": score, "severity": severity, "cwe_ids": cwes,
                  "published": cve.get("published"), "last_modified": cve.get("lastModified"),
                  "vuln_status": cve.get("vulnStatus")},
        structured={"cpe_matches": cpe_matches,
                    "references": [r["url"] for r in cve.get("references", [])]},
    )


def build_processed() -> dict:
    s = get_settings()
    out_path = Path(s.data_dir) / "processed" / "nvd.jsonl"  #jsonl: A json file where each line is an independent JSON object 
    tmp_path = out_path.with_suffix(".part")
    stats = {"written": 0, "rejected": 0, "no_score": 0}
    current_year = s.nvd_data_years[0]

    with open(tmp_path, "w") as out:
        for year in range(s.nvd_data_years[0],s.nvd_data_years[1]+1):
            raw = Path(s.data_dir) / "raw" / "nvd" / f"nvdcve-2.0-{year}.json.gz"
            with gzip.open(raw, "rt") as f:
                for item in json.load(f)["vulnerabilities"]:
                    doc = parse_cve(item)
                    if doc is None:
                        stats["rejected"] += 1
                        continue
                    stats["no_score"] += doc.metadata["cvss_score"] is None
                    out.write(doc.model_dump_json() + "\n")
                    stats["written"] += 1
            current_year = current_year + 1

    tmp_path.replace(out_path)
    return stats
