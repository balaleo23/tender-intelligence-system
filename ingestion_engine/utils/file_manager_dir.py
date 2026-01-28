from pathlib import Path
from datetime import datetime
from typing import Dict

BASE_DATA_DIR = Path("data/tenders")


class TenderStorageManager:
    """
    Manages creation and retrieval of tender storage directories.
    """

    def __init__(self, base_dir: Path = BASE_DATA_DIR):
        self.base_dir = base_dir
        self._store: Dict[str, Dict[str, Path]] = {}

    def _build_base_dir(self, tender_uid: str, published_date: datetime) -> Path:
        year = str(published_date.year)
        month = f"{published_date.month:02d}"
        return self.base_dir / year / month / tender_uid

    def create_storage(
        self, tender_uid: str, published_date: datetime
    ) -> Path:
        """
        Backward-compatible method.
        - Creates directories
        - Stores them in internal dict
        - RETURNS raw path (existing behavior)
        """
        base = self._build_base_dir(tender_uid, published_date)

        dirs = {
            "base": base,
            "raw": base / "raw",
            "extracted": base / "extracted",
            "processed": base / "processed",
        }

        for path in dirs.values():
            path.mkdir(parents=True, exist_ok=True)

        # cache internally
        self._store[tender_uid] = dirs

        # ⚠️ IMPORTANT: return raw path to keep flow unchanged
        return dirs["raw"]

    def get_dirs(self, tender_uid: str) -> Dict[str, Path]:
        """
        Retrieve dirs using tender_uid only.
        """
        if tender_uid in self._store:
            return self._store[tender_uid]

        # Fallback: discover from filesystem
        matches = list(self.base_dir.glob(f"*/*/{tender_uid}"))

        if not matches:
            return None
            raise FileNotFoundError(
                f"No storage directory found for tender UID: {tender_uid}"
            )

        base = max(matches, key=lambda p: p.stat().st_mtime)

        dirs = {
            "base": base,
            "raw": base / "raw",
            "extracted": base / "extracted",
            "processed": base / "processed",
        }

        self._store[tender_uid] = dirs
        return dirs

    def get_dir(self, tender_uid: str, key: str) -> Path:
        """
        Retrieve a specific directory (raw / extracted / processed).
        """
        dirs = self.get_dirs(tender_uid)

        if key not in dirs:
            raise KeyError(
                f"Invalid key '{key}'. Available keys: {list(dirs.keys())}"
            )

        return dirs[key]


storage_manager = TenderStorageManager()



# from pathlib import Path
# from datetime import datetime
# from ingestion_engine.services import document_service

# BASE_DATA_DIR = Path("data/tenders")

# def tender_get_storage_dir(tender_uid : str, published_date : datetime) -> Path :
#                 """
#                 Backward-compatible helper used by scraper.
                
#                 Returns RAW directory path:
#                 data/tenders/<year>/<month>/<tender_uid>/raw
#                 """
#                 year = str(published_date.year)
#                 month = f"{published_date.month:02d}"

#                 base = BASE_DATA_DIR / year / month / tender_uid

#                 raw_dir = base / "raw"
#                 extracted_dir = base / "extracted"
#                 processed_dir = base / "processed"

#                 for p in (raw_dir, extracted_dir, processed_dir):
#                     p.mkdir(parents=True, exist_ok=True)
                
#                 return raw_dir

#                 # """
#                 # Returns directory path for storing tender documents

#                 # """

#                 # year = published_date.year
#                 # month = f"{published_date.month:02d}"

#                 # path = Base_Data_Dir /str(year) / month / tender_uid
#                 # path.mkdir(parents=True, exist_ok=True)
                
#                 # return path


# # def find_tender_dirs(tender_uid: str) -> dict:
# #     """
# #     Finds existing tender directories without requiring date info.
# #     """
# #     matches = list(BASE_DATA_DIR.glob(f"*/ */{tender_uid}".replace(" ", "")))

# #     if not matches:
# #         raise FileNotFoundError(f"Tender directory not found for UID: {tender_uid}")

# #     if len(matches) > 1:
# #         raise RuntimeError(
# #             f"Multiple directories found for tender UID {tender_uid}: {matches}"
# #         )

# #     base = matches[0]

# #     dirs = {
# #         "base": base,
# #         "raw": base / "raw",
# #         "extracted": base / "extracted",
# #         "processed": base / "processed",
# #     }

# #     return dirs

# # def get_tender_dirs(tender_uid: str) -> dict:
#     """
#     Creates and returns standard directories for a tender.
#     """
#     base = BASE_DATA_DIR / tender_uid

#     dirs = {
#         "base": base,
#         "raw": base / "raw",
#         "extracted": base / "extracted",
#         "processed": base / "processed",
#     }

#     # for path in dirs.values():
#     #     path.mkdir(parents=True, exist_ok=True)

#     return dirs