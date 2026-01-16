import json
from datetime import datetime
import logging
from playwright.sync_api import sync_playwright, Page, Locator
import captcha_solver
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from PIL import Image
from pathlib import Path
import io
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
          
            for col_index in range(min(cells_count,len(headers))):
                # tender link open
                cell_value = cells.nth(col_index).inner_text().strip()
                row_data[headers[col_index]] = cell_value
                
                if col_index == 4:
                   
                    title_text = cells.nth(4).inner_text().strip()
                    # clean_text = title_text.split("]")[0].replace("[", "").strip()
                    clean_text_new = title_text.split("[")[-1].replace("]", "").strip()



                    title_cell = cells.nth(4)
                    tender_href = title_cell.locator("a").get_attribute("href")

 

                    full_url = urljoin(self.page.url, tender_href)
                    print(full_url)

                    new_page = self.page.context.new_page()
                    new_page.goto(full_url, wait_until="domcontentloaded")

                    locators = {
                       'DirectLink_8': '//*[@id="DirectLink_8"]',
                     'DirectLink_7'  : '//*[@id="DirectLink_7"]'
                    }

                    download_link_cnt = None
                    selected = None
                    captchsolved= False

                    for key,  xpath in locators.items():
                        locator = new_page.locator(xpath)
                        if locator.count() > 0:
                            download_link_cnt = locator
                            selected = key
                            break



                    print("download Link", download_link_cnt)
                    download_href = download_link_cnt.get_attribute('href')
                    if download_href:
                        print(f"Link href: {download_href}")
                        full_url_download = urljoin(self.page.url, download_href)
                        print(f"Full Url download{full_url_download}")
                        if selected == 'DirectLink_8':
                            download_page = self.page.context.new_page()
                            download_page.goto(full_url_download, wait_until="domcontentloaded")
                            download_page.wait_for_selector('//*[@id="captchaImage"]', state= "hidden" ,timeout=30000)
                            download_page.wait_for_timeout(30000)
                            
                            download_link_cnt.click()
                            download_page.close()

                        if selected == 'DirectLink_7':
                                # download_page.wait_for_timeout(3500)
                                with new_page.expect_download() as download_info:
                                    download_link_cnt.click()
                                download = download_info.value
                                download_dir = Path("downloads")
                                download_dir.mkdir(parents=True, exist_ok=True)
                                temp_path = download.path()
                                print(temp_path)
                                custom_name = f"{clean_text_new}_{download.suggested_filename}"
                                download.save_as(download_dir/custom_name)

                    page.wait_for_timeout(2000)
                    new_page.close()
                    
            
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