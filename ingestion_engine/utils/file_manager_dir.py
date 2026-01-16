from pathlib import Path
from datetime import datetime

Base_Data_Dir = Path("data/tenders")


def tender_get_storage_dir(tender_uid : str, published_date : datetime) -> Path :
                """
                Returns directory path for storing tender documents

                """

                year = published_date.year
                month = f"{published_date.month:02d}"

                path = Base_Data_Dir /str(year) / month / tender_uid
                path.mkdir(parents=True, exist_ok=True)

                return path
