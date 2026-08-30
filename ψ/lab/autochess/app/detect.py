"""ตรวจจับ piece ด้วย OpenCV template matching + จัดการ config ตำแหน่ง (calibration)."""
import json
import os
from pathlib import Path

import cv2
import numpy as np

from .pieces import PIECES

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
CONFIG_PATH = ROOT / "config.json"

# ค่าเริ่มต้น: สัดส่วนของจอ (0.0-1.0) — ปรับจริงด้วย --calibrate
DEFAULT_CONFIG = {
    # shop 5 ช่อง: x/y/w/h เป็นสัดส่วนของภาพ
    "shop":      {"x": 0.30, "y": 0.87, "w": 0.44, "h": 0.12},
    "board":     {"x": 0.15, "y": 0.25, "w": 0.70, "h": 0.45},
    "bench":     {"x": 0.15, "y": 0.76, "w": 0.70, "h": 0.09},
    "gold":      {"x": 0.03, "y": 0.94, "w": 0.08, "h": 0.05},
}

MATCH_THRESHOLD = 0.75


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return DEFAULT_CONFIG


def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))


def crop_ratio(img: np.ndarray, box: dict) -> np.ndarray:
    """ครอปตามสัดส่วน 0-1 ของภาพ"""
    h, w = img.shape[:2]
    x1 = int(box["x"] * w); y1 = int(box["y"] * h)
    x2 = int((box["x"] + box["w"]) * w); y2 = int((box["y"] + box["h"]) * h)
    return img[y1:y2, x1:x2]


def load_templates() -> dict[str, np.ndarray]:
    """โหลดรูป template ทั้งหมดจาก templates/<name>.png"""
    templates = {}
    if not TEMPLATES_DIR.exists():
        return templates
    for f in TEMPLATES_DIR.glob("*.png"):
        if f.stem in PIECES:
            templates[f.stem] = cv2.imread(str(f), cv2.IMREAD_COLOR)
    return templates


def match_in_region(region: np.ndarray, templates: dict[str, np.ndarray]):
    """หา piece ที่ match ใน region — คืน list ของ (name, confidence)

    ใช้ matchTemplate บน grayscale + เลือกจุดที่ score สูงสุดต่อ template
    (MVP: ตรวจว่า template ตัวไหน match มากที่สุดใน region แบบ rough)
    """
    if not templates or region.size == 0:
        return []
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    scores = []
    for name, tpl in templates.items():
        th, tw = tpl.shape[:2]
        if gray.shape[0] < th or gray.shape[1] < tw:
            continue
        res = cv2.matchTemplate(gray, cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY), cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val >= MATCH_THRESHOLD:
            scores.append((name, float(max_val)))
    scores.sort(key=lambda s: -s[1])
    return scores


def detect_shop_slots(img: np.ndarray, cfg: dict, templates: dict[str, np.ndarray]):
    """แบ่ง shop เป็น 5 ช่อง แล้วหา piece ต่อช่อง — คืน list[ (slot, name, conf) ]"""
    shop = crop_ratio(img, cfg["shop"])
    h, w = shop.shape[:2]
    results = []
    slot_w = w / 5
    for i in range(5):
        slot = shop[:, int(i * slot_w):int((i + 1) * slot_w)]
        m = match_in_region(slot, templates)
        if m:
            results.append((i, m[0][0], m[0][1]))
    return results


def detect_board(img: np.ndarray, cfg: dict, templates: dict[str, np.ndarray]):
    """นับ piece บน board — คืน dict name -> count (best-effort MVP)"""
    board = crop_ratio(img, cfg["board"])
    m = match_in_region(board, templates)
    # MVP: คืนเฉพาะตัวที่ match แรงสุดต่อ template — ต่อยอดนับหลายจุดภายหลัง
    return {name: 1 for name, _ in m}
