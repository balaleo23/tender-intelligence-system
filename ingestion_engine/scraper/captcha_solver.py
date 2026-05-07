import io
from typing import Optional

import cv2
import easyocr
import numpy as np
from PIL import Image
from playwright.sync_api import Page

from ingestion_engine.constants import CAPTCHA_IMAGE_XPATH, CAPTCHA_TEXT_XPATH
from ingestion_engine.utils.logger import get_logger

logger = get_logger(__name__)


def solve_text_captcha(page: Page) -> Optional[str]:
    for selector in [CAPTCHA_IMAGE_XPATH, CAPTCHA_TEXT_XPATH]:
        captcha_img = page.locator(selector).first
        if captcha_img.count() > 0:
            captcha_element = captcha_img.bounding_box()
            screenshot = page.screenshot(
                clip={
                    "x": float(captcha_element["x"]),
                    "y": float(captcha_element["y"]),
                    "width": float(captcha_element["width"]),
                    "height": float(captcha_element["height"]),
                }
            )

            img = Image.open(io.BytesIO(screenshot))
            img_array = np.array(img.convert("RGB"))

            reader = easyocr.Reader(["en"], gpu=False)
            result = reader.readtext(img_array, detail=0)
            text = clean_captcha_text("".join(result).strip())

            logger.debug("CAPTCHA OCR result: %s", text)
            return text

    return None


def clean_captcha_text(text: str) -> str:
    return "".join(text.split()).strip()


def preprocess_captcha_image(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img_np = np.array(img)
    img_np = cv2.medianBlur(img_np, 3)
    img_np = cv2.GaussianBlur(img_np, (3, 3), 0)
    img_np = cv2.adaptiveThreshold(
        img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    img_np = cv2.morphologyEx(img_np, cv2.MORPH_OPEN, kernel)
    return Image.fromarray(img_np)
