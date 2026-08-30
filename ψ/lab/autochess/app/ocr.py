"""OCR ตัวเลข (เงิน/เลเวล) ด้วย Tesseract — ใช้เฉพาะตัวเลขเพราะแม่นกว่ามาก"""
import re

import cv2
import numpy as np
import pytesseract

from .detect import crop_ratio


def read_number(img: np.ndarray, box: dict) -> int | None:
    """อ่านตัวเลขจากบริเวณ box (สัดส่วน 0-1) — คืน int หรือ None ถ้าอ่านไม่ได้"""
    region = crop_ratio(img, box)
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    # ขยาย + threshold ให้ตัวเลขชัด
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # ตัวเลขในเกมมักเป็นตัวขาวบนพื้นเข้ม — ลองทั้งสองขั้ว
    for im in (binary, cv2.bitwise_not(binary)):
        text = pytesseract.image_to_string(
            im, config="--psm 7 -c tessedit_char_whitelist=0123456789"
        )
        m = re.search(r"\d+", text)
        if m:
            return int(m.group())
    return None
