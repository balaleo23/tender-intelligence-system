import json
from datetime import datetime
import logging
from playwright.sync_api import sync_playwright, Page, Locator
from ingestion_engine.scraper import captcha_solver, captch_cnn_solver 
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from PIL import Image
from pathlib import Path
import time

import sys
import os

# # Add the parent directory (my_project) to Python path
# parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, parent_dir)

# from ingestion_engine.utils.file_manager_dir import TenderStorageManager
from ingestion_engine.scraper.eprocure_scraper import download_content
import io
# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URL = "https://eprocure.gov.in/eprocure/app?page=FrontEndListTendersbyDate&service=page"

class Scrapper:

    def __init__(self):
        self.data = []
        self.download_data = []
        self.p = None
        self.browser = None
        self.page = None
   
    def open_load_content(self) -> Page:
        """
        Help to initialise the playwright for scrapping

        """
        try:
            self.p = sync_playwright().start()
            self.browser = self.p.chromium.launch(headless=False)
            self.context = self.browser.new_context()
            # self.context = self.browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # viewport={'width': 1920, 'height': 1080}, accept_downloads=True)
            self.page = self.context.new_page() 
            self.page.set_default_navigation_timeout(90000)
            # 1. Navigate with retry logic
            response = self.page.goto(URL, wait_until="load", timeout=60000)

            if not response or response.status >= 400:
                logger.error(f"Failed to load page: {response.status if response else 'No Response'}")
                
            # 2. Instead of a hard sleep, wait for the button to be ready
            button = self.page.get_by_text("Closing within 14 days")
            button.wait_for(state="visible", timeout=10000)
            button.click()

            # 3. Wait for the table/results to actually load after the click
            self.page.wait_for_load_state("networkidle")

            logger.info("Page loaded and filtered successfully")
            return self.page

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.cleanup() # Ensure you close the browser on failure
            raise
    
    def cleanup(self):
        """Call this to prevent memory leaks"""
        if hasattr(self, 'browser'): self.browser.close()
        if hasattr(self, 'p'): self.p.stop()
        # self.page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        # self.page.wait_for_timeout(3000)
        
        # self.page.get_by_text("Closing within 14 days").click()

        # logger.info("Page loaded successfully")

        # return self.page

    def extract_rows(self, page: Page):
        """
        Trying to scrape the table from the page

        """

        page_number = 1

        while True:
           logger.info(f" Scraping Page {page_number}")

           tender_table = page.locator('//*[@id="table"]')

           if tender_table is None or page_number == 5: # sample for ten pages for demo
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
        """
        Help to process the rows of the table

        Args:
            rows: Playrwright object which is used to locate the rows content
        """

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

                if col_index == 1:
                    e_published_Date = cells.nth(col_index).inner_text().strip()
                    e_published_Date_converted = datetime.strptime(e_published_Date, "%d-%b-%Y %I:%M %p")
                    print(f"e_published_Date : {e_published_Date_converted}")
                

                if col_index == 4: 
                  filedata =  download_content(cells, self.page, e_published_Date_converted)


                """
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
                    #captchsolved= False

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
                                download_dir_new = tender_get_storage_dir(clean_text_new, e_published_Date_converted)
                                # print("download_path", download_dir_new) 
                                # download_dir = Path("downloads")
                                # download_dir.mkdir(parents=True, exist_ok=True)
                                # temp_path = download.path()
                                # print(temp_path)
                                custom_name = f"{clean_text_new}_{download.suggested_filename}"
                                download.save_as(download_dir_new/custom_name)
                                time.sleep(1)

                    page.wait_for_timeout(2000)
                    new_page.close()
                    
                """
                
            if row_data:
                self.data.append(row_data)

            # if self.download_data:
            #     print(self.download_data)
            
            if filedata not in self.download_data :
            #    breakpoint()
               print(filedata) 
               self.download_data.append(filedata)
        

    def form_json(self):
        """
        Help to form the json data
        """

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Tender_data_{timestamp}.json"
        filename_download = f"Tenders_filepath_{timestamp}.json"

        output_dir = "meta_data"
        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(output_dir, filename)
        filename_download_path = os.path.join(output_dir, filename_download)

        with open(filename_download_path,"w", encoding= "utf-8") as f1:
            json.dump(self.download_data,f1, indent=2, ensure_ascii=False )
        logger.info(f"✅ Data saved to {filename_download}")    

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Data saved to {filename}")

    def close(self):
        """
        Close the browser after the sucessful completion of the tasks

        """
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