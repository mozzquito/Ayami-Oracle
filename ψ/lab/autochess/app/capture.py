"""ADB screen capture: จับภาพจอมือถือ Android → numpy BGR image."""
import subprocess
import numpy as np
import cv2


class CaptureError(Exception):
    pass


def check_device() -> str:
    """ตรวจว่ามีมือถือต่ออยู่ คืน serial ตัวแรก"""
    out = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = [l for l in out.stdout.splitlines()[1:] if l.strip()]
    devices = [l.split("\t")[0] for l in lines if l.endswith("device")]
    if not devices:
        raise CaptureError(
            "ไม่พบมือถือ — ต่อ USB, เปิด USB Debugging และกดยืนยันบนมือถือ "
            "(หรือรัน: brew install --cask android-platform-tools)"
        )
    return devices[0]


def screencap() -> np.ndarray:
    """จับภาพจอปัจจุบัน คืนเป็น numpy image (BGR)"""
    proc = subprocess.run(
        ["adb", "exec-out", "screencap", "-p"], capture_output=True, timeout=10
    )
    if proc.returncode != 0 or not proc.stdout:
        raise CaptureError(f"adb screencap ล้มเหลว: {proc.stderr.decode(errors='replace')}")
    # แปลง PNG bytes → numpy image
    buf = np.frombuffer(proc.stdout, dtype=np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is None:
        raise CaptureError("ถอดรหัสภาพไม่สำเร็จ")
    return img
