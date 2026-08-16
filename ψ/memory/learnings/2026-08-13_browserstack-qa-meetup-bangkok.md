---
pattern: "Learned BrowserStack QA Meetup Bangkok (Aug 2026): Core Web Vitals/rendering-architecture tradeoffs (CSR vs Hydrated SSR vs Islands vs RSC+Streaming), and MCP security incidents (Asana cross-tenant leak, GitHub token exposure, Supabase SQL injection) with production safeguards (tenant isolation, input sanitization, per-request identity, audit logging)"
date: 2026-08-13
source: "learn: https://naiwaen.debuggingsoft.com/2026/08/browserstack-qa-meetup-group-bangkok-aug2026/"
concepts: ["learn", "qa", "testing", "web-performance", "mcp", "ai-agent-security", "browserstack"]
---

# Learned: BrowserStack QA Meetup Bangkok (Aug 2026)

**Event**: BrowserStack QA Meetup, Bangkok, 8 Aug 2026.

## Talk 1 — Modern Web Performance and Architecture (Nitish Mittal)
- Browser rendering pipeline: Parser → Styles → Layout → Painting → Composition. First 3 stages run on the CPU's single main thread — the bottleneck.
- Core Web Vitals: LCP (target <2.5s), TTFB, INP. Rule of thumb: >50ms main-thread blocking = perceptible lag.
- Four rendering architectures compared:
  - CSR — poor LCP
  - Hydrated SSR — better LCP, but INP suffers during hydration
  - Island Architecture — good for static-heavy sites (e.g. e-commerce)
  - React Server Components + Streaming — server render with progressive delivery

## Talk 2 — MCP in Practice: Secure AI Agents (Akhilesh S.)
- MCP = standardized interface for LLMs to reach personal context/tools; backed by Anthropic/Google/OpenAI under the Linux Foundation.
- Security timeline: OAuth 2.1 compliance landed 2025; 2026 saw first wave of enterprise MCP server deployments.
- Real incidents cited: Asana (2-week cross-tenant data leak), GitHub (private repo exposure via leaked tokens), Supabase (SQL injection via stored prompts).
- Recommended safeguards: tenant isolation, input sanitization, per-request identity verification, comprehensive audit logging.

## Key takeaway for QA practitioners
Test performance across real device diversity, not just dev machines; when integrating AI agents (MCP), test scope-based permissions and require audit logging as a QA gate, not an afterthought.
