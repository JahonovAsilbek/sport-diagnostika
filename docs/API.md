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
(for norms/batteries/thresholds, `region_admin` can also read).

| Method | Path | Description |
|---|---|---|
| GET | `/catalog/regions/` | regions (14) |
| GET | `/catalog/districts/?region=3` | districts |
| GET·POST | `/catalog/organizations/?type=OPSTTM&region=3` | organizations (`type` = classification only) |
| GET | `/catalog/sport-types/` | sport types (30+) |
| GET | `/catalog/age-categories/` | age categories (TOIFA, ordinal 1–6, `age_min`/`age_max`) |
| GET·POST | `/catalog/exercises/?is_active=true` | exercise pool (replaces test-types) |
| GET·POST | `/catalog/batteries/?age_category=4&gender=male` | test batteries (one per age category × gender) |
| GET | `/catalog/batteries/resolve/?athlete=101` | resolve the ordered 5 exercises for an athlete |
| GET | `/catalog/batteries/resolve/?age=14&gender=male` | …or by explicit age + gender |
| GET·POST | `/catalog/norms/?exercise=7&gender=male&age=14` | norms (by exercise × gender × age) |
| GET·PUT | `/catalog/norms/{id}/` | norm + its bands (nested) |
| GET·POST | `/catalog/daraja-thresholds/` | daraja bounds (I/II/III → total range) |

> `weight-categories` are **deferred** (morphofunctional) — see `DEFERRED.md`. Norms are
> **not** filtered by `sport_type` or `block`: the physical standard is universal by
> `age × gender`.

**Exercise** — `GET /catalog/exercises/`
```json
{ "id": 7, "name": "100 m ga pastki startdan yugurish", "unit": "s",
  "value_type": "seconds", "direction": "lower_is_better", "order": 2, "is_active": true }
```

**Battery resolution** — `GET /catalog/batteries/resolve/?athlete=101`
```json
{
  "age_category": { "id": 4, "ordinal": 4, "name": "13–15" },
  "gender": "male", "age": 14,
  "exercises": [
    { "order": 1, "id": 7,  "name": "100 m ga pastki startdan yugurish", "value_type": "seconds" },
    { "order": 2, "id": 8,  "name": "400 m ga pastki startdan yugurish", "value_type": "minsec" },
    { "order": 3, "id": 11, "name": "Turgan joydan uzunlikka sakrash",   "value_type": "count" },
    { "order": 4, "id": 12, "name": "Gimnastika oʻrindigʻida oldinga egilish", "value_type": "cm_signed" },
    { "order": 5, "id": 15, "name": "Turnikda tortilish", "value_type": "count" }
  ]
}
```
> The data-entry form is built directly from this ordered list of 5 exercises.

**Norm (with nested bands)** — `GET /catalog/norms/{id}/`
```json
{
  "id": 12,
  "exercise": { "id": 7, "name": "100 m ga pastki startdan yugurish", "unit": "s",
    "value_type": "seconds", "direction": "lower_is_better" },
  "age_min": 14, "age_max": 14, "gender": "male",
  "valid_from": "2026-01-01", "is_active": true,
  "bands": [
    { "points": 10, "lower_bound": 14.0, "upper_bound": 14.3 },
    { "points": 8,  "lower_bound": 14.3, "upper_bound": 14.6 },
    { "points": 6,  "lower_bound": 14.6, "upper_bound": 14.9 }
  ]
}
```
> Bands are `[lower_bound, upper_bound)` (lower inclusive, upper exclusive); `direction` is
> baked into the ordering of bounds. A value better than the best band clamps to `10`;
> worse than the worst band scores `0`.

**Daraja thresholds** — `GET /catalog/daraja-thresholds/`
```json
{ "results": [
    { "level": "I",   "total_min": 48, "total_max": 50 },
    { "level": "II",  "total_min": 38, "total_max": 46 },
    { "level": "III", "total_min": 30, "total_max": 36 }
] }
```
> `physical_total < 30` → `daraja = none` (nishonsiz). Bounds are data, editable by the admin.

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

**Filters:** `region · district · organization · organization_type · sport_type · gender ·
age_category · coach · is_active · search`.
> `age_category` (TOIFA) — computed from age relative to the session/current date; the
> server computes it dynamically in the filter. `organization_type (OTM|OPSTTM)` is a
> **classification** filter only — it does not affect scoring.

