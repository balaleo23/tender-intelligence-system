import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

from playwright.sync_api import sync_playwright, Page, Locator, TimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URL = "https://eprocure.gov.in/eprocure/app?page=FrontEndListTendersbyDate&service=page"

data = []

class Scrapper: 

    

    def open_load_content() -> Page:
        # with sync_playwright() as p:
            p = sync_playwright().start()
            browser= p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(URL,wait_until="domcontentloaded",timeout=6000)

            print("Page loaded successfully")
            page.wait_for_timeout(6000)
            page.get_by_text("Closing within 14 days").click()
            return page
           

    def extract_rows(self, page: Page):
        page_number = 1

        while True:
            print(f"\n📄 Scraping Page {page_number}")

            # 1️⃣ Locate table
            table = page.locator("#table")
            rows = table.locator("tr")

            # 2️⃣ Process rows
            page.wait_for_timeout(2000)
            self.process_rows(rows)

            # 3️⃣ Locate Next button
            next_btn = page.locator("#linkFwd")

            # 4️⃣ Stop condition
            if next_btn.is_disabled():
                print("❌ No more pages")
                break

            # 5️⃣ Click Next
            next_btn.click()

            # 6️⃣ Wait for page update
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)

            page_number += 1
            
            # table = page.locator("#table")
            # rows = table.locator("tr")
            # return rows


              

    def process_rows(self,rows: Locator) -> list:
        headers = []
        if rows.count() > 0:
            first_row = rows.nth(0)
            first_cells = first_row.locator("th, td")
            
            for column_index in range(first_cells.count()):
                header = first_cells.nth(column_index).inner_text().strip()
                headers.append(header) 

            print(f"Headers extracted: {headers}")

        for row_index in range(1, rows.count()):
            if row_index == rows.count()-1:
                break
            row = rows.nth(row_index)
            cells = row.locator("th, td")
            cells_count = cells.count()

            # result_list = re.findall(r'\[(.*?)\]', text)
        
            row_data = {}
        
            for col_index in range(min(cells_count,len(headers))):
                cell_value = cells.nth(col_index).inner_text().strip()
                row_data[headers[col_index]] = cell_value
            
            if row_data:
                data.append(row_data)
                print("\n")
        print(data)        
        return data
            
    def form_json(data : list) -> None:
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Tender_data_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_data)
        print("scrapperclosed")


if __name__ == "__main__":
        print("running")
        rows_got =  Scrapper.open_load_content()
        processed_data = Scrapper.process_rows(rows_got)
        Scrapper.form_json(processed_data)
        print("Process completed")

        
