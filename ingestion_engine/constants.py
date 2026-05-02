import re
from enum import Enum
from pathlib import Path

# --- Portal ---
EPROCURE_URL = "https://eprocure.gov.in/eprocure/app?page=FrontEndListTendersbyDate&service=page"
SOURCE_PORTAL = "eprocure.gov.in"
TENDER_FILTER_TEXT = "Closing within 14 days"
MAX_SCRAPE_PAGES = 5

# --- Scraper XPath / CSS selectors ---
TENDER_TABLE_XPATH = '//*[@id="table"]'
NEXT_PAGE_SELECTOR = "#linkFwd"
DOWNLOAD_LINK_7_XPATH = '//*[@id="DirectLink_7"]'
DOWNLOAD_LINK_8_XPATH = '//*[@id="DirectLink_8"]'
CAPTCHA_IMAGE_XPATH = '//*[@id="captchaImage"]'
CAPTCHA_TEXT_XPATH = '//*[@id="captchaText"]'
CAPTCHA_SUBMIT_XPATH = '//*[@id="Submit"]'

# --- Scraper timeouts (milliseconds) ---
NAV_TIMEOUT_MS = 90_000
PAGE_LOAD_TIMEOUT_MS = 60_000
BUTTON_WAIT_TIMEOUT_MS = 10_000
DOWNLOAD_TIMEOUT_MS = 30_000
ROW_WAIT_MS = 2_000
PAGE_TURN_WAIT_MS = 3_000

# --- Parsing ---
TENDER_DATE_FORMAT = "%d-%b-%Y %I:%M %p"
UID_PATTERN = re.compile(r"\[([^\]]+)\]")
ORG_SEPARATOR = "||"

# --- Storage directories ---
BASE_DATA_DIR = Path("data/tenders")
DIR_RAW = "raw"
DIR_EXTRACTED = "extracted"
DIR_PROCESSED = "processed"
METADATA_DIR = "meta_data"

# --- Document processing ---
MIN_TEXT_LENGTH = 100
OCR_DPI = 300
OCR_LANG = "eng"
TESSERACT_CONFIG = "--psm 6"
FILE_CHUNK_SIZE = 8192


class IngestionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
