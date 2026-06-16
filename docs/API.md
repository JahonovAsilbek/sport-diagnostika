# SPORT-DIAGNOSTIKA.UZ — API specification

REST API (Django + DRF). Models: `DATA_MODEL.md`. Architecture: `ARCHITECTURE.md`.

> Status: **agreed**. Version: `v1`.

---

## 1. General conventions

- **Base URL:** `/api/v1/`
- **Format:** JSON (`Content-Type: application/json`), UTF-8.
- **Auth:** JWT — `Authorization: Bearer <access_token>`.
- **Date/time:** ISO 8601 UTC (`2026-06-16T10:00:00Z`). Date: `YYYY-MM-DD`.
- **Language:** error/validation messages in Uzbek (`Accept-Language: uz`).

### Pagination (list responses)
```
GET ...?page=1&page_size=25        (page_size: default 25, max 100)
{
  "count": 1240,
  "next": "/api/v1/athletes/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

### Filtering / sorting / search
- Filter: query param (`?region=3&sport_type=5&gender=male`).
- Sorting: `?ordering=-ranking_score` (`-` = descending).
- Text search: `?search=Aliyev`.

### Error format
```json
{ "detail": "Permission denied.", "code": "permission_denied" }
```
Validation error (422/400):
```json
{ "detail": "Validation error.", "errors": {
    "birth_year": ["This field is required."],
    "height_cm": ["Value must be in the range 50–250."] } }
```

### HTTP statuses
`200` OK · `201` created · `202` accepted (async) · `204` deleted ·
`400/422` validation · `401` not authenticated · `403` permission denied · `404` not found ·
`409` conflict · `429` rate limit.

---

## 2. Roles and scope (permission matrix)

| Role | Athletes | Measurements | Catalog/Norms | Users | Rating | Reports | Scope |
|---|---|---|---|---|---|---|---|
| **super_admin** | CRUD | CRUD | CRUD | CRUD | ✓ | ✓ | entire country |
| **region_admin** | CRUD | CRUD | read | own region | ✓ | ✓ | only own `region_id` |
| **coach** | read | CRUD for own athletes | read | — | ✓ | own athletes | only own athletes |
| **lab_operator** | read | entry (CRUD) | read | — | read | — | only own `organization_id` |
| **ministry** | read | — | read | — | ✓ | ✓ | entire country (read only) |

Scope is enforced **on the server side** for every request (queryset filter) — regardless
of the client filter. `403` is returned if the user accesses a resource outside their
scope.

---

## 3. Auth

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login/` | login+password → token pair |
| POST | `/auth/refresh/` | refresh → new access |
| POST | `/auth/logout/` | blacklist the refresh token |
| GET | `/auth/me/` | current user profile |

**POST `/auth/login/`**
```json
// request
{ "username": "ali.admin", "password": "••••••••" }
// response 200
{
  "access": "eyJ...", "refresh": "eyJ...",
  "user": { "id": 4, "full_name": "Ali Valiyev", "role": "region_admin",
            "region": { "id": 3, "name": "Namangan" }, "organization": null }
}
```

---

## 4. Catalog (reference data)

Read — all authenticated users. Write — `super_admin`
(for norms, `region_admin` can also read).

| Method | Path | Description |
|---|---|---|
| GET | `/catalog/regions/` | regions (14) |
| GET | `/catalog/districts/?region=3` | districts |
| GET·POST | `/catalog/organizations/?type=OPSTTM&region=3` | organizations |
| GET | `/catalog/sport-types/` | sport types (30+) |
| GET | `/catalog/age-categories/` | age categories (5) |
| GET | `/catalog/weight-categories/?sport_type=5&gender=male` | weight categories |
| GET·POST | `/catalog/test-types/?block=OTM&category=physical` | test types |
| GET·POST | `/catalog/norms/?test_type=12&age_category=2&gender=male&sport_type=5` | norms |
| GET·PUT | `/catalog/norms/{id}/` | norm + its bands (nested) |

