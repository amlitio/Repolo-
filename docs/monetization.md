# Monetization

FIRIP's MVP scope (Risk + Water intelligence for Florida) maps to the
following customer segments and packaging. These are product-strategy
notes, not implemented billing code — there is no payment integration in
this repository yet.

## Segments

- **Government (county/municipal emergency management, planning, public
  works)** — county-wide risk dashboards, alert subscriptions for their
  jurisdiction, and the ability to export risk/flood data for grant
  applications and resilience planning. Likely sold as an annual seat or
  site license per county/agency.
- **Engineering & environmental consulting firms** — property and
  parcel-level risk scoring with full factor explanations, used in due
  diligence and resilience design work. Usage-based or per-seat.
- **Investors / lenders / insurers** — portfolio-level risk scoring across
  many properties/counties, likely via API access rather than the
  dashboard UI. API-call or portfolio-size based pricing.
- **Contractors** — procurement/opportunity intelligence once that module
  is activated (post-MVP); a logical upsell on top of a base risk
  subscription rather than a standalone product at launch.

## Packaging shape (proposed, not yet built)

| Tier | Audience | Includes |
| --- | --- | --- |
| Free / public | General public, journalists | Public map view, county-level risk grades, published weather alerts |
| Professional | Engineering firms, small government | Property-level scoring, saved searches, alert subscriptions, CSV export |
| Enterprise | Large government, insurers, lenders | API access, bulk/portfolio scoring, SSO, audit log export, SLA |
| Procurement add-on (post-MVP) | Contractors | Opportunity feed + ranking |

## Why this is deferred past the MVP gate

The task's own assumptions mark procurement/construction as
production-scaffolded but not the first acceptance gate, and billing
integration was not part of the Risk + Water MVP scope. Building payment
flows against a product surface that hasn't been validated with real
users would be premature; the database schema (`organizations`,
`memberships`, `roles`) is already shaped to support seat-based and
org-scoped billing later without a schema migration that breaks existing
data.
