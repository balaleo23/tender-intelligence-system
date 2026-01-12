#web = https://eprocure.gov.in/eprocure/app     //*[@id="linkFwd"]


from playwright.sync_api import sync_playwright, expect
import pandas as pd
import re
import json

URL = "https://eprocure.gov.in/eprocure/app?page=FrontEndListTendersbyDate&service=page"

data = []
with sync_playwright() as p:
    browser= p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(URL,wait_until="domcontentloaded",timeout=6000)

    # wait_until(Text("Tenders/Auctions Closing Today").exists)
    # expect(page.get_by_text("Tenders/Auctions Closing Today")).to_be_visible()
    print("Page loaded successfully")
    # page.wait_for_timeout(3000)
    # page.get_by_text("Tenders by Closing Date").click()
    page.wait_for_timeout(3000)
    page.get_by_text("Closing within 14 days").click()

    

    tenders = page.locator('//*[@id="table"]')
    print("Table found:", tenders.count())

    if tenders:
        rows = tenders.locator("tr")



    print("Rows Count:", rows.count())
    page.wait_for_timeout(2000)

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
       
        for col_index in range(min(cells.count(),len(headers))):
               cell_value = cells.nth(col_index).inner_text().strip()
               row_data[headers[col_index]] = cell_value
        
        if row_data:
            data.append(row_data)
            print("\n")
            

    json_data = json.dumps(data, indent=2, ensure_ascii=False)
    print("\nFormatted JSON output:")
    print(data)
   

    with open('tender_data4.json', 'w', encoding='utf-8') as f:
        f.write(json_data)


    # print(data)
    # df = pd.DataFrame(data)
    # df.to_csv('scrapped_data.csv', index=False, header=False)



        # row_data = [cells.nth(j).inner_text().strip()
        #             for j in range(cells.count())]




    browser.close()
    # page.get_by_text("Tenders/Auctions Closing Today").click()
    # page.get_by_text("closing within 14 days", exact=False).click()

    # table = page.locator('//*[@id="table"]')

    # tenders = page.locator('//*[@id="table"]//tr')
    # tenders_content = page.locator('//*[@id="table"]//tbody/tr')

    # for i in range(tenders.count()):
        # row = tenders.nth(i)
        # print(row.inner_text())                    








"""
while True:
    rows_before = page.locator("#table tr").count()

    link_fwd = page.locator("#linkFwd")
    if link_fwd.count() == 0 or not link_fwd.is_visible():
        break

    link_fwd.click()

    # wait until row count changes
    page.wait_for_function(
        # (prev) => document.querySelectorAll('#table tr').length !== prev, # need to add triple column
        rows_before
    )



while True:
    rows_before = page.locator("#table tr").count()

    link_fwd = page.locator("#linkFwd")
    if link_fwd.count() == 0 or not link_fwd.is_visible():
        break

    link_fwd.click()

    # wait until row count changes
    page.wait_for_function(

from helium import *
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

# Auto ChromeDriver setup

start_chrome()

go_to("https://eprocure.gov.in/eprocure/app?page=FrontEndListTendersbyDate&service=page")
wait_until(Text("Tenders/Auctions Closing Today").exists)
click("Closing within 14 days")
tenders = find_all(S('//*[@id="table"]'))

for tender in tenders:
    try:
        cols = tender.find_all("td")  # use "td" directly
        title = cols[4].text.strip() if len(cols) > 4 else "N/A"
        print(f"Title: {title}")
    except Exception as e:
        print(f"Error: {str(e)}")
        continue

# Extract tender data like your Heavy Water Board example
# tenders = find_all(S("table tr"))[1:5]  # First 5 tenders
# for tender in tenders:
#     try:
#         cols = tender.find_all(S("td"))
#         print(f"Title: {cols[4].text.strip() if len(cols)>4 else 'N/A'}")
#     except:
#         continue

kill_browser()


# service = Service(ChromeDriverManager().install())
# start_chrome(service=service, headless=True)

# go_to("https://eprocure.gov.in/eprocure/app?page=FrontEndListTendersbyDate&service=page")
# wait_until(Text("Tenders/Auctions Closing Today").exists)
# click("Closing within 14 days")
# tenders = find_all(S("//table//tr"))[1:]
# for row in tenders:
#     cols = row.find_all(S("td"))
#     if cols:
#         print(f"Title: {cols[4].web_element.text}")  # Adjust index for title 
"""
