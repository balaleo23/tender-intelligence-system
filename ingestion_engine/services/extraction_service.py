from pathlib import Path
import zipfile


class ExtractionService:
    @staticmethod
    def extract_zip(zip_path: Path, extract_dir: Path) -> list[Path]:
        """
        Extracts zip into extract_dir and returns extracted file paths.
        """
        extracted_files = []

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith("/"):
                    continue

                zip_ref.extract(member, extract_dir)
                extracted_files.append(extract_dir / member)

        return extracted_files
