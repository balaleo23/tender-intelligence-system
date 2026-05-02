from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ingestion_engine.constants import BASE_DATA_DIR, DIR_RAW, DIR_EXTRACTED, DIR_PROCESSED


class TenderStorageManager:

    def __init__(self, base_dir: Path = BASE_DATA_DIR):
        self.base_dir = base_dir
        self._store: Dict[str, Dict[str, Path]] = {}

    def _build_base_dir(self, tender_uid: str, published_date: datetime) -> Path:
        year = str(published_date.year)
        month = f"{published_date.month:02d}"
        return self.base_dir / year / month / tender_uid

    def create_storage(self, tender_uid: str, published_date: datetime) -> Path:
        base = self._build_base_dir(tender_uid, published_date)

        dirs = {
            "base": base,
            DIR_RAW: base / DIR_RAW,
            DIR_EXTRACTED: base / DIR_EXTRACTED,
            DIR_PROCESSED: base / DIR_PROCESSED,
        }

        for path in dirs.values():
            path.mkdir(parents=True, exist_ok=True)

        self._store[tender_uid] = dirs
        return dirs[DIR_RAW]

    def get_dirs(self, tender_uid: str) -> Optional[Dict[str, Path]]:
        if tender_uid in self._store:
            return self._store[tender_uid]

        matches = list(self.base_dir.glob(f"*/*/{tender_uid}"))

        if not matches:
            return None

        base = max(matches, key=lambda p: p.stat().st_mtime)

        dirs = {
            "base": base,
            DIR_RAW: base / DIR_RAW,
            DIR_EXTRACTED: base / DIR_EXTRACTED,
            DIR_PROCESSED: base / DIR_PROCESSED,
        }

        self._store[tender_uid] = dirs
        return dirs

    def get_dir(self, tender_uid: str, key: str) -> Path:
        dirs = self.get_dirs(tender_uid)

        if key not in dirs:
            raise KeyError(f"Invalid key '{key}'. Available: {list(dirs.keys())}")

        return dirs[key]


storage_manager = TenderStorageManager()
