"""ฐานข้อมูล piece ของ Auto Chess Mobile (Drodo) — MVP เริ่มจาก piece ยอดนิยม

โครงสร้าง: name -> {cost, species (list), classes (list)}
เอาไว้เติมเพิ่มเรื่อย ๆ ได้
"""

PIECES = {
    # ---- 1 cost ----
    "red_axe":       {"cost": 1, "species": ["goblin"],  "classes": ["warrior"]},
    "sword_master":  {"cost": 1, "species": ["orc"],     "classes": ["warrior"]},
    "wendigo":       {"cost": 1, "species": ["beast"],   "classes": ["warrior"]},
    "stabber":       {"cost": 1, "species": ["goblin"],  "classes": ["assassin"]},
    "toxic_savage":  {"cost": 1, "species": ["cave_elf"],"classes": ["druid"]},
    # ---- 2 cost ----
    "pirate_captain":{"cost": 2, "species": ["human"],   "classes": ["warrior"]},
    "sword_knight":  {"cost": 2, "species": ["human"],   "classes": ["knight"]},
    "dire_wolf":     {"cost": 2, "species": ["beast"],   "classes": []},
    "goblin_pilot":  {"cost": 2, "species": ["goblin"],  "classes": ["mech"]},
    "night_wisp":    {"cost": 2, "species": ["cave_elf"],"classes": ["mage"]},
    # ---- 3 cost ----
    "poison_master": {"cost": 3, "species": ["beast"],   "classes": ["mage"]},
    "cursed_crow":   {"cost": 3, "species": ["beast"],   "classes": []},
    "warrior":       {"cost": 3, "species": ["orc"],     "classes": ["warrior"]},
    "shining_archer":{"cost": 3, "species": ["human"],   "classes": ["hunter"]},
    "beast_elder":   {"cost": 3, "species": ["beast"],   "classes": ["shaman"]},
    # ---- 4-5 cost ----
    "dominator":     {"cost": 4, "species": ["demon"],   "classes": ["knight"]},
    "doom":          {"cost": 4, "species": ["demon"],   "classes": ["warrior"]},
    "tsunami_stone": {"cost": 4, "species": ["marine"],  "classes": ["mage"]},
    "storm_bringer": {"cost": 4, "species": ["marine"],  "classes": ["mage"]},
    "corrupted_angel":{"cost": 5, "species": ["spirit"], "classes": ["knight"]},
    "thunder_lord":  {"cost": 5, "species": ["spirit"],  "classes": ["mage"]},
}

# ชื่อแสดงผล (ไทย/อังกฤษอ่านง่าย)
DISPLAY = {
    "red_axe": "Red Axe", "sword_master": "Sword Master", "wendigo": "Wendigo",
    "stabber": "Stabber", "toxic_savage": "Toxic Savage",
    "pirate_captain": "Pirate Captain", "sword_knight": "Sword Knight",
    "dire_wolf": "Dire Wolf", "goblin_pilot": "Goblin Pilot", "night_wisp": "Night Wisp",
    "poison_master": "Poison Master", "cursed_crow": "Cursed Crow",
    "warrior": "Warrior (3c)", "shining_archer": "Shining Archer",
    "beast_elder": "Beast Elder",
    "dominator": "Dominator", "doom": "Doom", "tsunami_stone": "Tsunami Stone",
    "storm_bringer": "Storm Bringer", "corrupted_angel": "Corrupted Angel",
    "thunder_lord": "Thunder Lord",
}


def synergy_tags(piece_name: str) -> list[str]:
    p = PIECES.get(piece_name)
    return p["species"] + p["classes"] if p else []


# meta comps อย่างง่าย: list ของ tag ที่ comp นั้นต้องการ
META_COMPS = [
    {"name": "Beast Warrior",    "tags": ["beast", "warrior"], "core": ["red_axe", "wendigo", "warrior", "doom"]},
    {"name": "Goblin Mech",      "tags": ["goblin", "mech"],   "core": ["red_axe", "stabber", "goblin_pilot"]},
    {"name": "Human Knight Mage","tags": ["human", "knight", "mage"], "core": ["sword_knight", "shining_archer", "corrupted_angel"]},
    {"name": "Marine Mage",      "tags": ["marine", "mage"],   "core": ["tsunami_stone", "storm_bringer"]},
    {"name": "Beast Druid",      "tags": ["beast", "druid"],   "core": ["toxic_savage", "dire_wolf", "beast_elder"]},
]
