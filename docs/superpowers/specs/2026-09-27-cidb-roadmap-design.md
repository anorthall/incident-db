# CIDB Roadmap: From Search Box to Incident Database

**Date:** 2026-09-27
**Status:** Approved design; implementation not started
**Scope:** Application code, migrations, tests and documentation in this repository.
Deployment (`deploy/`, `tf/`, compose files, Caddy, deploy workflows) is owned separately
and is out of scope; see [Deployment dependencies](#deployment-dependencies).

## 1. Purpose

CIDB today is a search box over the digitised *American Caving Accidents* archive. This
document defines the target state — a browsable, filterable, downloadable incident database
with a light editor workflow — and a phased roadmap to reach it. Each phase ships on its own,
leaves the live site working at every merge, and builds on shared seams so later phases
cannot regress earlier ones.

The primary audience is the general public: cavers, grotto safety officers and NSS members.
Success means a caver can answer "what goes wrong in vertical caving in Tennessee?" without
knowing search syntax, and can take the answer away as a spreadsheet. Researchers and editors
are served by the same work, not by separate tracks.

## 2. Current state

### Backend

Django 6.0 with django-ninja under `/api/v1`, Postgres 18, Python 3.14, strict mypy.

Public endpoints: `incidents/search` (Postgres full-text search plus `icontains` on cave and
tag names; five sort modes; no filters), `incidents/suggestions`, `incidents/did-you-mean`,
`incidents/click`, `incidents/{id}`, `reports/` (feedback submission). Staff endpoints under
`EditorAuth`: feedback list, detail and resolve.

The domain model is richer than the API exposes: `Person`/`IncidentPerson`/`Injury`, a
`GeographicArea` tree, `Location` with latitude/longitude, `Publication`/`Document`/
`SourceExtract`, `Tag`, `DuplicateGroup`, `IncidentEmbedding` (1536-dimension float array,
used only by the duplicate detector) and the `DataOperation` LLM pipeline.

`Incident.search_vector` is maintained by a Postgres trigger. `Incident.date` is an
`ImpreciseDateField` — a `CharField` holding strings such as `2015-summer` — so there is no
sortable or range-filterable date column. `Incident` has no status field; everything in the
table is public. Editing happens in Django admin (unfold).

Search logic (filtering, ranking, sorting, pagination) lives inline in the endpoint function.

### Frontend

React 19, Vite, TypeScript, shadcn/ui, TanStack Query, React Router 7. Routes: `/`,
`/incidents/:id`, `/privacy`, `/staff/login`, `/staff/feedback`, `/staff/feedback/:id`.

`src/lib/api.ts` is a hand-written 500-line fetch client whose TypeScript interfaces mirror the
Ninja schemas by hand. `SearchPage.tsx` is 400 lines combining the landing hero, a typing
animation, infinite scroll, a table-view hint, sort state and staff "commands" typed into the
search box. Filters do not exist; sort state is component state, not URL state.

### Operations

A single EC2 instance runs the API in Docker; the SPA is served from S3 behind CloudFront.
There is no task queue or worker. `incidents_export.sql` already denormalises incidents for
CSV export. `TODO.md` holds a backlog of hygiene items from a code audit.

## 3. Requirements

### Public

1. **Search.** Free-text search combining keyword and semantic ranking, with filters: tags,
   country, state, region, cave, year range, injury type, publication, and "has location".
   Facet counts update with the current query. Every search state is a shareable URL.
2. **Explore.** Browse pages for state/region, cave, tag, year and publication, each a
   filtered list with counts at a crawlable URL. A statistics dashboard (incidents over time,
   by tag, by state, by injury type, age distribution) that respects the active filters. A
   clustered map of geocoded incidents, synced to the same filters.
3. **Incident page.** As today, plus people involved (age and injuries as published; no
   additional personal detail), related incidents, source publication, and a "report a
   problem" affordance that pre-fills feedback with the incident.
4. **Downloads.** Export the current result set as CSV or JSON (capped and streamed).
   Versioned full-dataset snapshots (CSV, JSON and a schema description) with a citation
   string and a page listing available versions.

### Editors

5. **Light in-app editing.** Users with `is_editor` can edit title, summary, date, cave,
   location, tags and analysis from the incident page. Every change produces an audit record
   (editor, timestamp, per-field before and after). Editors can view an incident's revision
   history. Structural edits (people, references, sources, duplicates) remain in Django admin.
6. **Feedback triage.** The existing list/detail/resolve flow, plus resolving feedback from the
   incident it concerns, linking a resolution to the revision that fixed it, and a pending
   count in the sidebar.

### Non-functional

7. API changes under `/api/v1` are additive only. The OpenAPI schema is committed and
   frontend types are generated from it.
8. Search, browse, stats, map and export share one filter specification and one queryset
   builder.
9. Each phase is deployable on its own and the live site works at every merge. Slices are
   additive, so no feature flags are needed.
10. Strict mypy, ruff, `tsc`, eslint and vitest stay green. New backend behaviour has
    factory-based tests; new UI features have component tests against a mocked API.
11. Background work (embedding refresh, snapshots, sitemap) runs through `django.tasks`, never
    in a request.
12. Nothing in scope touches deployment. Infrastructure needs are recorded as dependencies for
    the deployment owner.

### Out of scope

Public API commitments or API keys; per-incident PDF or print output; a full incident editor
replacing Django admin; an approval or publish workflow; public user accounts; server-side
rendering; an end-to-end browser test suite.

## 4. Backend architecture

### 4.1 Query layer

New package `cidb/src/incidents/queries/`:

- `filters.py` — `IncidentFilters`, a Ninja `FilterSchema` with fields `q`, `tags`,
  `countries`, `states`, `regions`, `caves`, `year_from`, `year_to`, `injuries`,
  `publications`, `has_location`. Ninja parses it from query parameters; Python code (browse
  pages, exports, tasks) constructs it directly. It is the single definition of "a subset of
  incidents".
- `incidents.py` — `IncidentQuery` with `base()` (the optimised queryset with `select_related`
  and `prefetch_related`), `apply(filters)`, `order(sort, direction)`, `facets(filters)`
  (counts per dimension), `aggregate(filters, group_by)` (rows for stats) and
  `points(filters)` (id, title, latitude, longitude for the map).
- `ranking.py` — full-text rank, popularity boost and vector similarity, combined by
  reciprocal rank fusion for `sort_by=relevance`.

Endpoints parse input, call the query layer and serialise. The rule enforced in review: no
code outside `queries/` builds an `Incident` queryset for a public response.

### 4.2 Sortable dates

`Incident` gains `date_start` and `date_end` (`DateField`, null) and `date_year`
(`SmallIntegerField`, null), derived from the imprecise date in `save()` and backfilled by a
data migration. All three are indexed. Filters, sorting and stats use them; the imprecise
string remains the source of truth and the display value. This mirrors the existing pattern
for `search_vector`: a derived column beside a canonical one.

### 4.3 Vectors and hybrid search

`IncidentEmbedding.embedding` becomes a `pgvector` `VectorField(dimensions=1536)` with an HNSW
cosine index, via the `pgvector` Python package's Django integration. The migration adds the
extension, adds the new column, copies the array data, drops the array column and builds the
index.

`/incidents/{id}/related` returns the nearest neighbours by cosine distance, excluding the
incident itself. Hybrid relevance ranking fuses the full-text rank and the cosine distance to
the query embedding. Embeddings refresh through a task when `title`, `report` or `analysis`
change.

### 4.4 Background work

Django 6's `django.tasks` API with the `django-tasks` database backend. Tasks live in
`cidb/src/incidents/tasks/`: `refresh_embedding(incident_id)`, `build_dataset_snapshot()`,
`build_sitemap()`. Tests run with the immediate backend. Because task code is written against
the framework API, the backend can be switched to Redis-based by settings alone if load ever
warrants it.

### 4.5 Exports

Package `cidb/src/incidents/exports/`:

- `row.py` — `IncidentExportRow`, a Pydantic model defining the flat export shape. It follows
  the column set of `incidents_export.sql`, which is retained as documentation of the schema
  but not executed at runtime. Multi-valued relations are joined with ` || ` between records
  and `; ` within a record, as the SQL does today.
- `writers.py` — CSV and JSON writers that stream rows from a queryset.

`/incidents/export?format=csv|json&<filters>` streams up to 5 000 rows and returns 400 above
the cap with the count, so the UI can direct users to the full snapshot. The
`build_dataset_snapshot` task writes the full set to the public S3 bucket and records a
`DatasetSnapshot` row (version, created date, row count, SHA-256 per file, URLs). `/datasets`
lists snapshots.

### 4.6 Editing and audit

`IncidentRevision`: `incident` FK, `editor` FK to `ACAUser`, `created_at`, `changes` JSONField
of `{field: {"before": ..., "after": ...}}`, optional `content_report` FK.

`IncidentEditSchema` declares the editable subset: title, summary, date, cave, location fields,
tags, analysis. `IncidentEditor.apply(incident, schema, editor, content_report=None)` validates,
diffs against the current values, writes the revision and saves the incident in one
transaction. It is the only write path for the staff API. `ContentReport` gains a nullable
`resolved_by` FK to `IncidentRevision`.

Django admin edits are not audited by this work. Recording them through the same service is
a follow-up.

### 4.7 API structure and hygiene

Routers are grouped by audience: `api/public/` (incidents, browse, stats, geo, exports,
datasets, reports) and `api/staff/` (feedback, incident edits, revisions). Existing paths are
unchanged.

`manage.py export_openapi_schema` output is committed at
`frontend/cidb/src/api/openapi.json`. CI regenerates it and fails on a diff, so a schema change
must arrive with its generated client.

The `CIDB-User-*` response headers (which carry PII) are removed; the frontend uses the
existing `/auth/me` endpoint. The dead `db` app and the unused `DataOperation.model` attribute
are removed when the query layer lands.

### 4.8 Test infrastructure

`factory_boy` factories for every model in `cidb/src/incidents/tests/factories.py` and
`cidb/src/core/tests/factories.py`. A `search_fixture` of roughly thirty incidents spanning
several states, caves, tags, years and injury types is shared by search, facet, browse, stats
and export tests so all five surfaces are asserted against the same data. Existing tests are
moved onto factories in Phase 0.

## 5. Frontend architecture

### 5.1 Generated API client

`openapi-typescript` generates `src/api/schema.d.ts` from `openapi.json`; `openapi-fetch`
provides a typed client. `pnpm api:generate` runs locally and in CI with a diff check. The
retry, CSRF and auth-sync behaviour of `fetchWithRetry` becomes an `openapi-fetch` middleware.

Each feature exposes TanStack Query hooks in `src/api/hooks/` (`useIncidentSearch`,
`useFacets`, `useIncident`, `useRelatedIncidents`, `useStats`, `useGeoPoints`, `useDatasets`,
`useFeedback`, `useEditIncident`). `src/lib/api.ts` is retired function by function; the
final slice deletes it.

### 5.2 Feature folders

```
src/
  api/            generated schema, client, middleware, hooks
  components/ui   shadcn primitives (unchanged)
  components/layout
  features/
    search/       hero, results, filter sidebar, facets, toolbar
    incident/     detail layout, people, related, report-a-problem
    browse/       dimension index and detail pages
    stats/        dashboard and charts
    map/          map view (lazy-loaded)
    export/       download menu, datasets page
    feedback/     public feedback modal
    staff/        login, feedback triage, editor mode, revisions
  lib/            cross-cutting utilities (theme, cookies, sentry)
  test/           setup, MSW handlers and fixtures
```

Each feature exports `routes.tsx`; `App.tsx` assembles them. The map and stats routes are
`React.lazy` so MapLibre and Recharts load only when visited.

### 5.3 Filters as URL state

`useIncidentFilters()` parses and serialises `IncidentFilters` to the query string with a codec
keyed by the same field names as the backend schema, plus `sort_by`, `sort_order` and `view`.
Search, browse, stats, map and export all read from it, so moving between results, map and
download carries the filters, and every state is a link. `SearchPage` component state for sort
and view mode moves into this hook.

### 5.4 Search page decomposition

`SearchPage.tsx` splits into `SearchHero` (landing state with the typing animation),
`SearchResults` (cards or table with infinite scroll), `FilterSidebar` (facet groups, a sheet
on mobile), `FacetGroup`, `ActiveFilterChips` and `ResultsToolbar` (sort, view, count, timing,
download). Staff commands typed into the search box are removed; staff tools are reached from
sidebar routes.

### 5.5 Design system additions

shadcn `chart` (Recharts), `command` (searchable filter pickers), `sheet` (mobile filter
drawer), `accordion` (facet groups), and `form` with `react-hook-form` and `zod` for the
editor form, with zod schemas derived from the generated types. No custom CSS for these.

### 5.6 Testing

MSW handlers in `src/test/msw/` with fixtures typed against the generated schema. Component
tests cover loading, empty, error and populated states for each new feature. Hook tests cover
the URL codec round-trip. No Playwright in this roadmap; the backend API tests plus mocked-API
component tests cover the contract.

### 5.7 Discoverability

A `build_sitemap` task writes `sitemap.xml` to S3 beside the snapshots, listing browse pages
and incidents. A `usePageMeta` hook sets `<title>` and description per route. The SPA is
rendered client-side; no SSR.

## 6. Roadmap

Every slice is a mergeable unit that leaves the live site working. Phases 2, 3 and 4 depend
only on Phases 0 and 1 and may be reordered.
Each phase receives its own implementation plan under `docs/superpowers/plans/` before work
on it starts; this document is the source those plans are written from.

### Phase 0 — Foundations

| # | Slice | Notes |
|---|-------|-------|
| 0.1 | Factories and `search_fixture`; existing tests moved onto them | Test-only change |
| 0.2 | `queries/` package; search and sort moved into it behind characterisation tests | Endpoint output byte-identical before and after |
| 0.3 | Derived date columns, backfill migration, date sort switched to them | Additive migration |
| 0.4 | `IncidentFilters` with tags, states, countries, year range; `/incidents/facets` | Additive API |
| 0.5 | OpenAPI export, committed schema, CI diff check, generated client, `useIncidentSearch` | Replaces `searchIncidents` |
| 0.6 | `useIncidentFilters`; `FilterSidebar` with facet counts | **Ships filtered search** |
| 0.7 | PII headers replaced by `/auth/me`; `db` app and `DataOperation.model` removed | From `TODO.md` |

### Phase 1 — Search complete

| # | Slice | Notes |
|---|-------|-------|
| 1.1 | pgvector migration; `refresh_embedding` task; change signal | Deployment dependency: pgvector image, worker |
| 1.2 | Hybrid ranking behind `sort_by=relevance`; `/incidents/{id}/related`; related list on incident page | |
| 1.3 | Remaining filters (cave, region, injury, publication, has-location); people and injuries on incident page | |
| 1.4 | Search page decomposition; staff commands removed | Frontend-only |

### Phase 2 — Exploration

| # | Slice | Notes |
|---|-------|-------|
| 2.1 | `/browse/{dimension}` API over `facets()` | |
| 2.2 | Browse routes and pages; `usePageMeta`; `build_sitemap` task | |
| 2.3 | `/incidents/stats?group_by=` API; stats dashboard | Lazy route |
| 2.4 | `/incidents/geo` API; map feature with clustering and filter sync | Lazy route |

### Phase 3 — Downloads

| # | Slice | Notes |
|---|-------|-------|
| 3.1 | `exports/` package; `IncidentExportRow`; writers; tests pinning the column set | Column set is the public contract |
| 3.2 | `/incidents/export` streaming endpoint; download menu in results toolbar | |
| 3.3 | `DatasetSnapshot`, `build_dataset_snapshot` task, `/datasets`, Datasets page | Deployment dependency: schedule |

### Phase 4 — Editors

| # | Slice | Notes |
|---|-------|-------|
| 4.1 | `IncidentRevision`, `IncidentEditSchema`, `IncidentEditor`; `PATCH /staff/incidents/{id}`; revisions endpoint | |
| 4.2 | Editor mode on incident page; revision history panel | |
| 4.3 | Feedback linked to revisions; resolve from incident; pending count; staff dashboard route | |
| 4.4 | Follow-up recorded: audit Django admin edits through `IncidentEditor` | Not in this roadmap |

### Phase 5 — Continuous

Picked up alongside the phases above, in no fixed order: remaining `TODO.md` items, an
accessibility pass per feature, a bundle-size budget in CI, cache headers on browse and stats
responses, and review of the collected `SearchQuery`/`SearchClick` data to tune ranking.

### No-regression mechanics

- Characterisation tests are written before any refactor and must pass unchanged after it.
- API changes are additive; the committed OpenAPI schema diff is the tripwire.
- Every public read goes through `IncidentQuery`, so filters cannot diverge between surfaces.
- Migrations are backward-compatible with the running code: add a column, backfill, switch
  reads. Never rename or drop in the same release as the code that stops using it.

## 7. Quality gates

### Per slice

- `just lint` (ruff and strict mypy) clean; `pnpm lint`, `pnpm format:check`, `tsc -b` and
  `vitest` clean.
- OpenAPI schema regenerated and committed if any endpoint or schema changed; CI diff passes.
- Backend: factory-based tests for new behaviour; characterisation tests precede refactors.
- Frontend: component tests for the loading, empty, error and populated states of anything
  new; hook tests for codecs.
- Dead code removed in the same pull request.
- Migrations additive and safe to apply before the code deploys.

### Per phase

- The phase's section of this document is re-read against what shipped; deviations are
  recorded here.
- Deployment dependencies for the next phase are handed over in writing before it starts.
- One manual walk of the primary journey on the live site: search, filter, detail, related,
  feedback.

### Architecture guardrails

- No endpoint builds an `Incident` queryset outside `queries/`.
- No frontend `fetch` outside the generated client.
- No staff write path outside `IncidentEditor`.
- No request-time work that belongs in a task.

## 8. Deployment dependencies

Handed to the deployment owner; not performed by this roadmap.

| Needed by | Dependency |
|-----------|------------|
| 1.1 | Postgres image with the `pgvector` extension available |
| 1.1 | A worker container running the `django-tasks` database worker |
| 2.2, 3.3 | A public S3 prefix the API can write to for `sitemap.xml` and dataset snapshots, and the bucket URL exposed as a setting |
| 3.3 | A schedule invoking `build_dataset_snapshot` (weekly is sufficient) |

## 9. Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Roadmap shape | Foundations first, then vertical slices | Makes "no regression" a property of the architecture rather than of discipline |
| Primary audience | General public | Exploration leads; data access and editor tooling support it |
| Editor scope | Light in-app edits with audit trail | Covers common fixes without rebuilding Django admin |
| Downloads | Result export plus full snapshots | No public API commitment; snapshots are citable and cheap |
| Exploration | Browse, stats, map, related | All four approved |
| Task queue | `django.tasks` with the database worker | Backend-agnostic API; one new process, no Redis, switchable by settings |
| Vectors | pgvector | Related incidents and hybrid search become one SQL query |
| Frontend client | Generated from OpenAPI | Removes the hand-maintained type mirror, the largest source of silent drift |
| Dates | Derived sortable columns | Imprecise string retained as source of truth |
| SEO | Sitemap and meta, no SSR | Sufficient for a client-rendered SPA |
