---
name: project_period_filter
description: Optional period filter (quarter/half/year) across rating/comparison/history/reports; the latest-within-period + cache-key rules
metadata:
  type: project
---

**Period filter (BCKND-70).** Optional, calendar-based; absent → today's behavior (latest overall).

- Shared utility `apps/common/periods.py`: `resolve_period(period_type, year, index) → (start, end)
  | None` (raises DRF `ValidationError` on a bad combo), `period_range_from_params(params)` (reports),
  and `PeriodParamsSerializer` (query params `period_type` ∈ quarter|half|year, `period_year`,
  `period_index`; methods `period_range()` + `period_cache_params()`). **FRNTND-26 consumes these exact
  query params.**
- The selectors take an optional `date_range` (a `(start, end)` tuple, inclusive `session_date__range`):
  `scoring.selectors.latest_evaluation`/`athlete_evaluations`, `rating.selectors.*`,
  `comparison.selectors.compare_athletes`. `None` → unchanged.
- **Load-bearing invariant:** in `rating/selectors.py` the range is filtered **inside `_latest_ids()`
  BEFORE `.distinct("athlete_id")`** — so it's "latest per athlete *within* the period," not
  latest-overall-then-filtered. Do NOT move it to the outer `filters` dict.
- **Cache:** the rating response cache (`rating/cache.py`) keys off the `filters` dict, so the period
  MUST be added there — `rating/api.py` folds `serializer.period_cache_params()` into the dict passed
  to `cached_response` (top **and** regions), or Q1/Q2 collide.
- Endpoints wired: rating (top/athletes/regions), comparison, evaluation-history
  (`EvaluationViewSet.get_queryset` + the athletes `evaluations`/`latest-evaluation` actions), reports
  (validated at request time → 400, honored in `datasets.py` builders).
- History-stable because `session_date`/dims are snapshots (see [[project_athlete_transfer]]).
