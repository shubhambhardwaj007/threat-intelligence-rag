from pathlib import Path
from tirag.config import get_settings
from tirag.ingest.http import download_file

BASE_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/refs/heads/master"

def download_attack(force: bool = False) -> List[Path]:
    paths = []
    for attack_type,version in get_settings().attack_versions.items():
        out = Path(get_settings().data_dir) / "raw" / "attack" / f"{attack_type}-{version}.json"
        paths.append(download_file(f"{BASE_URL}/{{attack_type}}/{attack_type}-{version}.json", out, force))
    return paths