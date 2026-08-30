---
pattern: "4-part Thai System Design primer (blog.odds.team, by Boonsong Srithong) uses one running use case — a Gym App (membership, booking, payment, QR check-in) evolving Monolith → Modular Monolith → Distributed System — to connect Database/Storage, Core Infrastructure, Distributed Systems, and Communication/Reliability concepts into one coherent mental model instead of teaching them in isolation"
date: 2026-08-31
source: blog series: https://blog.odds.team (4 parts, see links below)
concepts: ["system-design", "database", "distributed-systems", "infrastructure", "messaging", "reference-material"]
---

# System Design Concepts Series (blog.odds.team) — สรุปย่อเก็บไว้อ้างอิง

ซีรีส์ 4 ตอน สอน System Design โดยใช้ **use case เดียวกันตลอด (Gym App)** ให้เห็นว่าแต่ละ concept เชื่อมกันยังไง
เหมาะเป็น reference กลับมาอ่านตอนต้องออกแบบระบบจริง ไม่ใช่ความรู้เฉพาะโปรเจกต์ไหน

## 1. Database & Storage — https://blog.odds.team/database-storage-concepts-system-design-simply-explained/
SQL/ACID, NoSQL, Index, Partitioning/Sharding, Replication, Cache patterns (Cache-Aside/Write-Through/
Write-Behind/Read-Through), Object Storage, Event Sourcing — **14 concepts รวม**
> ทุกโซลูชันเป็น trade-off ไม่มีคำตอบที่ดีที่สุดสำหรับทุกกรณี ต้องเลือกตาม access pattern จริง

## 2. Core Infrastructure — https://blog.odds.team/core-infrastructure-concepts-system-design-simply-explained/
Scaling (Vertical/Horizontal), Latency vs Throughput, CDN, DNS, Reverse Proxy/Load Balancer/API Gateway
> Use case: gym peak hour 18:00 จองคลาสยอดนิยม → เพิ่ม server หน้าไม่ช่วยถ้า bottleneck อยู่ที่ database;
Horizontal scaling บังคับให้ต้องทำ stateless design (Redis/JWT แทน local session)

## 3. Distributed Systems — https://blog.odds.team/distributed-systems-concepts-system-design-simply-explained/
CAP Theorem, Strong vs Eventual Consistency, Consensus, Leader Election, Idempotency Key, 2PC, Saga Pattern,
Clock Skew & Vector Clock
> ใช้วิวัฒนาการ gym app: Monolith → Modular Monolith → Distributed System เป็นเส้นเรื่อง

## 4. Communication & Reliability — https://blog.odds.team/communication-concepts-system-design-simply-explained/
API protocols (SOAP/REST/gRPC/GraphQL), Async (Message Queue/Pub-Sub/DLQ/Backpressure), Real-time
(WebSocket/SSE), Webhook, Reliability (Circuit Breaker/Rate Limiting/Load Shedding), Bloom Filter,
AI integration (Embedding/RAG/MCP)
> ตัวอย่าง: จองคลาสไม่ควรเรียก Notification/Analytics/Reminder แบบ synchronous — ส่งผ่าน message queue แทน
> มี table เปรียบเทียบข้อดี/trade-off ของแต่ละ pattern ชัดเจน — ใช้เป็น cheat sheet ได้เลย

## เกี่ยวข้องกับงานที่ทำอยู่

Concept กลุ่ม Communication (โดยเฉพาะ RAG/MCP) เชื่อมกับสิ่งที่กำลังเรียนรู้เรื่อง Agent Skills/MCP
ในเซสชันนี้โดยตรง — MCP ถูกนิยามในบทความว่า "มาตรฐานเชื่อม AI Application เข้า Tool/ข้อมูลภายนอก"
ตรงกับ Agent Skills architecture ที่เพิ่งอ่านไป ([[2026-08-31_anthropic-agent-skills-official-docs]])
