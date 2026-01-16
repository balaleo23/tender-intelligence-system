import pytesseract
from PIL import Image
import cv2
import numpy as np
from playwright.sync_api import sync_playwright
import re
import io
import easyocr
import captch_cnn_solver



def solve_text_captcha_with_tesseract(page):
    """Free OCR solution for text CAPTCHAs"""
    
    # Common CAPTCHA image selectors
    captcha_selectors = [
       '//*[@id="captchaImage"]','//*[@id="captchaText"]'
    ]
    
    for selector in captcha_selectors:
        captcha_img = page.locator(selector).first
        if captcha_img.count() > 0:
            # Screenshot CAPTCHA image
            captcha_element = captcha_img.bounding_box()
            screenshot = page.screenshot(
                                clip={
                                    'x': float(captcha_element['x']),
                                    'y': float(captcha_element['y']),
                                    'width': float(captcha_element['width']),
                                    'height': float(captcha_element['height'])
                                }
                                    )
            
            # Process image for better OCR
            img = Image.open(io.BytesIO(screenshot))
            img_array = np.array(img.convert('RGB'))
            
            capthc = captch_cnn_solver.CaptchaCNN()
            captcha_text = capthc.predict(img)
            print(f"Captcha form cnn {captcha_text}")

            reader = easyocr.Reader(['en'], gpu=False)
            # img = preprocess_captcha_image(img)
            img.save("debug_processed_captcha.png")
            result = reader.readtext(img_array, detail=0)
            result1 = reader.readtext(screenshot, detail=0)
            # results = reader.readtext(img, detail=0, paragraph=False)
            text = ''.join(result).strip()
            print(f"text from processed {text}")
            text1 = ''.join(result1).strip()
            print(f"text1 from screenshot {text1}")
            # if 4 <= len(text) <= 6:
            #     text 
            # else:
            #     text = None
            # captcha_textnew = ()
            # Extract text
            # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

            # captcha_text = pytesseract.image_to_string(img, config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
            # captcha_text = re.sub(r'[^A-Za-z0-9]', '', captcha_text)
            
            # print(f"Tesseract solved CAPTCHA: {captcha_text}")
            
            # # Fill CAPTCHA field
            # captcha_input = page.locator('input[name*="captcha"], input[id*="captcha"]').first
            # captcha_input.fill(captcha_text)
            text = clean_captcha_text(text)
            return text
    
    return None


def clean_captcha_text(text):
    """Remove ALL spaces from OCR result"""
    # Remove spaces completely, then strip whitespace
    cleaned = ''.join(text.split()).strip()
    return cleaned

def preprocess_captcha_image(img):
    """Improve OCR accuracy for CAPTCHA images"""
    # Convert to grayscale
    img = img.convert('L')
    img_np = np.array(img)

    img_np = cv2.medianBlur(img_np, 3)
    img_np = cv2.GaussianBlur(img_np, (3, 3), 0)

    img_np = cv2.adaptiveThreshold(img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    img_np = cv2.morphologyEx(img_np, cv2.MORPH_OPEN, kernel)
    img_clean = Image.fromarray(img_np)
    # Enhance contrast
    # img = ImageEnhance.Contrast(img).enhance(2)
    
    # Apply threshold
    # img_np = np.array(img)
    # _, img_np = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # img = Image.fromarray(img_np)
    
    return img_clean
