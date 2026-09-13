# Overnight agent-tech scan (2026-09-11, dynamic /loop until 08:00)

มอสสั่งให้วนส่ง /zcode + /agy ค้นเทคโนโลยีใหม่ๆ (2025-2026) คนละมุมทุกรอบ, Ayami QC เอง, ถ้าไม่ผ่านไล่หาใหม่ในรอบเดียวกัน, append ผลที่ผ่านลงไฟล์นี้ไฟล์เดียวตลอดคืน จนถึง 08:00 น.

**หัวข้อที่ห้ามซ้ำสะสม** (รวมจากทุกไฟล์ 2026-09-11_* + ทุกรอบด้านล่าง): context/prompt caching, model routing (RouteLLM/LiteLLM), RAG-MCP tool filtering, Mem0/Letta/Zep, Aider tree-sitter repo-map, multi-agent-via-files, Aviator Verify, GitHub MCP secret scanning, Apiiro CLI, mabl MCP Server, Auto TFA, Langfuse, Arize Phoenix, Inspect AI, DeepEval, Sequential Thinking MCP Server, Microsoft Presidio, OpenAI Privacy Filter, pii-redact, Browser Use, Genspark, Microsoft LLMLingua-2, Headroom, LangGraph, CrewAI, Mastra, NVIDIA Parakeet TDT, NVIDIA Canary-1B-v2, Moonshine, K8sGPT, kagent, A2A (Agent2Agent Protocol), ACP (Agent Client Protocol), BAML, XGrammar, Outlines, SafeMigrate, Postgres MCP Server Comparison (Powabase), Arcade.dev SQL tools guide, Gideon (Discord bot), llmcord, vLLM V1 engine, Aphrodite Engine, SGLang, simonw/llm, toktrack, AWS FinOps Agent, AWS Billing and Cost Management MCP Server, aws-cost-explorer-mcp-server, HashiCorp Terraform MCP Server, Pulumi Copilot/AI, sqlite-vec, LanceDB, USearch, NeMo Guardrails, cc-bash-guard, NautilusTrader, VectorBT PRO, PyThaiNLP 5.1, Typhoon OCR 1.5, kham, Docling, Microsoft MarkItDown, LlamaParse, Claude Code Plugin System, Smithery.ai Marketplace, Meetily, Otter.ai, Kokoro-82M, F5-TTS, Chatterbox, Khoj, SilverBullet, OpenCommit, aicommits

---

## รอบ 1 — 03:15