**POST `/athletes/`**
```json
{
  "last_name": "Aliyev", "first_name": "Akmal", "middle_name": "B.",
  "birth_year": 2008, "gender": "male",
  "region": 3, "district": 14, "organization": 7, "sport_type": 5,
  "razryad": "1-razryad", "coach": 22,
  "training_experience": 4, "main_competitions": "National championship 2025"
}
```
> `age_category` is **computed** (not submitted). `block` is no longer submitted or derived
> for scoring — `organization.type (OTM|OPSTTM)` is exposed as a classification attribute
> only. `weight_category` is **deferred** (`DEFERRED.md`).

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
// response: { "id": 555, "status": "draft", "age_category": 4, "gender": "male", ... }
```
> `height_cm` / `weight_kg` are optional (nullable placeholders for future morpho work).
> The response carries the snapshot dims (age_category, gender, region, organization,
> sport_type) frozen at session time.

**POST `/sessions/555/measurements/`** (bulk raw results for the 5 battery exercises)
```json
{ "measurements": [
    { "exercise": 7,  "raw_value": 14.4 },
    { "exercise": 8,  "raw_value": "1:22" },
    { "exercise": 11, "raw_value": 178 },
    { "exercise": 12, "raw_value": 9 },
    { "exercise": 15, "raw_value": 13 }
] }
```
> One row per exercise in the athlete's resolved battery. `minsec` values (e.g. `"1:22"`)
> are normalized to seconds; signed flexibility (e.g. `9` or `-3`) is stored as signed cm.

**POST `/sessions/555/finalize/`** → `202 Accepted`
The scoring engine runs (raw → points 10/8/6 via `NormBand` → `physical_total` → `daraja`
+ color + recommendations), an `Evaluation` snapshot is created, and the relevant rating
cache is invalidated. Finalize is rejected (`400`) if not all 5 battery exercises are
entered, or if a norm is missing for any exercise × age × gender.
```json
{
  "evaluation_id": 900, "status": "computed",
  "physical_total": 42, "daraja": "II", "color": "yellow",
  "indicators": [
    { "exercise": 7,  "raw_value": 14.4, "points": 8 },
    { "exercise": 8,  "raw_value": 82.0, "points": 8 },
    { "exercise": 11, "raw_value": 178,  "points": 10 },
    { "exercise": 12, "raw_value": 9,    "points": 8 },
    { "exercise": 15, "raw_value": 13,   "points": 8 }
  ]
}
```

### Excel import (async)
| Method | Path | Description |
|---|---|---|
| GET | `/imports/template/?age_category=4&gender=male` | download Excel template (columns = the battery exercises) |
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

Partition / filter dimensions: `region · sport_type · age_category · gender` (**no block**).
An optional `period_type(quarter|half|year)` + value applies a `session_date` range; with no
period, the latest Evaluation per athlete is used.

**GET `/rating/top/?sport_type=5&region=3&age_category=4&gender=male&limit=10`**
```json
{ "filters": { "sport_type": "Handball", "region": "Namangan",
               "age_category": "13–15", "gender": "male" },
  "results": [
    { "rank": 1, "athlete": { "id": 101, "full_name": "Aliyev A." },
      "ranking_score": 48, "daraja": "I", "color": "green" },
    { "rank": 2, "athlete": { "id": 140, "full_name": "Valiyev B." },
      "ranking_score": 42, "daraja": "II", "color": "yellow" }
  ] }
```
> `ranking_score = physical_total (0–50)`. The result is cached in Redis (filter
> combination = key). When an athlete is newly evaluated, the key is invalidated.
> Ties share the same `rank`; display tiebreak: latest evaluation date, then full name.

**GET `/rating/regions/?sport_type=5&age_category=4`** (region rating)
```json
{ "results": [
    { "rank": 1, "region": "Namangan", "daraja_i_count": 126, "avg_score": 41.2 },
    { "rank": 2, "region": "Samarqand", "daraja_i_count": 118, "avg_score": 39.8 }
] }
```

---

## 8. Comparison

| Method | Path | Description |
|---|---|---|
| GET | `/comparison/?athletes=101,140,205` | 2–3 athletes side by side |

```json
{ "athletes": [
    { "id": 101, "full_name": "Aliyev A.",
      "physical_total": 48, "ranking_score": 48, "daraja": "I", "color": "green",
      "indicators": [
        { "exercise": "100 m ga pastki startdan yugurish", "raw_value": 14.1, "points": 10 },
        { "exercise": "Turnikda tortilish", "raw_value": 15, "points": 10 }
      ] },
    { "id": 140, "full_name": "Valiyev B.",
      "physical_total": 42, "ranking_score": 42, "daraja": "II", "color": "yellow", "indicators": [ ] }
  ],
  "leader": 101 }
```
> Comparison is per-exercise `points (10/8/6)` and the resulting `physical_total` / `daraja`
> — no OTM/OPSTTM category percentages.

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
{ "athletes_total": 1240,
  "by_organization_type": { "OTM": 800, "OPSTTM": 440 },
  "by_daraja": { "I": 210, "II": 500, "III": 380, "none": 150 },
  "regions": 14, "recent_sessions": 42 }
```
> `by_organization_type` is a classification breakdown only. Numbers are limited to the
> user's scope (region/org).

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
All `Evaluation`s for the given slice (`exercise / age / gender / ...`) are recomputed
against the current norms and the rating cache is cleared.
