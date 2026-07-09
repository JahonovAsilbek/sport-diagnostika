from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.athletes.selectors import AgeOutOfRange, age_category_for
from apps.catalog.models import Exercise
from apps.measurements.models import Measurement, TestSession
from apps.measurements.selectors import battery_exercise_ids, missing_exercises

_CENTS = Decimal("0.01")


def parse_raw_value(value_type, raw):
    """Normalize one raw entry to the stored Decimal, per the exercise `value_type`.

    - `minsec`: `"m:ss"` (or numeric seconds) → total seconds, must be > 0
    - `seconds`: Decimal, must be > 0 (a time)
    - `count`: non-negative whole number
    - `cm_signed`: signed Decimal (negatives are valid flexibility readings)

    Raises `ValidationError` on malformed or out-of-domain input. No magic upper bounds —
    the `DecimalField(max_digits=8)` capacity rejects absurd typos; scoring thresholds are
    data, never hardcoded here.
    """
    vt = Exercise.ValueType
    s = str(raw).strip().replace(",", ".")
    if not s:
        raise ValidationError("Qiymat bo'sh bo'lishi mumkin emas.")

    try:
        if value_type == vt.MINSEC:
            if ":" in s:
                minutes, seconds = s.split(":", 1)
                total = Decimal(int(minutes) * 60) + Decimal(seconds)
            else:
                total = Decimal(s)
            if total <= 0:
                raise ValidationError("Vaqt musbat bo'lishi kerak.")
            return total.quantize(_CENTS)
        value = Decimal(s)
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"Noto'g'ri qiymat: {raw!r}.") from exc

    if value_type == vt.CM_SIGNED:
        return value.quantize(_CENTS)
    if value_type == vt.SECONDS:
        if value <= 0:
            raise ValidationError("Vaqt musbat bo'lishi kerak.")
        return value.quantize(_CENTS)
    if value_type == vt.COUNT:
        if value < 0 or value != value.to_integral_value():
            raise ValidationError("Son manfiy bo'lmagan butun bo'lishi kerak.")
        return value.quantize(_CENTS)
    # Unknown value_type: store as-is (defensive; the pool is a fixed set).
    return value.quantize(_CENTS)


def open_session(
    *, athlete, entered_by, date=None, height_cm=None, weight_kg=None,
    source=TestSession.Source.MANUAL,
):
    """Create a draft `TestSession`, snapshotting the athlete's ranking dims at `date`.
    `source` marks how it was entered (manual vs the Excel import pipeline, B11)."""
    date = date or timezone.localdate()
    try:
        age_category = age_category_for(athlete.birth_year, date)
    except AgeOutOfRange as exc:
        raise ValidationError(
            {"athlete": f"Sportchi yoshi ({exc.age}) TOIFA oralig'ida emas."}
        ) from exc
    return TestSession.objects.create(
        athlete=athlete,
        entered_by=entered_by,
        date=date,
        source=source,
        age_category=age_category,
        gender=athlete.gender,
        region=athlete.region,
        organization=athlete.organization,
        sport_type=athlete.sport_type,
        height_cm=height_cm,
        weight_kg=weight_kg,
    )


def resnapshot_date(session, new_date):
    """Re-derive `age_category` when a draft session's date changes."""
    try:
        session.age_category = age_category_for(session.athlete.birth_year, new_date)
    except AgeOutOfRange as exc:
        raise ValidationError(
            {"date": f"Bu sanada sportchi yoshi ({exc.age}) TOIFA oralig'ida emas."}
        ) from exc
    session.date = new_date


def save_measurements(session, items):
    """Upsert raw results for a draft session. `items` is a list of
    `{"exercise": Exercise, "raw_value": <str|number>}`. Every exercise must belong to the
    session's battery; values are parsed per the exercise `value_type`. All-or-nothing."""
    required = battery_exercise_ids(session)
    if required is None:
        raise ValidationError("Bu guruh uchun test batareyasi aniqlanmagan.")
    required_set = set(required)

    errors, parsed = {}, []
    for index, item in enumerate(items):
        exercise = item["exercise"]
        if exercise.id not in required_set:
            errors[str(index)] = f"'{exercise}' bu batareyaga kirmaydi."
            continue
        try:
            parsed.append((exercise, parse_raw_value(exercise.value_type, item["raw_value"])))
        except ValidationError as exc:
            errors[str(index)] = exc.detail
    if errors:
        raise ValidationError({"measurements": errors})

    with transaction.atomic():
        for exercise, value in parsed:
            Measurement.objects.update_or_create(
                session=session, exercise=exercise, defaults={"raw_value": value}
            )
    return session


def finalize_session(session):
    """Validate the full 5-exercise battery is entered, then transition draft→finalized.

    The scoring trigger (`evaluate_session` → `Evaluation`) is wired here in B7/BCKND-46;
    B6 only validates and transitions.
    """
    if not session.is_draft:
        raise ValidationError("Sessiya allaqachon yakunlangan.")
    missing = missing_exercises(session)
    if missing is None:
        raise ValidationError("Bu guruh uchun test batareyasi aniqlanmagan.")
    if missing:
        raise ValidationError(
            {"missing": missing, "detail": "Barcha 5 mashq kiritilishi shart."}
        )
    session.status = TestSession.Status.FINALIZED
    session.save(update_fields=["status", "updated_at"])
    return session
