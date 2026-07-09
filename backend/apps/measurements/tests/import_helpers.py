"""Shared fixtures for the Excel import tests (B11) — build batteries, matching athletes,
permissive norms (so commit can score), and in-memory `.xlsx` uploads."""

import io
from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from apps.athletes.factories import AthleteFactory
from apps.catalog.factories import (
    AgeCategoryFactory,
    BatteryItemFactory,
    DarajaThresholdFactory,
    ExerciseFactory,
    NormBandFactory,
    NormFactory,
    TestBatteryFactory,
)
from apps.catalog.models import Exercise
from apps.measurements.import_services import IDENT_COLUMNS

IMPORTS = "/api/v1/imports/"
TEMPLATE = f"{IMPORTS}template/"
BATCH_DATE = date(2026, 6, 1)  # an athlete born 2012 is 14 here
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def make_battery(gender="male", age=14):
    """An AgeCategory covering `age` + a 5-exercise (COUNT) battery. Returns (cat, exercises)."""
    cat = AgeCategoryFactory(age_min=age, age_max=age)
    battery = TestBatteryFactory(age_category=cat, gender=gender)
    exercises = [ExerciseFactory(value_type=Exercise.ValueType.COUNT) for _ in range(5)]
    for order, exercise in enumerate(exercises, start=1):
        BatteryItemFactory(battery=battery, exercise=exercise, order=order)
    return cat, exercises


def seed_norms(exercises, gender="male", age=14):
    """A permissive band (→ 8 points) per exercise + the 3 daraja thresholds, so a committed
    row scores 5×8 = 40 → II daraja."""
    for exercise in exercises:
        norm = NormFactory(exercise=exercise, gender=gender, age_min=age, age_max=age)
        NormBandFactory(
            norm=norm, points=8, lower_bound=Decimal("-100"), upper_bound=Decimal("1000")
        )
    DarajaThresholdFactory(level="I", total_min=48, total_max=50)
    DarajaThresholdFactory(level="II", total_min=38, total_max=46)
    DarajaThresholdFactory(level="III", total_min=30, total_max=36)


def make_athlete(gender="male", birth_year=2012, **kwargs):
    return AthleteFactory(gender=gender, birth_year=birth_year, **kwargs)


def row_for(athlete, exercises, value="10"):
    """A template row (dict) matching `athlete`, with `value` for each exercise."""
    row = {
        "last_name": athlete.last_name,
        "first_name": athlete.first_name,
        "middle_name": athlete.middle_name,
        "birth_year": athlete.birth_year,
        "gender": athlete.gender,
    }
    for exercise in exercises:
        row[exercise.name] = value
    return row


def unmatched_row(exercises, value="10"):
    """A well-formed row whose athlete doesn't exist → a validation error row."""
    row = {
        "last_name": "Nomavjud",
        "first_name": "Nomavjud",
        "middle_name": "",
        "birth_year": 2012,
        "gender": "male",
    }
    for exercise in exercises:
        row[exercise.name] = value
    return row


def make_xlsx_bytes(exercises, rows):
    workbook = Workbook()
    worksheet = workbook.active
    header = IDENT_COLUMNS + [exercise.name for exercise in exercises]
    worksheet.append(header)
    for row in rows:
        worksheet.append([row.get(column, "") for column in header])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def xlsx_upload(exercises, rows, name="import.xlsx"):
    return SimpleUploadedFile(name, make_xlsx_bytes(exercises, rows), content_type=XLSX)