**Norm (with nested bands)** — `GET /catalog/norms/{id}/`
```json
{
  "id": 12, "test_type": { "id": 7, "name": "30m sprint", "unit": "s",
    "direction": "lower_is_better" },
  "age_category": { "id": 2, "name": "14–15" }, "gender": "male",
  "sport_type": null, "block": "OTM",
  "bands": [
    { "score": 5, "lower_bound": 0,   "upper_bound": 4.5 },
    { "score": 4, "lower_bound": 4.5, "upper_bound": 4.8 },
    { "score": 3, "lower_bound": 4.8, "upper_bound": 5.2 },
    { "score": 2, "lower_bound": 5.2, "upper_bound": 5.6 },
    { "score": 1, "lower_bound": 5.6, "upper_bound": 999 }
  ]
}
```

---

## 5. Athletes

| Method | Path | Description |
|---|---|---|
| GET | `/athletes/` | list + filter (below) |
| POST | `/athletes/` | new athlete card |
| GET·PATCH·DELETE | `/athletes/{id}/` | single athlete |
| GET | `/athletes/{id}/sessions/` | test session history |
| GET | `/athletes/{id}/evaluations/` | evaluation history |
| GET | `/athletes/{id}/latest-evaluation/` | latest evaluation |
| GET | `/athletes/{id}/recommendations/` | recommendations |

**Filters:** `region · district · organization · sport_type · gender ·
age_category · block · coach · is_active · search`.
> `age_category` — computed from `birth_year` relative to the current date; the server
> computes it dynamically in the filter.

**POST `/athletes/`**
```json
{
  "last_name": "Aliyev", "first_name": "Akmal", "middle_name": "B.",
  "birth_year": 2008, "gender": "male",
  "region": 3, "district": 14, "organization": 7, "sport_type": 5,
  "razryad": "1-razryad", "coach": 22, "weight_category": 9,
  "training_experience": 4, "main_competitions": "National championship 2025"
}
```
> `block` is returned but not submitted — it is derived from `organization.type`.

---

## 6. Measurements (test results)

| Method | Path | Description |
|---|---|---|
| GET·POST | `/sessions/` | test sessions |
| GET·PATCH·DELETE | `/sessions/{id}/` | single session (editable in draft state) |
| POST | `/sessions/{id}/measurements/` | bulk entry of raw results |
| POST | `/sessions/{id}/finalize/` | finalize session → triggers evaluation |

**POST `/sessions/`** (open a session)
```json
{ "athlete": 101, "date": "2026-06-15", "height_cm": 178, "weight_kg": 70 }
// response: { "id": 555, "block": "OTM", "status": "draft", ... }
```

**POST `/sessions/555/measurements/`** (raw results)
```json
{ "measurements": [
    { "test_type": 7,  "raw_value": 4.6 },
    { "test_type": 8,  "raw_value": 240 },
    { "test_type": 15, "raw_value": 62 }
] }
```

**POST `/sessions/555/finalize/`** → `202 Accepted`
The scoring engine runs (BMI, score, percentage, level, color + recommendations),
an `Evaluation` snapshot is created, and the relevant rating cache is invalidated.
```json
{ "evaluation_id": 900, "status": "computed" }
```

### Excel import (async)
| Method | Path | Description |
|---|---|---|
| GET | `/imports/template/?block=OTM` | download Excel template |
| POST | `/imports/` | upload file (multipart) → `ImportBatch` |
| GET | `/imports/{id}/` | status + rows + errors |
| POST | `/imports/{id}/commit/` | save the rows that passed validation |

Flow: `uploaded → validating → validated (with errors) → committed`.
Validation runs in Celery; `GET /imports/{id}/` returns the error rows.

---

## 7. Rating — ★ core feature

| Method | Path | Description |
|---|---|---|
| GET | `/rating/athletes/` | rating list (sorted) |
| GET | `/rating/top/` | "Top Athletes" (TOP N) |
| GET | `/rating/regions/` | region rating |

