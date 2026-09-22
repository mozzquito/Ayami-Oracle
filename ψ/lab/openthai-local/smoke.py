import os, sys, time, resource, torch
os.environ["HF_HUB_OFFLINE"] = "1"
from openthai_systemone import SystemOneClient, Choice, Score, Noul
dev = sys.argv[1] if len(sys.argv) > 1 else None
t0 = time.time()
client = SystemOneClient("model", device=dev)  # local dir, no network
print(f"device={client.device} dtype={next(client.model.parameters()).dtype} load={time.time()-t0:.1f}s")
state = {"ticket": "ลูกค้าแจ้งว่าโดนหักเงินซ้ำสองครั้ง ขอเงินคืนด่วน โทรมาสามรอบแล้ว"}
qs = {
  "department": Choice(instructions="ทีมใดควรรับผิดชอบ", criteria={"billing": "การเงิน/ค่าบริการ", "technical": "ระบบใช้งานไม่ได้", "sales": None}),
  "frustration": Score(instructions="ลูกค้าหงุดหงิดแค่ไหน", criteria=["ใจเย็น", "หงุดหงิดแต่สุภาพ", "โกรธมาก"]),
  "refund_requested": Noul(instructions="ลูกค้าขอเงินคืน"),
}
outs, times = [], []
for i in range(6):
    t = time.time(); r = client.system_one(state=state, questions=qs); times.append(time.time() - t)
    outs.append((r.answers["department"].choice, round(r.answers["department"].probabilities["billing"], 6), round(r.answers["frustration"].score, 6), round(r.answers["refund_requested"].noul, 6)))
print("first call %.2fs (warm-up), next calls median %.2fs" % (times[0], sorted(times[1:])[2]))
print("answer:", outs[0], "| usage", r.usage)
print("identical across 6 repeats (deterministic):", len(set(outs)) == 1)
print("max RSS: %.2f GB" % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9))
