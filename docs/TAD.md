# Technical Architecture Document — Vigil

Status: Draft v1 — for review
Repo location (suggested): docs/tad.md
Companion doc: docs/prd.md — this document implements PRD v1 scope only.

---

## 1. System Overview

One repo, two services, one Postgres database, one public domain.

```
Shopify Admin (merchant's browser)
        |
        | embedded iframe, App Bridge session token
        v
  admin-ui (Node / React Router / Polaris)
        |
        | internal HTTP, docker-network only, never public
        v
  backend (Python / FastAPI)
        |
        |-- Postgres (Neon)               -- all persistent state
        |-- Shopify GraphQL Admin API      -- order/fulfillment reads
        |-- OpenRouter/Groq                -- AI reasoning + drafting
        |-- Resend                         -- outbound email

Shopify webhooks (orders/updated, fulfillments/update, GDPR, app/uninstalled)
        |
        | public HTTPS, HMAC-verified
        v
  backend (Python / FastAPI) -- same service, separate route group

Nginx reverse-proxies one public domain:
  /              -> admin-ui   (embedded UI, OAuth install)
  /webhooks/*    -> backend    (Shopify webhook receiver)
  everything admin-ui needs from backend goes over the docker-internal
  network, never through the public-facing routes
```

Two containers from two images (unlike Velvora's one-image-two-services pattern, since admin-ui and backend are genuinely different runtimes this time), same docker-compose + Nginx + Let's Encrypt + EC2 deployment shape already proven.

---

## 2. Component Responsibilities

**admin-ui (Node / React Router, Shopify-CLI scaffolded)**
- OAuth install flow via Token Exchange
- Embedding, App Bridge, session token issuance/verification
- Polaris UI: flagged-orders list, order detail, settings page
- On every page load, calls backend's internal API for data — holds no business logic and no direct DB or Shopify API access of its own

**backend (Python / FastAPI)**
- Owns the Postgres connection and all persistent state
- Owns all Shopify GraphQL Admin API calls (reads only in v1 — see Section 6)
- Receives and verifies Shopify webhooks
- Runs the in-process APScheduler safety-net poll (same "right-sized, no Celery" decision as prior projects)
- Owns the orchestrator/guardrails split: LLM reasons and drafts, deterministic code decides what counts as flagged and what's allowed to send
- Sends approved messages via Resend
- Exposes two API surfaces: an internal API (admin-ui only, docker-network) and the public webhook receiver (HMAC-verified)

This mirrors Velvora's `core/` `tools/` `integrations/` `persistence/` structure inside `backend/`, extended with `shop_id` scoping everywhere instead of assuming one store.

---

## 3. Data Flow — the Four Paths That Matter

**Install:** merchant clicks install → Shopify redirects to admin-ui's OAuth route → Token Exchange completes → admin-ui calls backend's internal API to persist the shop record and access token → backend registers the required webhooks with Shopify → merchant lands on the embedded dashboard.

**Detection:** Shopify fires `orders/updated` or `fulfillments/update` → backend verifies the HMAC signature → backend checks the deterministic rule (paid + unfulfilled past threshold) → if triggered, the prioritization/reasoning pass runs (order value, prior delays on this SKU/route, time past threshold) → LLM generates the explanation and draft message → row written to `flagged_orders` → audit log entry written. The APScheduler poll runs on an interval as a safety net, re-checking orders that should have triggered a webhook but didn't, to catch missed events.

**Approval:** merchant opens the dashboard (admin-ui calls backend's internal API for the current flagged list) → merchant approves, edits then approves, or dismisses → admin-ui calls backend's internal API with the decision → backend sends via Resend only on approve/edit-approve, never on dismiss → audit log entry written either way.

**Uninstall:** Shopify fires `app/uninstalled` → backend marks the shop record inactive, stops any further processing for that shop, retains data per the retention policy defined at Phase 8 (security pass), doesn't delete outright without checking GDPR webhook requirements first.

---

## 4. Internal API Contract (admin-ui to backend)

Draft shape, refined as Phase 2 actually builds it:

```
GET  /internal/shops/{shop_id}/flags          -> ranked list of flagged orders
GET  /internal/shops/{shop_id}/flags/{id}     -> single flag detail (explanation + draft)
POST /internal/shops/{shop_id}/flags/{id}/decision
     body: { action: "approve" | "edit_approve" | "dismiss", edited_message?: string }
GET  /internal/shops/{shop_id}/settings
PUT  /internal/shops/{shop_id}/settings
     body: { threshold_hours: int }
POST /internal/shops/install
     body: { shop_domain, access_token, scope }   -- called once, right after OAuth completes
```

Authenticated with a shared internal secret (not the merchant-facing session token — that's verified by admin-ui itself), and only reachable on the docker-internal network, never exposed through Nginx.

---

## 5. Database Schema — First Pass

All tables carry `shop_id`. Refined into real migrations at Phase 3; this is the shape to design against now.

```
shops
  id, shop_domain (unique), access_token (encrypted at rest),
  scope, installed_at, uninstalled_at (nullable)

settings
  shop_id (FK), threshold_hours (default 72), updated_at

flagged_orders
  id, shop_id (FK), shopify_order_id, order_number, customer_email,
  order_value, flagged_at, threshold_crossed_at, priority_score,
  ai_explanation, ai_draft_message, status
    (pending | approved | edited_approved | dismissed | sent),
  resolved_at, resolved_by

audit_log
  id, shop_id (FK), flagged_order_id (FK, nullable),
  event_type, event_data (jsonb), created_at

webhook_events
  id, shop_id (FK), shopify_webhook_id, topic, received_at
    -- idempotency guard; Shopify retries webhooks, this prevents
       double-processing the same event
```

---

## 6. Security — Initial Pass (full doc written at Phase 8)

- **OAuth scope: `read_orders` only for v1.** No write scope requested — the only outbound action is an email via Resend, not a Shopify mutation. This is both the correct minimal-privilege posture and it materially lowers app review friction.
- **Every webhook verified via HMAC-SHA256** (`X-Shopify-Hmac-Sha256` header) before any processing — unverified requests are rejected, not logged-and-ignored.
- **Session tokens (App Bridge JWTs) verified on every embedded request** — signature, `aud`, `exp`, `nbf` all checked, not just presence of a token.
- **Access tokens encrypted at rest**, never logged, never included in the dual-level file logging by default (console INFO / file DEBUG convention carries over, but access tokens are explicitly excluded from both levels).
- **Secrets via `.env`, excluded from git from commit one** — direct lesson from the Velvora `.env` screenshot exposure; this time `.gitignore` exists before the first secret does.
- **Rate limits:** GraphQL Admin API uses a cost-based bucket; backend needs to handle `THROTTLED` responses with backoff rather than assuming every call succeeds.

---

## 7. Non-Functional Notes

- Dual-level logging (console INFO, file always DEBUG) — same convention as prior projects, applied per-request with `shop_id` in every log line so multi-tenant logs are actually traceable.
- Conventional commits throughout.
- No Celery, no Redis queue for v1 — APScheduler in-process is sufficient at this scale, same reasoning as before; revisit only if real usage data says otherwise.

---

## 8. Open Questions Carried From PRD

- Default threshold (72h) — confirm.
- Whether GDPR webhook data-retention behavior on uninstall needs a hard delete or a soft-archive — needs a decision before Phase 3 migrations are finalized, not urgent today.