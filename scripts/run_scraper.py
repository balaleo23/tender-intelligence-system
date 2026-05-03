"""
Manual scraper runner — run this locally, NOT inside Docker.

Why locally?
  eprocure.gov.in uses image captchas that require human input.
  This opens a real visible browser so you can type the captcha.
  After scraping, trigger /ingest via Streamlit or API to index the results.

Usage:
    python scripts/run_scraper.py

Output:
    meta_data/Tender_data_<timestamp>.json
    meta_data/Tenders_filepath_<timestamp>.json

Next step:
    Go to Streamlit → Ingest page → click "Run Ingestion"
    OR: curl -X POST http://localhost:8000/ingest
"""

import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion_engine.scraper.scraper_runner import Scrapper
from ingestion_engine.utils.logger import get_logger

logger = get_logger("scraper_runner")


def main():
    logger.info("=" * 60)
    logger.info("Tender scraper starting")
    logger.info("A browser window will open — solve captchas when prompted")
    logger.info("=" * 60)

    scrapper = Scrapper()

    try:
        page = scrapper.open_load_content()
        logger.info("Browser loaded — scraping tender listings...")

        scrapper.extract_rows(page)
        logger.info("Extracted %d tenders", len(scrapper.data))

        scrapper.form_json()
        logger.info("Saved to meta_data/ — ready to ingest")

        logger.info("=" * 60)
        logger.info("Scraping complete!")
        logger.info("Next step: trigger /ingest via Streamlit or API")
        logger.info("  Streamlit: http://localhost:8501 → Ingest page")
        logger.info("  API:       POST http://localhost:8000/ingest")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("Scraper interrupted by user")

    except Exception as e:
        logger.error("Scraper failed: %s", e)
        sys.exit(1)

    finally:
        scrapper.close()


if __name__ == "__main__":
    main()