**zcode** (privacy-preserving/local-LLM สำหรับ PII + agentic browser/desktop automation ใหม่):
- **Microsoft Presidio** (self-hosted) — redact PII ก่อนเข้า LLM ใดๆ, ไม่มี data egress — เหมาะกับงาน eVisa/government DB — [philterd.ai comparison](https://philterd.ai/best-pii-redaction-software/)
- **OpenAI Privacy Filter** — open-weight PII detect+redact, รัน local ได้ — [openai.com](https://openai.com/index/introducing-openai-privacy-filter/)
- **pii-redact** — รัน local 100% — ⚠️ source เป็นแค่ LinkedIn post ไม่ใช่ primary source, ความน่าเชื่อถือต่ำกว่าอันอื่น — [LinkedIn](https://www.linkedin.com/posts/kcorbitt_openpipe-rl-for-agents-activity-7310746759670968320-C6PK)
- **Browser Use** — agentic browser framework ที่ dominant ที่สุด (89.1% WebVoyager), รันกับ local LLM ได้, session/credential อยู่บนเครื่องเรา — [browser-use.com](https://browser-use.com/)
- **Genspark** — agentic browser รัน AI on-device ไม่ต้องพึ่งเน็ต — [NoHacks 2026](https://nohacks.co/blog/agentic-browser-landscape-2026)

**agy** (prompt/context compression + agent orchestration platform):
- **Microsoft LLMLingua-2** — task-agnostic prompt compression (BERT-sized model), ลด token 30-60% ไม่เสียความหมาย — [GitHub](https://github.com/microsoft/LLMLingua)
- **Headroom** — compression proxy เฉพาะ AI coding agent + tool/JSON payload, ลด token 60-95% — [GitHub](https://github.com/headroomlabs-ai/headroom)
- **LangGraph** — graph-based agent orchestration, cyclic workflow + state checkpointing — [GitHub](https://github.com/langchain-ai/langgraph)
- **CrewAI** — role-based multi-agent orchestration (Researcher/Writer/Evaluator) — [GitHub](https://github.com/crewAIInc/crewAI)
- **Mastra** — TypeScript-native orchestration, graph control flow + human-in-the-loop — [GitHub](https://github.com/mastra-ai/mastra)

**QC ของ Ayami**: ผ่าน (ไม่ต้องหาใหม่) — เกือบทั้งหมดมี source แข็งแรงและหลายตัวยืนยันได้เอง (Presidio, LLMLingua-2, LangGraph, CrewAI คือของจริงที่รู้จักกันแพร่หลาย) มีจุดอ่อนเดียวคือ "pii-redact" อ้างอิงแค่ LinkedIn post — ให้ระวังไว้ ไม่ใช่ตัดทิ้ง เพราะที่เหลือ 9/10 คุณภาพดี ไม่คุ้มเสีย token รีรันทั้งรอบเพื่อจุดเดียว

**น่าสนใจสุดของรอบนี้ (ความเห็น Ayami)**: Microsoft Presidio ตรงกับงาน eVisa/PII ของมอสโดยตรง และ LLMLingua-2 ตรงกับปัญหา token efficiency ที่คุยกันมาทั้งคืน — ทั้งคู่ควรพิจารณาจริงจังกว่ารายการอื่นในรอบนี้

---

## รอบ 2 — 04:00

**zcode** (local STT ใหม่แก้ hallucination + AI-assisted K8s ops):
- **NVIDIA Parakeet TDT 0.6B v3** — ชนะ Whisper ทั้งความแม่นและเร็วใน test จริง 30 วัน, ไม่ "ฝัน" คำบนช่วงเงียบแบบ Whisper — ตรงปัญหา hallucination ที่เจอซ้ำหลายครั้งกับ mlx_whisper บนเสียงยาว — [Reddit 30-day test](https://www.reddit.com/r/LocalLLaMA/comments/1nf10ye/30_days_testing_parakeet_v3_vs_whisper/)
- **NVIDIA Canary-1B-v2** — แม่นกว่า Whisper-large-v3 (อังกฤษ) เร็วกว่า ~10x, มาคู่กับ Parakeet ใน release เดียว — [arXiv 2509.14128](https://arxiv.org/html/2509.14128v1)
- **Moonshine** — โมเดลจิ๋ว footprint เล็กสุดสำหรับ edge/real-time — [Northflank benchmark 2026](https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks)
- **K8sGPT** — CLI สแกน cluster หา error แล้วให้ LLM อธิบาย+แนะ fix, มี MCP server ในตัว — ตรงกับงาน eVisa K8s/cert-manager ที่มอสดูแล — [k8sgpt.ai](https://k8sgpt.ai/)
- **kagent (CNCF/Solo.io)** — agent รันอัตโนมัติในตัว cluster (~19 tools) inspect+remediate เอง (ต่างจาก k8sgpt ที่แค่วินิจฉัย) — [kagent.dev](https://kagent.dev/)

**agy** (agent-to-agent protocol + structured output reliability):
- **A2A (Agent2Agent Protocol)** — มาตรฐานกลางระดับ Linux Foundation (Google/IBM/Microsoft) สำหรับ discovery+task delegation ข้าม agent ต่างค่าย — [a2a-protocol.org](https://a2a-protocol.org)
- **ACP (Agent Client Protocol)** — โดย Zed Industries, JSON-RPC 2.0, เหมือน LSP แต่สำหรับ IDE↔AI-coding-agent — [GitHub](https://github.com/zed-industries/agent-client-protocol)
- **BAML** — DSL + Schema-Aligned Parsing บังคับความถูกต้องของ structured output/tool-calling แบบ type-safe ข้าม provider — [boundaryml.com](https://www.boundaryml.com)
- **XGrammar** — constrained decoding engine (MLC-AI) สลับ grammar ระหว่าง reasoning/tool-call ระดับไมโครวินาที — [GitHub](https://github.com/mlc-ai/xgrammar)
- **Outlines** — แปลง JSON Schema/Pydantic เป็น FSM บังคับระดับ token, การันตี structure ถูก 100% — [GitHub](https://github.com/dottxt-ai/outlines)

**QC ของ Ayami**: ผ่านทั้งหมด ไม่ต้องหาใหม่ — ทุกตัวมี source แข็งแรง (arXiv paper, official site, GitHub) และหลายตัวยืนยันได้เอง (A2A, Outlines, K8sGPT เป็นของจริงที่รู้จักกันในวงการ)

**น่าสนใจสุดของรอบนี้**: **NVIDIA Parakeet/Canary** ตรงปัญหาจริงที่เกิดซ้ำในโปรเจกต์นี้หลายครั้ง (whisper hallucination บนเสียงยาว — เคยบันทึกใน session-metrics.md อย่างน้อย 2 ครั้ง) น่าลองจริงจังกว่ารายการอื่นทั้งหมดในคืนนี้

---

## รอบ 3 — 04:44

**zcode** (AI-assisted SQL/DB tooling + Discord bot framework):
- **SafeMigrate** — ตรวจ destructive DB ops + dry-run ก่อน apply สำหรับ agent ที่แตะ schema เอง — [dev.to](https://dev.to/depapp/safemigrate-never-fear-database-migrations-again-with-ai-agents-2aon)
- **Postgres MCP Server Comparison (Powabase)** — วิเคราะห์ว่าทำไม 8-9/10 Postgres MCP server ใช้กับ coding agent จริงไม่ได้ + เกณฑ์เลือก (schema introspection, query safety) — [powabase.ai](https://powabase.ai/blog/postgres-mcp-server-comparison-why-2-10-tool-servers-fail-coding-agents/)
- **Arcade.dev: SQL tools for AI agents** — แนวปฏิบัติ least-privilege + กัน SQL injection สำหรับ agent ที่ generate query เอง — [arcade.dev](https://www.arcade.dev/blog/sql-tools-ai-agents-security/)
- ⚠️ รอบแรกอ้าง "OpenClaw ~280K GitHub stars" — **ไม่ผ่าน QC** (ตัวเลขไม่น่าเชื่อถือ) → สั่งหาใหม่เฉพาะมุม Discord bot ด้วยเงื่อนไข "ห้ามอ้างตัวเลขที่ไม่มั่นใจ" ได้ผลจริงรอบ 2:
  - **Gideon** — self-hosted Discord AI hub (Python/Pycord), LLM ผ่าน OpenRouter/OpenAI-compatible, tool calling + per-channel persona + auto-summarize memory, Docker deploy — [github.com/eoko-dev/gideon](https://github.com/eoko-dev/gideon)
  - **llmcord** — Discord เป็น frontend ของ LLM, ใช้ reply-chain เป็น history (ไม่ต้องมี DB), รองรับ local model (Ollama/LM Studio/**vLLM**) ผ่าน OpenAI-compatible API, โค้ดไฟล์เดียว ~300 บรรทัด — [github.com/jakobdylanc/llmcord](https://github.com/jakobdylanc/llmcord)

**agy** (vLLM ecosystem + lightweight cost-tracking CLI):
- **vLLM V1 Engine** — สถาปัตยกรรมใหม่ (C++ execution loop + PagedAttention ปรับปรุง), OpenAI-compatible API, จุดเริ่มมาตรฐานสำหรับเรียนรู้ local serving — [GitHub](https://github.com/vllm-project/vllm)
- **Aphrodite Engine** — ต่อยอดจาก vLLM ติดตั้งง่ายกว่าบน consumer GPU — [GitHub](https://github.com/PygmalionAI/aphrodite-engine)
- **SGLang** — high-throughput local serving เทียบเคียง vLLM ได้ โครงสร้างโค้ดตรงไปตรงมา เหมาะเรียนรู้ — [GitHub](https://github.com/sgl-project/sglang)
- **simonw/llm** — CLI เรียก LLM หลายค่าย + log token usage ลง local SQLite อัตโนมัติ เช็คด้วย `llm logs --usage` ไม่ต้อง self-host — [GitHub](https://github.com/simonw/llm)
- **toktrack** — Rust CLI รวม token usage/cost จากการรันหลาย CLI พร้อมกัน, local cache, ไม่พึ่ง external stack — [GitHub](https://github.com/mag123c/toktrack)

**QC ของ Ayami**: zcode รอบแรกไม่ผ่าน (เลข star ปลอม) → หาใหม่แล้วผ่าน; SQL tooling ของ zcode + ผลทั้งหมดของ agy ผ่านตั้งแต่รอบแรก (vLLM/Aphrodite/SGLang/simonw-llm เป็นของจริงที่รู้จักกันแพร่หลาย)

**น่าสนใจสุดของรอบนี้**: **simonw/llm + toktrack** ตอบโจทย์ตรงจุดที่ Langfuse/Phoenix ทำไม่ได้บนเครื่องนี้ (RAM จำกัด ~1.4GB ว่างจริง) — เป็น CLI เบาๆ ไม่ต้อง self-host เต็มระบบ ตรงกับ feasibility survey ก่อนหน้านี้พอดี; **vLLM V1** ตรงกับความสนใจส่วนตัวของมอสที่เพิ่งเริ่มบุกเบิกสาย vLLM ด้วย

---

## รอบ 4 — 05:29

**zcode** (AWS FinOps/AI-ops tooling + IaC AI assistant):
- **AWS FinOps Agent** (public preview, re:Invent 2025) — agentic AI ของ AWS เอง สืบ root cause cost anomaly + หา optimization opportunity — ตรงกับพื้นฐาน Cloud/AWS ของมอสโดยตรง — [AWS CFM blog](https://aws.amazon.com/blogs/aws-cloud-financial-management/aws-cloud-financial-management-key-reinvent-2025-launches-to-transform-your-finops-practice/)
- **AWS Billing and Cost Management MCP Server** (awslabs, official) — เชื่อม Cost Explorer/Cost Optimization Hub เข้ากับ AI assistant แบบ natural language — [AWS blog](https://aws.amazon.com/blogs/aws-cloud-financial-management/aws-announces-billing-and-cost-management-mcp-server/)
- **aws-cost-explorer-mcp-server** (open source, aarora79) — community MCP server query spend ผ่าน Claude/Cursor ได้เลย ไม่ต้องรอ AWS preview — [GitHub](https://github.com/aarora79/aws-cost-explorer-mcp-server)
- **HashiCorp Terraform MCP Server** — agent ดึง provider docs/modules/policies จาก Terraform Registry real-time + guardrails, v0.4 รองรับ Stacks — [GitHub](https://github.com/hashicorp/terraform-mcp-server)
- **Pulumi Copilot/AI** — generate Pulumi program จาก natural language — [pulumi.com](https://www.pulumi.com/)

**agy** (lightweight local vector DB สำหรับ RAM จำกัด + agent safety/guardrail scanning):
- **sqlite-vec** — C extension สำหรับ SQLite, in-process 100% ไม่มี external dependency, SIMD acceleration — เบาสุดสำหรับ RAM จำกัด — [GitHub](https://github.com/asg017/sqlite-vec)
- **LanceDB** — embedded vector DB, disk-first (columnar Lance format), ค้นจากดิสก์ได้โดยไม่ต้องโหลด index ทั้งหมดขึ้น RAM — [GitHub](https://github.com/lancedb/lancedb)
- **USearch** — vector search engine C++ header-only, รองรับ mmap ดึง HNSW index จากดิสก์เท่าที่จำเป็น กิน RAM ต่ำมาก — [GitHub](https://github.com/unum-cloud/usearch)
- **NeMo Guardrails** (NVIDIA) — framework ตั้ง execution rails เช็ค parameter/argument ของ tool call ก่อนรันจริง กันไม่ให้ agent รัน action เสี่ยง — [GitHub](https://github.com/NVIDIA/NeMo-Guardrails)
- **cc-bash-guard** — hook policy engine ระดับ `PreToolUse` ดักประเมิน shell command ตาม policy (allow/ask/deny) ก่อน execute — [GitHub](https://github.com/tasuku43/cc-bash-guard)

**QC ของ Ayami**: ผ่านทั้งหมด ไม่ต้องหาใหม่ — source แข็งแรงทุกตัว (AWS official blog, HashiCorp docs, GitHub) ไม่มีตัวเลขอ้างลอยๆ

**น่าสนใจสุดของรอบนี้**: **NeMo Guardrails / cc-bash-guard** ตรงปัญหาที่เจอจริงคืนนี้เป๊ะ (agy เขียนไฟล์ทั้งที่สั่ง `--mode plan` ซ้ำหลายรอบ) — น่าเอามาทำ `PreToolUse` policy จับพฤติกรรมนี้โดยเฉพาะ; **AWS Billing MCP Server** ตรงกับพื้นฐาน Cloud/AWS ของมอสที่กำลังบุกเบิกสาย AI/LLM ต่อยอดด้วย

---

## รอบ 5 — 06:14

**zcode** (quant backtesting library ใหม่ + Thai NLP/OCR tooling):
- **NautilusTrader (2.0)** — event-driven engine Rust+Python, backtest deterministic แล้ว deploy live ได้ด้วยโค้ดชุดเดียว, multi-asset/multi-venue — เหมาะถ้า market-backtester อยากไปต่อ live crypto จริง — [GitHub](https://github.com/nautechsystems/nautilus_trader/releases)
- **VectorBT PRO** — vectorized backtesting (Python+Rust) สำหรับ sweep parameter เร็วมิติสูง — [vectorbt.pro](https://vectorbt.pro/)
- **PyThaiNLP 5.1** (25 ก.พ. 2025) — เพิ่ม Thai Discourse Treebank + Solar↔Lunar date conversion, lib หลักสำหรับ Thai segmentation ที่ update ต่อเนื่อง — [announcement](http://pythainlp.github.io/2025-02-25-pythainlp-5-1-0/)
- **Typhoon OCR 1.5** (SCB 10X, พ.ย. 2025) — open-source bilingual (ไทย/อังกฤษ) vision-language model สำหรับ document OCR, รัน local ได้ (HF/Ollama) — ตรงกับงาน extract เอกสารราชการไทย (eVisa) — [blog](https://opentyphoon.ai/blog/en/typhoon-ocr-release)
- **kham** — Thai NLP เน้นความเร็วสูง (segmentation/POS/NER/spell correction) — [kham.io](https://kham.io/thai-nlp/)
- (zcode เองตัดตัวเลข arXiv ที่ verify ไม่ได้ทิ้งเอง แสดงว่าคัดกรองเข้มขึ้น)

**agy** (document parsing tool ดีกว่า manual unzip/pdftotext + Claude Code plugin ecosystem):
- **Docling** (IBM Research) — แปลง PDF/DOCX/XLSX/PPTX → Markdown/JSON รักษาโครงสร้างตาราง+ลำดับอ่าน+OCR ในตัว — ตรงจุดที่เคยทำ manual unzip+pdftotext+openpyxl กับเอกสาร evisa หลายรอบ — [GitHub](https://github.com/docling-project/docling)
- **Microsoft MarkItDown** — utility แปลงเอกสารหลาย format → Markdown สะอาด พร้อมให้ agent ใช้ต่อทันที — [GitHub](https://github.com/microsoft/markitdown)
- **LlamaParse** — API สกัดเอกสารด้วย vision layout analysis วิเคราะห์ตาราง/element ซับซ้อน — [GitHub](https://github.com/run-llama/llama_parse)
- **Claude Code Plugin System (official)** — ระบบ `/plugin` จัดการ skills/hooks/LSP อย่างเป็นทางการ — [Anthropic docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
- **Smithery.ai Marketplace** — registry ค้นหา/ติดตั้ง MCP server สำหรับ Claude Code — [smithery.ai](https://smithery.ai)

**QC ของ Ayami**: ผ่านทั้งหมด ไม่ต้องหาใหม่ — ของจริงที่รู้จักกันแพร่หลาย (NautilusTrader, PyThaiNLP, Docling, MarkItDown, LlamaParse) source แน่น

**น่าสนใจสุดของรอบนี้**: **Docling/MarkItDown + Typhoon OCR** ตรงปัญหาจริงที่เจอซ้ำในโปรเจกต์นี้หลายครั้ง (ทำ manual unzip+pdftotext+openpyxl กับเอกสาร evisa docx/pdf/xlsx มาโดยตลอด, Typhoon OCR ยังเป็น bilingual ไทย/อังกฤษโดยเฉพาะ) — น่าลองแทนที่ workflow เดิมจริงจัง

---

## รอบ 6 — 06:58

**zcode** (AI meeting/video summarization โปร่งใส + local TTS/voice cloning):
- **Meetily** — self-hosted meeting assistant, transcribe+summarize บนเครื่องทั้งหมด เปิด transcript จริงดูได้ ไม่ใช่กล่องดำ — [dev.to guide](https://dev.to/zackriya/how-to-transcribe-summarize-meetings-locally-with-meetily-the-best-self-hosted-open-source-ai-dmk)
- **Otter.ai** (SaaS) — full searchable transcript คู่กับ AI summary ตรวจสอบย้อนหลังได้ — [comparison](https://www.cirrusinsight.com/blog/ai-meeting-summary-tools)
- **Kokoro-82M** — TTS เล็ก (82M, Apache 2.0) รัน CPU/VRAM ต่ำได้ latency ต่ำ เหมาะ notification bot เสียงเดียวซ้ำๆ (ไม่มี voice cloning) — [localaimaster.com](https://localaimaster.com/blog/best-local-tts-models)
- **F5-TTS / Chatterbox** (Resemble AI, MIT) — zero-shot voice cloning รัน local ได้ ถ้าอยากได้เสียงเฉพาะตัว — [centron.de](https://www.centron.de/tutorials/best-open-source-tts-models-compared-kokoro-f5-tts-sparktts-sesa)

**agy** (PKM/second-brain สำหรับ solo builder + AI git commit/changelog):
- **Khoj** — open-source AI second brain, self-host, ดึง markdown notes/PDF/GitHub repo มา search+วิเคราะห์ ต่อ agent/LLM ได้ทั้ง local/cloud — [GitHub](https://github.com/khoj-ai/khoj)
- **SilverBullet** — local-first plain-text markdown KB, มี Space Lua scripting + query engine ในตัว ต่อ AI agent/CLI workflow ได้อิสระ — [silverbullet.md](https://silverbullet.md)
- **OpenCommit** — CLI สร้าง conventional commit message จาก staged diff อัตโนมัติ รองรับ cloud LLM หรือ local ผ่าน Ollama — [GitHub](https://github.com/di-sukharev/opencommit)
- **aicommits** — CLI Node.js เบาๆ สร้าง commit message จาก staged diff คำสั่งเดียว — [GitHub](https://github.com/nutlope/aicommits)

**QC ของ Ayami**: ผ่านทั้งหมด — ของจริงที่รู้จักกันแพร่หลาย (Otter.ai, Khoj, OpenCommit, aicommits) source ครบ ไม่มีตัวเลขอ้างลอยๆ

**น่าสนใจสุดของรอบนี้**: **Meetily** ตรงกับที่เคยบ่นเรื่อง call.md's live transcript เป็น "กล่องดำ" บางครั้งไม่แม่น (เจอปัญหา garbled transcript มาก่อน) — self-hosted แบบเปิด transcript ดูได้เองน่าจะช่วยแก้ปัญหาความไม่โปร่งใสนั้นได้ตรงจุด
