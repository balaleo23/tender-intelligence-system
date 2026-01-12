import json
from datetime import datetime
import logging
from playwright.sync_api import sync_playwright, Page, Locator
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
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
        self.context = self.browser.new_context()
        self.page = self.context.new_page() 

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

           if tender_table is None or page_number == 3: # sample for ten pages for demo
               break
               
           page.wait_for_timeout(2000)
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
                # tender link open
                cell_value = cells.nth(col_index).inner_text().strip()
                row_data[headers[col_index]] = cell_value
                
                if col_index == 4:
                    # page.get_by_text(cell_value)
                    title_text = cells.nth(4).inner_text().strip()
                    # clean_text = title_text.split("]")[0].replace("[", "").strip()

                    # page.get_by_text(clean_text).click()
                    # # page.get_by_role("link", name=clean_text, exact=True).click()
                    # page.wait_for_load_state("domcontentloaded")

                    title_cell = cells.nth(4)
                    tender_href = title_cell.locator("a").get_attribute("href")

                    # print(f"tender_href : {tender_href}")
                    # print(f"page_Url : {self.page.url}")

                    full_url = urljoin(self.page.url, tender_href)
                    print(full_url)

                    new_page = self.page.context.new_page()
                    new_page.goto(full_url, wait_until="domcontentloaded")

                    download_link_cnt = new_page.locator('//*[@id="DirectLink_8"]')
                    # download_link_cnt.click()
                    

                    print(download_link_cnt)
                    # need to handle the captch logic and saving logic for the same

                    # print("Tender URL:", tender_href)
                    # page.goto(tender_href, wait_until="domcontentloaded")
                    # page.wait_for_timeout(2000)
                    #scraping_logic here

                    # page.go_back(wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)
                    
            
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