**GET `/rating/top/?sport_type=5&region=3&age_category=2&gender=male&block=OTM&limit=10`**
```json
{ "filters": { "sport_type": "Handball", "region": "Namangan",
               "age_category": "14–15", "gender": "male", "block": "OTM" },
  "results": [
    { "rank": 1, "athlete": { "id": 101, "full_name": "Aliyev A." },
      "ranking_score": 87.0, "level": "high", "color": "green" },
    { "rank": 2, "athlete": { "id": 140, "full_name": "Valiyev B." },
      "ranking_score": 79.0, "level": "medium", "color": "yellow" }
  ] }
```
> The result is cached in Redis (filter combination = key). When an athlete is newly
> evaluated, the key is invalidated.

**GET `/rating/regions/?sport_type=5&age_category=2`** (region rating)
```json
{ "results": [
    { "rank": 1, "region": "Namangan", "high_count": 126, "avg_score": 71.2 },
    { "rank": 2, "region": "Samarqand", "high_count": 118, "avg_score": 68.9 }
] }
```

---

## 8. Comparison

| Method | Path | Description |
|---|---|---|
| GET | `/comparison/?athletes=101,140,205` | 2–3 athletes side by side |

```json
{ "athletes": [
    { "id": 101, "full_name": "Aliyev A.", "block": "OTM",
      "ranking_score": 87.0, "level": "high",
      "categories": { "physical": 92.0, "functional": 82.0 },
      "indicators": [ { "test_type": "30m sprint", "score": 5 }, ... ] },
    { "id": 140, "full_name": "Valiyev B.", "ranking_score": 79.0, ... }
  ],
  "leader": 101 }
```

---

## 9. Recommendations

| Method | Path | Description |
|---|---|---|
| GET | `/athletes/{id}/recommendations/` | athlete recommendations (from the latest evaluation) |
| GET·POST | `/recommendation-rules/` | rules (admin) |
| GET·PUT·DELETE | `/recommendation-rules/{id}/` | rule |

Recommendations are generated automatically during `finalize` (rule → text).

---

## 10. Reports (async)

| Method | Path | Description |
|---|---|---|
| POST | `/reports/` | report request → background job |
| GET | `/reports/` | my reports |
| GET | `/reports/{id}/` | status |
| GET | `/reports/{id}/download/` | download the ready file |

**POST `/reports/`** → `202`
```json
{ "type": "region", "format": "pdf",
  "params": { "region": 3, "sport_type": 5, "age_category": 2 } }
// response: { "id": 77, "status": "pending" }
```
States: `pending → processing → done | failed`. When `done`,
`/reports/77/download/` returns the file. Generation runs in a Celery worker
(`openpyxl` / `python-docx` / `WeasyPrint`).

---

## 11. Users (admin)

| Method | Path | Description |
|---|---|---|
| GET·POST | `/users/` | users (super_admin; region_admin → own region) |
| GET·PATCH·DELETE | `/users/{id}/` | user |
| POST | `/users/{id}/reset-password/` | reset password |

---

## 12. Dashboard / statistics

| Method | Path | Description |
|---|---|---|
| GET | `/stats/overview/` | role-tailored dashboard numbers |

```json
{ "athletes_total": 1240, "by_block": { "OTM": 800, "OPSTTM": 440 },
  "by_level": { "high": 310, "medium": 600, "low": 330 },
  "regions": 14, "recent_sessions": 42 }
```
> The numbers are limited to the user's scope (region/org).

---

## 13. Audit (super_admin)

| Method | Path | Description |
|---|---|---|
| GET | `/audit/?user=&entity_type=athlete&date_from=&date_to=` | change log |

---

## 14. Async job pattern (general)

Long-running jobs (import, report, recompute after a norm change) follow the same pattern:
1. `POST` → `202 Accepted` + `{ id, status: "pending" }`
2. A Celery worker executes it and updates the status.
3. The client polls via `GET /<resource>/{id}/` (`pending|processing|done|failed`).
4. `done` → result/file available.

**POST `/evaluations/recompute/`** (admin, after a norm change) → `202` + job id.
All `Evaluation`s for the given slice (`block/sport/age/...`) are recomputed
and the rating cache is cleared.
