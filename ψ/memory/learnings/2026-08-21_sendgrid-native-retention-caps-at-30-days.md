---
pattern: "SendGrid's native Email Activity retention maxes out at 30 days even on paid plans — anything beyond that requires capturing events via the Event Webhook and storing them yourself. The Filter Messages API (GET /messages) is a query interface over that same short retention window, not a long-term archive."
date: 2026-08-21
source: "learn: https://www.twilio.com/docs/sendgrid/api-reference/email-logs/filter-all-messages"
concepts: ["sendgrid", "twilio", "email-logs", "retention", "api", "event-webhook"]
---

# Learned: SendGrid Email Logs API + retention limits

## Filter All Messages API (`GET /v3/messages`)
- Query syntax filters on `sg_message_id`, `subject`, `to_email`, `status`, `reason`, `categories` — operators `=`, `IN`, `>`, `<`, `>=`, `<=`, up to 160 conditions combined with `AND` (no nesting).
- `limit` param: 1–1000 results, default 10.
- Auth: Bearer API key.
- Response per message: `from_email`, `sg_message_id`, `subject`, `to_email`, `status` (processed/delivered/deferred/dropped/bounced/blocked), `reason`, `sg_message_id_created_at`.
- No retention info documented in the API reference itself — it just queries whatever SendGrid currently has stored.

## Retention by plan (confirmed via web search, not the API doc)
- Free: 3 days
- Essentials: ~7 days
- Pro (+ 30-Day Activity add-on, $10-15/mo): up to 30 days
- **No plan reaches 180 days natively.**

## Implication
For retention beyond SendGrid's own window (this project's ask: >180 days at ~450k emails/month), the only path is the **Event Webhook** (push-based, event-by-event as they happen) piped into your own storage (e.g. S3) — the Filter Messages API cannot be used to backfill history that SendGrid has already expired.
