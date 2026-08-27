# Product Requirements Document — Vigil

Status: Draft v1 — for review
Owner: Usman Javaid
Repo location (suggested): docs/PRD.md

---

## 1. Overview

Vigil is an embedded Shopify app that watches order fulfillment in real time, flags orders at risk of turning into a support ticket or a bad review, explains why each one matters, drafts a customer-facing delay message, and sends nothing without merchant approval.

One-line pitch: "Vigil catches stuck orders before your customers have to complain about them."

---

## 2. Problem Statement

Fulfillment delays are one of the most common, most preventable causes of support tickets, refund requests, and negative reviews on Shopify stores. Merchants currently find out about a stuck order in one of two ways: a customer complains, or someone manually scrolls the orders list looking for anything that looks old. Neither scales past a small order volume, and both are reactive — the customer already had a bad experience by the time the merchant knows.

Existing tracking-page tools (AfterShip, Malomo, etc.) show status to the customer but don't proactively flag anything to the merchant or take any action. Nothing on the market reasons about *which* delayed orders actually matter most and drafts a response for a human to approve.

---

## 3. Target Users

**Primary:** mid-size Shopify merchants with enough order volume that fulfillment delays are a recurring, not occasional, cost — roughly the range where manually eyeballing the orders list stops being reliable.

**Secondary (future expansion, not v1):** COD-heavy regional merchants (Pakistan/South Asia/MENA), where delay communication has an outsized effect on return-to-origin rates. Noted here as a known future direction, not built in v1.

---

## 4. Goals & Success Criteria (v1 / demo-readiness bar)

Since v1 has no real usage data yet, these are correctness and trust bars, not growth metrics:

- 100% of orders crossing the configured paid+unfulfilled threshold are flagged in test data — no missed flags, ever.
- Zero customer-facing sends without explicit merchant approval. This is a hard requirement, not a target.
- Every flag, AI draft, and merchant decision (approve / edit / dismiss) is written to the audit log with no gaps.
- A merchant looking at the dashboard for the first time understands, without explanation, why each order is flagged and what will happen if they click approve.

---

## 5. User Stories

- As a merchant, I want to see which orders are at risk of becoming a support problem, so I find out before the customer complains.
- As a merchant, I want to know *why* an order was flagged, not just that it was — including why it's ranked more or less urgent than others.
- As a merchant, I want a ready-to-send message drafted for me, but I always want the choice to approve, edit, or dismiss it before anything goes out.
- As a merchant, I want to set what "delayed" means for my own store, since a 2-day threshold makes sense for some stores and not others.
- As a merchant, I want a record of everything the app has flagged and done, in case I need to check later.

---

## 6. Scope — In for v1

- Webhook-driven detection on `orders/updated` and `fulfillments/update` (no polling as the primary mechanism — see TAD for the background safety-net poll).
- Deterministic base rule: paid + unfulfilled past a merchant-configured threshold (default 72 hours).
- A prioritization/reasoning layer on top of the base rule: ranks flagged orders using order value, whether this SKU or shipping route has caused delays before, and how far past threshold the order is — output is a ranked, explained list, not a flat trigger. This is the core differentiator and is treated as in-scope for v1, not a stretch goal.
- AI-generated plain-language explanation for each flagged order.
- AI-drafted customer delay/ETA message per order.
- Merchant approval workflow: approve as-is, edit then send, or dismiss.
- Email send via Resend on approval.
- Per-shop configurable threshold (stored per tenant, not in `.env`).
- Full audit log of every flag, draft, and decision.
- Embedded Polaris dashboard: flagged-orders list, order detail view, settings page.

---

## 7. Scope — Explicitly Out for v1

- Stale-tracking detection (fulfilled but tracking hasn't moved) — real, valid, deferred to v1.1 once the core loop is proven.
- WhatsApp/SMS/Telegram channels — deferred; natural v2 expansion, especially toward COD-heavy regional merchants.
- Multi-store/agency rollup reporting.
- Any second agent type (retention, inventory, pricing, etc.) — Vigil stays single-purpose in v1.
- Billing/subscription logic — added at App Store submission phase, not before.
- Multi-language support.

---

## 8. Assumptions & Dependencies

- Shopify GraphQL Admin API (current version at build time) for order and fulfillment data — REST not used, per Shopify's own guidance for new apps.
- Resend for outbound email, reusing the integration pattern already proven in Velvora.
- Dev store `vigil-test.myshopify.com` for all testing until private beta.
- Postgres (Neon) for persistence, multi-tenant (`shop_id`-scoped) from day one — this is the structural difference from Velvora's single-tenant design.

---

## 9. Open Questions

- Default threshold: 72 hours proposed — confirm or adjust.
- Should v1 include a "snooze" action alongside approve / edit / dismiss, or is that v1.1?
- Public vs. unlisted App Store listing — decision deferred to Phase 12, not needed now.

---

## 10. Non-Goals (explicit, to protect scope)

Vigil is not trying to become a general operations dashboard, a general analytics tool, or a multi-agent platform in v1. Every feature request during the build should be checked against this document before being added — if it's not in Section 6, it's a v1.1+ conversation, not a v1 addition.