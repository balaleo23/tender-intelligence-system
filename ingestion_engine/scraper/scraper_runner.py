import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, Page, Locator

from ingestion_engine.constants import (
    EPROCURE_URL,
    TENDER_FILTER_TEXT,
    MAX_SCRAPE_PAGES,
    TENDER_TABLE_XPATH,
    NEXT_PAGE_SELECTOR,
    TENDER_DATE_FORMAT,
    METADATA_DIR,
    NAV_TIMEOUT_MS,
    PAGE_LOAD_TIMEOUT_MS,
    BUTTON_WAIT_TIMEOUT_MS,
    ROW_WAIT_MS,
    PAGE_TURN_WAIT_MS,
)
from ingestion_engine.scraper.download_handler import download_content
from ingestion_engine.utils.logger import get_logger

logger = get_logger(__name__)


class Scrapper:

    def __init__(self):
        self.data = []
        self.download_data = []
        self.p = None
        self.browser = None
        self.page = None

    def open_load_content(self) -> Page:
        try:
            self.p = sync_playwright().start()
            self.browser = self.p.chromium.launch(headless=False)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.page.set_default_navigation_timeout(NAV_TIMEOUT_MS)

            response = self.page.goto(EPROCURE_URL, wait_until="load", timeout=PAGE_LOAD_TIMEOUT_MS)

            if not response or response.status >= 400:
                logger.error("Failed to load page: %s", response.status if response else "No Response")

            button = self.page.get_by_text(TENDER_FILTER_TEXT)
            button.wait_for(state="visible", timeout=BUTTON_WAIT_TIMEOUT_MS)
            button.click()

            self.page.wait_for_load_state("networkidle")
            logger.info("Page loaded and filtered successfully")
            return self.page

        except Exception as e:
            logger.error("Initialization failed: %s", e)
            self.cleanup()
            raise

    def cleanup(self):
        if hasattr(self, "browser"):
            self.browser.close()
        if hasattr(self, "p"):
            self.p.stop()

    def extract_rows(self, page: Page):
        page_number = 1

        while True:
            logger.info("Scraping page %d", page_number)

            tender_table = page.locator(TENDER_TABLE_XPATH)

            if tender_table is None or page_number == MAX_SCRAPE_PAGES:
                break

            page.wait_for_timeout(ROW_WAIT_MS)
            tender_content = tender_table.locator("tr")
            logger.debug("Rows count: %d", tender_content.count())
            page.wait_for_timeout(ROW_WAIT_MS)

            self.process_rows(tender_content)

            next_btn = page.locator(NEXT_PAGE_SELECTOR)

            if next_btn.is_disabled():
                logger.info("No more pages")
                break

            next_btn.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(PAGE_TURN_WAIT_MS)
            page_number += 1

    def process_rows(self, rows: Locator):
        headers = []
        if rows.count() == 0:
            return

        first_row = rows.nth(0)
        first_cells = first_row.locator("th, td")

        for i in range(first_cells.count()):
            headers.append(first_cells.nth(i).inner_text().strip())

        for row_index in range(1, rows.count() - 1):
            row = rows.nth(row_index)
            cells = row.locator("th, td")
            cells_count = cells.count()
            row_data = {}
            filedata = None

            for col_index in range(min(cells_count, len(headers))):
                cell_value = cells.nth(col_index).inner_text().strip()
                row_data[headers[col_index]] = cell_value

                if col_index == 1:
                    e_published_Date = cells.nth(col_index).inner_text().strip()
                    e_published_Date_converted = datetime.strptime(e_published_Date, TENDER_DATE_FORMAT)
                    logger.debug("Published date: %s", e_published_Date_converted)

                if col_index == 4:
                    filedata = download_content(cells, self.page, e_published_Date_converted)

            if row_data:
                self.data.append(row_data)

            if filedata and filedata not in self.download_data:
                logger.debug("New file data: %s", filedata)
                self.download_data.append(filedata)

    def form_json(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Tender_data_{timestamp}.json"
        filename_download = f"Tenders_filepath_{timestamp}.json"

        os.makedirs(METADATA_DIR, exist_ok=True)

        with open(os.path.join(METADATA_DIR, filename_download), "w", encoding="utf-8") as f:
            json.dump(self.download_data, f, indent=2, ensure_ascii=False)
        logger.info("Data saved to %s", filename_download)

        with open(os.path.join(METADATA_DIR, filename), "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        logger.info("Data saved to %s", filename)

    def close(self):
        if self.browser:
            self.browser.close()
        if self.p:
            self.p.stop()


if __name__ == "__main__":
    logger.info("Scraper started")
    scrapper = Scrapper()
    page = scrapper.open_load_content()
    scrapper.extract_rows(page)
    scrapper.form_json()
    scrapper.close()
