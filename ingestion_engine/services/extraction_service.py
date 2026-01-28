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
    
    
    # @staticmethod
    # def extract_zip(zip_path: str, extract_to: str) -> list[Path]:
        zip_path = Path(zip_path)
        extract_to = Path(extract_to)

        if not zip_path.exists() or not zip_path.is_file():
            raise ValueError(f"{zip_path} is not a valid ZIP file")

        extract_to.mkdir(parents=True, exist_ok=True)

        extracted_files = []

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                # Skip directories inside zip
                if member.endswith("/"):
                    continue

                zip_ref.extract(member, extract_to)
                extracted_files.append(extract_to / member)

        return extracted_files
