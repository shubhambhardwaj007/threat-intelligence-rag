from pathlib import Path
import httpx


def download_file(url: str, out_path: Path, force: bool = False) -> Path:
    """Stream url to out_path atomically. Skips if already present."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and not force:
        print(f"skip: {out_path.name} already downloaded")
        return out_path

    tmp_path = out_path.with_suffix(out_path.suffix + ".part")
    with httpx.stream("GET", url, timeout=120, follow_redirects=True) as r:
        r.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)

    tmp_path.replace(out_path)
    print(f"done: {out_path.name} ({out_path.stat().st_size / 1e6:.1f} MB)")
    return out_path