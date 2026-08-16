---
pattern: "When asked to convert a structured diagram file (drawio/mxGraph, similar XML) to HTML, parse the real node/edge data and render it (SVG + generic layout logic) rather than embedding a screenshot or an external viewer library"
date: 2026-08-10
source: "rrr: ayami-oracle"
concepts: [artifacts, svg, diagramming, csp, drawio, data-extraction]
---

# Render structured diagrams from their real data, not a screenshot or embedded viewer

## What happened

Asked to turn `batchMSMQ.drawio` (an uncompressed mxGraph XML file, 2 pages, ~90
nodes/edges) into HTML. Two tempting shortcuts existed: embed the official drawio
viewer via a `<script>` tag, or just screenshot the diagram and drop the image in an
`<img>`. Neither was viable — Artifacts run under a strict CSP that blocks external
script/CDN loads, and a screenshot isn't actually "HTML," it's an image wearing an
HTML extension.

Instead, read the full XML, transcribed every vertex (id, x/y/w/h, label, style/color)
and edge (source, target, explicit waypoints, label) into plain JS data arrays, then
wrote a small generic renderer: box/ellipse/text draw functions, an orthogonal-path
builder that uses real waypoints when the source data has them and falls back to a
simple 2-segment elbow otherwise, and a path-fraction interpolator for edge labels.
Result was a real, zoomable, theme-aware, self-contained HTML page that structurally
matches the source file — not a static picture of one.

## Why

A "convert X to HTML" request implicitly means the content should still *be* HTML —
inspectable, resizable, restyleable, accessible — not a raster image with an HTML
wrapper. For any file format that already encodes structure (mxGraph XML, most
diagram/CAD interchange formats, even well-formed SVG source), that structure is the
actual asset worth preserving. Screenshotting throws it away for no benefit; embedding
a viewer library either violates a sandboxed CSP or adds a dependency that may not
render identically later.

## How to apply

- Before defaulting to a screenshot or an embedded third-party viewer for a
  structured file format, check whether the format is human-readable/parseable
  (uncompressed XML, JSON, etc.) — mxGraph/.drawio files often are, unless base64+
  deflate-compressed (check for a bare `<mxGraphModel>` near the top vs. a single
  opaque blob).
- A generic data-driven renderer (nodes as objects, edges as source/target + optional
  explicit waypoints, one shared draw/route function) scales better than hand-writing
  SVG path strings per element, and is much less error-prone at diagram sizes beyond
  a handful of shapes.
- It's fine to approximate secondary details (e.g. edge-label exact pixel offset via
  midpoint-of-path instead of literal source coordinates) as long as the primary
  structure (boxes, connections, text, correct topology) is faithful — say so
  explicitly rather than presenting it as pixel-perfect.
