from pathlib import Path
import httpx

from tirag.config import get_settings

FEED_URL = "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-{year}.json.gz"


def download_year(year: int, force: bool = False) -> Path:
    """Download one CVE year's feed into raw/nvd/. Skips if already present."""
    out_dir = Path(get_settings().data_dir) / "raw" / "nvd"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"nvdcve-2.0-{year}.json.gz"

    if out_path.exists() and not force:
        print(f"skip {year}: already downloaded")
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
