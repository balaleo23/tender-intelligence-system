import json
from datetime import datetime
import logging
from playwright.sync_api import sync_playwright, Page, Locator

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URL = "https://eprocure.gov.in/eprocure/app?page=FrontEndListTendersbyDate&service=page"

class Scrapper:

    def __init__(self):
        self.data = []
        self.p = None
        self.browser = None
        self.page = None

    
    def open_load_content(self) -> Page:
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(headless=False)
        self.page = self.browser.new_page()

        self.page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        self.page.wait_for_timeout(3000)
        self.page.get_by_text("Closing within 14 days").click()

        logger.info("Page loaded successfully")

        return self.page


    def extract_rows(self, page: Page):
        page_number = 1

        while True:
           logger.info(f" Scraping Page {page_number}")

           tender_table = page.locator('//*[@id="table"]')

           if tender_table is None or page_number == 10:
               break

           tender_content = tender_table.locator("tr")
           print("Rows Count:", tender_content.count())
           page.wait_for_timeout(2000)

           self.process_rows(tender_content)


           next_btn = page.locator("#linkFwd")

           if next_btn.is_disabled():
                logger.info("No more pages")
                break

           next_btn.click()
           page.wait_for_load_state("networkidle")

           page.wait_for_timeout(3000)

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
            # for col_index  in range(min(cells_count), len(headers)):
            #     row_data[headers[col_index]] = cells.nth(col_index).inner_text().strip()
            for col_index in range(min(cells_count,len(headers))):
                cell_value = cells.nth(col_index).inner_text().strip()
                row_data[headers[col_index]] = cell_value
            
            if row_data:
                self.data.append(row_data)

    def form_json(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Tender_data_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Data saved to {filename}")

    def close(self):
        if self.browser:
            self.browser.close()
        if self.p:
            self.p.stop()     


if __name__ == "__main__":
    logger.info("scrapper started")

    scrapper = Scrapper()
    page = scrapper.open_load_content() 
    scrapper.extract_rows(page)
    scrapper.form_json()
    scrapper.close()
           
            


        