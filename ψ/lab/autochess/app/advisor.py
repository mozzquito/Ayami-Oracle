"""Advisor: ให้คะแนน piece ใน shop แล้วแนะนำ ซื้อ/ข้าม"""
from collections import Counter

from .pieces import PIECES, DISPLAY, synergy_tags, META_COMPS

# น้ำหนักคะแนน
W_PAIR_UP = 10.0   # จับคู่เป็น 2 ดาวได้ (มี 1 ตัวแล้ว)
W_TRIPLE = 14.0    # มี 2 ตัวแล้ว ซื้อใบนี้ = 2 ดาวทันที
W_SYNERGY = 4.0    # เพิ่ม synergy ที่ board มีอยู่ (ต่อ tag)
W_META_CORE = 6.0  # เป็น core ของ meta comp
W_META_TAG = 3.0   # tag เข้ากับ meta comp ที่ board กำลังเล่น
BUY_THRESHOLD = 6.0


def board_tags(board: dict[str, int]) -> Counter:
    tags = Counter()
    for name, cnt in board.items():
        for _ in range(cnt):
            tags.update(synergy_tags(name))
    return tags


def best_matching_comp(board: dict[str, int]):
    """เดา meta comp ที่ใกล้ที่สุดกับ board ปัจจุบัน"""
    if not board:
        return None
    tags = board_tags(board)
    best, best_score = None, -1
    for comp in META_COMPS:
        score = sum(tags.get(t, 0) for t in comp["tags"])
        if score > best_score:
            best, best_score = comp, score
    return best


def score_piece(name: str, board: dict[str, int], owned_bench: dict[str, int]) -> float:
    """คะแนน piece ใน shop ตาม board/bench ปัจจุบัน"""
    p = PIECES.get(name)
    if not p:
        return 0.0
    have = board.get(name, 0) + owned_bench.get(name, 0)
    score = 0.0
    if have == 1:
        score += W_PAIR_UP
    elif have >= 2:
        score += W_TRIPLE

    tags = board_tags(board)
    score += sum(W_SYNERGY for t in synergy_tags(name) if tags.get(t, 0) > 0)

    comp = best_matching_comp(board)
    if comp:
        if name in comp["core"]:
            score += W_META_CORE
        elif set(synergy_tags(name)) & set(comp["tags"]):
            score += W_META_TAG
    return score


def advise(shop: list[tuple[int, str, float]], board: dict[str, int],
           bench: dict[str, int], gold: int | None) -> str:
    """สร้างคำแนะนำเป็นข้อความ"""
    lines = []
    gold_txt = f"{gold}g" if gold is not None else "?g"
    tags = board_tags(board)
    tag_txt = ", ".join(f"{v}x{k}" for k, v in tags.most_common(4)) or "ว่าง"
    comp = best_matching_comp(board)
    comp_txt = f" | Comp ใกล้เคียง: {comp['name']}" if comp else ""
    lines.append(f"💰 {gold_txt} | Board: {tag_txt}{comp_txt}")

    buy, skip = [], []
    for slot, name, conf in shop:
        s = score_piece(name, board, bench)
        disp = f"{DISPLAY.get(name, name)} (slot {slot+1}, conf {conf:.2f})"
        if s >= BUY_THRESHOLD and (gold is None or PIECES[name]["cost"] <= gold):
            buy.append(f"{disp} — คะแนน {s:.0f} ✅")
        else:
            skip.append(f"{disp} — คะแนน {s:.0f} ❌")
    lines.append("ซื้อ: " + (" | ".join(buy) if buy else "ไม่มีใบไหนคุ้ม"))
    lines.append("ข้าม: " + (" | ".join(skip) if skip else "-"))
    return "\n".join(lines)
