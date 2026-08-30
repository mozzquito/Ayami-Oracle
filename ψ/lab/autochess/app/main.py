"""จุดเข้าโปรแกรม — โหมด: assist (ปกติ), --calibrate, --learn

วิธีรัน:
  ./run.sh              # โหมดช่วยเล่น
  ./run.sh calibrate    # ตั้งค่าตำแหน่ง shop/board
  ./run.sh learn        # บันทึกรูป template ของ piece
"""
import argparse
import sys
import time
from pathlib import Path

import cv2

from . import capture, detect, ocr
from .advisor import advise

SNAPSHOT = Path("snapshot.png")


def select_box(title: str, img):
    """เลือกกรอบด้วยการคลิกเมาส์ 2 ครั้ง (มุมซ้ายบน → มุมขวาล่าง)

    ใช้แทน cv2.selectROI เพราะบน macOS คีย์บอร์ดของ selectROI มักไม่ทำงาน
    คืน (x, y, w, h) หรือ None ถ้าปิดหน้าต่าง/คลิกจุดเดิมซ้ำ
    """
    state = {"p1": None, "p2": None, "done": False}

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if state["p1"] is None:
                state["p1"] = (x, y)
            else:
                state["p2"] = (x, y)
                state["done"] = True

    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(title, on_mouse)
    print(f"🖱️ [{title}] คลิกมุมซ้ายบน → คลิกมุมขวาล่าง ของกรอบที่ต้องการ (ปิดหน้าต่างเพื่อยกเลิก)")

    # แสดงภาพวาด guide line ตำแหน่งคลิกแรก
    display = img.copy()
    while not state["done"]:
        cv2.imshow(title, display)
        if cv2.waitKey(50) != -1:  # กดคีย์ใด ๆ = ยอมรับ (รองรับกรณีคีย์ทำงาน)
            if state["p1"] and state["p2"]:
                break
        if cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
            cv2.destroyAllWindows()
            return None
        if state["p1"]:
            d = display.copy()
            cv2.circle(d, state["p1"], 8, (0, 255, 0), 2)
            cv2.imshow(title, d)
    cv2.destroyAllWindows()

    x1, y1 = state["p1"]
    x2, y2 = state["p2"]
    if (x1, y1) == (x2, y2):
        return None
    x, y = min(x1, x2), min(y1, y2)
    w, h = abs(x2 - x1), abs(y2 - y1)
    return (x, y, w, h) if w > 2 and h > 2 else None


def cmd_calibrate():
    """จับภาพ 1 รูป ให้ผู้ใช้เลือกบริเวณ shop/board/bench/gold ด้วยเมาส์ (คลิก 2 จุด)"""
    capture.check_device()
    img = capture.screencap()
    cv2.imwrite(str(SNAPSHOT), img)
    print(f"📸 บันทึกภาพเป็น {SNAPSHOT.resolve()}")
    print("จะตั้งค่า 4 บริเวณทีละอัน: shop(แถบร้าน 5 ใบ), board(กระดาน), bench(ม้านั่งสำรอง), gold(ตัวเลขเงิน)")
    print("→ คลิกมุมซ้ายบน แล้วคลิกมุมขวาล่าง ของแต่ละบริเวณ (ปิดหน้าต่างเพื่อข้าม)")

    cfg = detect.load_config()
    for key in ("shop", "board", "bench", "gold"):
        box = select_box(f"เลือกบริเวณ: {key}", img)
        if box:
            x, y, w, h = box
            H, W = img.shape[:2]
            cfg[key] = {"x": x / W, "y": y / H, "w": w / W, "h": h / H}
            print(f"  ✅ {key}: {cfg[key]}")
        else:
            print(f"  ⏭️ ข้าม {key} (ใช้ค่าเดิม)")
    detect.save_config(cfg)
    print(f"💾 บันทึก config แล้ว → {detect.CONFIG_PATH}")


def cmd_learn():
    """จับภาพ 1 รูป ให้ผู้ใช้เลือกกรอบ piece ด้วยคลิก 2 จุด แล้วพิมพ์ชื่อเพื่อบันทึก template"""
    from .pieces import PIECES

    capture.check_device()
    detect.TEMPLATES_DIR.mkdir(exist_ok=True)
    names = sorted(PIECES)
    print("📋 ชื่อ piece ที่รองรับ:", ", ".join(names))
    while True:
        img = capture.screencap()
        box = select_box("คลิกมุมซ้ายบน → มุมขวาล่าง ของ piece (ปิดหน้าต่างเพื่อออก)", img)
        if not box:
            break
        x, y, w, h = box
        crop = img[y:y + h, x:x + w]
        name = input("ชื่อ piece (เช่น red_axe, ว่างเปล่า=ทิ้ง): ").strip()
        if not name:
            continue
        if name not in PIECES:
            print(f"⚠️ ไม่รู้จัก '{name}' — เพิ่มใน app/pieces.py ก่อน")
            continue
        out = detect.TEMPLATES_DIR / f"{name}.png"
        cv2.imwrite(str(out), crop)
        print(f"💾 บันทึก {out}")


def cmd_assist(interval: float = 2.0):
    """loop หลัก: จับจอ → ตรวจจับ → แนะนำ"""
    capture.check_device()
    cfg = detect.load_config()
    templates = detect.load_templates()
    if not templates:
        print("❌ ยังไม่มี template — รัน './run.sh learn' ก่อนเพื่อบันทึกรูป piece")
        sys.exit(1)
    print(f"👀 เริ่มช่วยเล่น ({len(templates)} templates) — Ctrl+C เพื่อหยุด\n")
    last_msg = ""
    try:
        while True:
            try:
                img = capture.screencap()
            except capture.CaptureError as e:
                print(f"⚠️ {e}"); time.sleep(3); continue
            shop = detect.detect_shop_slots(img, cfg, templates)
            board = detect.detect_board(img, cfg, templates)
            gold = ocr.read_number(img, cfg["gold"])
            msg = advise(shop, board, {}, gold)
            if msg != last_msg:
                print(msg + "\n" + "-" * 50)
                last_msg = msg
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 หยุดแล้ว")


def main():
    ap = argparse.ArgumentParser(prog="autochess-assistant")
    ap.add_argument("--calibrate", action="store_true", help="ตั้งค่าตำแหน่งบนจอ")
    ap.add_argument("--learn", action="store_true", help="บันทึกรูป template piece")
    args = ap.parse_args()
    if args.calibrate:
        cmd_calibrate()
    elif args.learn:
        cmd_learn()
    else:
        cmd_assist()


if __name__ == "__main__":
    main()
