---
pattern: never write a specific root-cause hypothesis into a report from a coarse-resolution chart alone — query the underlying data at native granularity first
date: 2026-08-22
source: rrr: ayami-oracle
concepts: [root-cause-analysis, monitoring, grafana, prometheus, verify-before-asserting, incident-investigation]
---

# Verify fine-grained data before writing root cause into a report

While investigating a VMware/Grafana weekly monitoring report, I published an Executive
Summary artifact claiming a CPU spike was "an isolated single-point spike... recommend
checking Task Scheduler/backup job" — based only on reading a 5-minute-bucketed chart
screenshot. When later asked to dig further, I queried the same metric at 15-second
resolution and found it was actually a real, sustained ~17-minute climb from ~50% to 93%
and back down — not a blip at all. The earlier framing was flatly wrong and had to be
walked back after it was already in a client-facing document.

**Why**: coarse-resolution dashboards (5-min buckets, daily charts) visually compress
sustained multi-minute events into what looks like a single point. A screenshot is
sufficient evidence for "something happened here," but never for a specific causal claim
("isolated," "scrape artifact," "scheduled task") — that requires the underlying time
series at native/fine granularity.

**How to apply**: before writing any "likely cause" or diagnostic hypothesis into a
document meant to inform real decisions (an incident report, a root-cause summary, an
Executive Summary artifact), pull the raw metric at the finest available resolution for
the exact incident window first. If fine-grained data isn't accessible, say "cause
unconfirmed, need fine-grained data" rather than offering a specific guess — a labeled
absence is more honest and more useful than a plausible-sounding wrong answer. See also
[[feedback_verify_before_asserting]] — this is the same pattern applied specifically to
monitoring/observability data, where the failure mode is subtler because the chart
*looks* like evidence even when its resolution hides the real shape of the event.

A related trap in the same session: don't transfer one host's confirmed root cause to a
different host/metric in the same report just because the explanations "feel similar" —
chronic sustained anomalies and one-off time-boxed incidents are different failure
classes. Check the second case's own data before reusing the first case's explanation.
