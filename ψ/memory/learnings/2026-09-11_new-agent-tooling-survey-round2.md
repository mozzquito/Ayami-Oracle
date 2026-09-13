# New agent tooling survey (round 2) — code review/security/testing + observability/eval

Source: มอสสั่งให้ zcode (code-review/security/testing angle) + agy (observability/eval/MCP angle) ค้นเน็ตจริงแยกมุมกัน เพื่อกันซ้ำกับ 7 ข้อรอบแรก (`2026-09-11_agent-token-efficiency-playbook.md`, `2026-09-11_subagent-routing-rules.md`) — Ayami ตรวจ QC แล้วผ่าน (มี source จริง, หลายตัวยืนยันได้เองว่ามีอยู่จริง)

## จาก zcode — code review / security / testing tooling

- **Aviator Verify** — spec-driven/intent-based code review: เช็คว่า PR ตรง intent ของ requirement จริงไหม ไม่ใช่หา bug ผิวเผิน — [Redgate](https://www.red-gate.com/simple-talk/ai/the-best-ai-developer-tools-in-2026-from-coding-agents-to-code-review/)
- **GitHub MCP Server Secret Scanning** (Mar 2026) — agent เรียกสแกน secret ผ่าน MCP ก่อน commit/PR ได้เลย ไม่ต้องรอ CI — [GitHub Changelog](https://github.blog/changelog/2026-03-17-secret-scanning-in-ai-coding-agents-via-the-github-mcp-server/)
- **Apiiro CLI** — security scanner ออกแบบมาเพื่อโค้ดที่ AI agent เขียนโดยเฉพาะ (SAST เดิมสมมติว่ามนุษย์เขียน) — [Apiiro blog](https://apiiro.com/blog/security-tools-were-built-for-humans-we-built-one-for-ai-agents-introducing-apiiro-cli/)
- **mabl MCP Server** — agent ถาม/รัน/ดู root-cause test ผ่าน natural language จาก IDE/agent โดยตรง — [TestGuild](https://testguild.com/7-innovative-ai-test-automation-tools-future-third-wave/)
- **Auto TFA (autonomous test-failure analysis)** — agent วิเคราะห์ root-cause test ที่พังใน CI เอง แยก flaky จาก regression จริง — [TestGuild](https://testguild.com/7-innovative-ai-test-automation-tools-future-third-wave/)

## จาก agy — observability / eval / MCP ecosystem

- **Langfuse** — open-source LLM observability: trace/cost/latency ข้ามหลาย model+CLI พร้อมกัน — [langfuse.com](https://langfuse.com) / [GitHub](https://github.com/langfuse/langfuse)
- **Arize Phoenix** — OTel-native observability, track agent trajectory + tool calls แบบ real-time — [arize.com/phoenix](https://arize.com/phoenix) / [GitHub](https://github.com/Arize-ai/phoenix)
- **Inspect AI** — eval framework จาก UK AI Safety Institute, เน้น trajectory + sandboxed tool execution — [GitHub](https://github.com/UKGovernmentBEIS/inspect_ai)
- **DeepEval** — eval แบบ pytest-style ใส่ CI pipeline ได้, รองรับ LLM-as-judge — [GitHub](https://github.com/confident-ai/deepeval)
- **Sequential Thinking MCP Server** — official MCP server เสริม structured multi-step reasoning ไม่ต้องพึ่ง memory server — [GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking)

## Next step (กำลังทำต่อ)

มอสเลือก **Langfuse / Arize Phoenix** ให้สำรวจจริงจังว่าติดตั้งกับ setup เรา (Claude Code + zcode/agy/grok เป็น subprocess CLI แยกกัน ไม่ใช่เรียกผ่าน SDK โดยตรง) ได้จริงไหม — ผลสำรวจจะบันทึกเป็นไฟล์แยกต่างหากเมื่อได้ข้อสรุป
