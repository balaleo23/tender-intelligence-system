from datetime import datetime
from urllib.parse import urljoin
import time

from playwright.sync_api import Page, Locator

from ingestion_engine.constants import (
    DOWNLOAD_LINK_7_XPATH,
    DOWNLOAD_LINK_8_XPATH,
    ROW_WAIT_MS,
)
from ingestion_engine.utils.file_manager_dir import storage_manager
from ingestion_engine.utils.logger import get_logger

logger = get_logger(__name__)

downlod_dict: dict = {}


def download_content(cells: Locator, page: Page, e_published_Date_converted: datetime) -> dict:
    title_text = cells.nth(4).inner_text().strip()
    clean_text_new = title_text.split("[")[-1].replace("]", "").strip()

    title_cell = cells.nth(4)
    tender_href = title_cell.locator("a").get_attribute("href")

    if not tender_href:
        logger.warning("No tender href found for '%s' — skipping", clean_text_new)
        return downlod_dict

    full_url = urljoin(page.url, tender_href)
    logger.debug("Navigating to tender page: %s", full_url)

    new_page = page.context.new_page()
    new_page.goto(full_url, wait_until="domcontentloaded")

    locators = {
        "DirectLink_8": DOWNLOAD_LINK_8_XPATH,
        "DirectLink_7": DOWNLOAD_LINK_7_XPATH,
    }

    download_link_cnt = None
    selected = None

    for key, xpath in locators.items():
        locator = new_page.locator(xpath)
        if locator.count() > 0:
            download_link_cnt = locator
            selected = key
            break

    logger.info("Download link selected: %s", selected)

    if not download_link_cnt:
        logger.warning("No download link found for '%s' — skipping", clean_text_new)
        new_page.close()
        return downlod_dict

    download_href = download_link_cnt.get_attribute("href")

    if not download_href:
        logger.warning("No download href for '%s' — skipping", clean_text_new)
        new_page.close()
        return downlod_dict

    full_url_download = urljoin(page.url, download_href)
    logger.debug("Download URL: %s", full_url_download)

    if selected == "DirectLink_8":
        download_page = page.context.new_page()
        download_page.goto(full_url_download, wait_until="domcontentloaded")
        download_page.wait_for_selector('//*[@id="captchaImage"]', state="hidden", timeout=30000)
        # download_page.wait_for_timeout(30000)
        # download_link_cnt.wait_for(selector='//*[@id="DirectLink_7"]', state="hidden", timeout=30000)
        # --- OLD (broken): click fired before expect_download, and a Page was
        # --- passed to create_download which calls .click() with no selector ---
        # target_element = download_page.wait_for_selector('//*[@id="DirectLink_7"]')
        # download_page.click('//*[@id="DirectLink_7"]')
        # logger.info(f"download_link_cnt: {download_page}")
        # download = create_download(new_page, download_page)
        # save_download_storage(e_published_Date_converted, clean_text_new, download)
        # download_page.close()
        # download_link_cnt.click()
        # download_page.close()
        # selected ="DirectLink_7"

        # --- NEW: pass the download_page (where the download fires) and a
        # --- locator, so create_download clicks inside expect_download() ---
        download_page.wait_for_selector('//*[@id="DirectLink_7"]')
        download_link = download_page.locator('//*[@id="DirectLink_7"]')
        download = create_download(download_page, download_link)
        save_download_storage(e_published_Date_converted, clean_text_new, download)
        download_page.close()

    if selected == "DirectLink_7":
        download = create_download(new_page, download_link_cnt)

        save_download_storage(e_published_Date_converted, clean_text_new, download)

    page.wait_for_timeout(ROW_WAIT_MS)
    new_page.close()
    return downlod_dict

def save_download_storage(e_published_Date_converted, clean_text_new, download):
    download_dir_new = storage_manager.create_storage(
            tender_uid=clean_text_new,
            published_date=e_published_Date_converted,
        )
    custom_name = f"{clean_text_new}_{download.suggested_filename}"
    if clean_text_new not in downlod_dict:
        downlod_dict[clean_text_new] = str(download_dir_new / custom_name)
    download.save_as(download_dir_new / custom_name)
    time.sleep(1)

def create_download(new_page, download_link_cnt):
    with new_page.expect_download() as download_info:
        download_link_cnt.click()
    download = download_info.value
    return download
