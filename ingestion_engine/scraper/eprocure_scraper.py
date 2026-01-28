import json
from datetime import datetime
import logging
from playwright.sync_api import sync_playwright, Page, Locator
from ingestion_engine.scraper import captch_cnn_solver, captcha_solver
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from PIL import Image
from pathlib import Path
import time
from ingestion_engine.utils.file_manager_dir  import storage_manager
import sys
import os

# Add the parent directory (my_project) to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# from utils.file_manager_dir import TenderStorageManager

# download_filepath =[]

downlod_dict ={} 
def download_content(cells : Locator, page : Page,  e_published_Date_converted : datetime) -> dict:
                   
                    title_text = cells.nth(4).inner_text().strip()
                    # clean_text = title_text.split("]")[0].replace("[", "").strip()
                    clean_text_new = title_text.split("[")[-1].replace("]", "").strip()
                    # downlod_dict ={} 
                       

                    title_cell = cells.nth(4)
                    tender_href = title_cell.locator("a").get_attribute("href")

 

                    full_url = urljoin(page.url, tender_href)
                    print(full_url)

                    new_page = page.context.new_page()
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
                    if download_link_cnt:
                        download_href = download_link_cnt.get_attribute('href')
                        if download_href:
                            print(f"Link href: {download_href}")
                            full_url_download = urljoin(page.url, download_href)
                            print(f"Full Url download{full_url_download}")
                            if selected == 'DirectLink_8':
                                download_page = page.context.new_page()
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

                                    

                                    download_dir_new = storage_manager.create_storage(
                                            tender_uid=clean_text_new,
                                            published_date=e_published_Date_converted
                                        )
                                    # download_dir_new = tender_get_storage_dir(clean_text_new, e_published_Date_converted)
                                    
                                    
                                    # print("download_path", download_dir_new) 
                                    # download_dir = Path("downloads")
                                    # download_dir.mkdir(parents=True, exist_ok=True)
                                    # temp_path = download.path()
                                    # print(temp_path)
                                    custom_name = f"{clean_text_new}_{download.suggested_filename}"
                                    if clean_text_new not in downlod_dict: 
                                        downlod_dict[clean_text_new] = str(download_dir_new/custom_name)
                                    download.save_as(download_dir_new/custom_name)
                                    time.sleep(1)
                        
                    page.wait_for_timeout(2000)
                    new_page.close()
                    return downlod_dict
            