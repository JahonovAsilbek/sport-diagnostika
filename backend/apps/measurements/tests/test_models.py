import pytest
from django.db import IntegrityError, transaction

from apps.catalog.factories import ExerciseFactory
from apps.measurements.factories import MeasurementFactory, TestSessionFactory
from apps.measurements.models import TestSession

pytestmark = pytest.mark.django_db


def test_is_draft_true_for_draft_session():
    session = TestSessionFactory()
    assert session.is_draft is True


def test_is_draft_false_when_finalized():
    session = TestSessionFactory(status=TestSession.Status.FINALIZED)
    assert session.is_draft is False


def test_str_contains_athlete_and_date():
    session = TestSessionFactory()
    rendered = str(session)
    assert str(session.athlete) in rendered
    assert str(session.date) in rendered


def test_measurement_unique_per_session_and_exercise():
    exercise = ExerciseFactory()
    first = MeasurementFactory(exercise=exercise)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            MeasurementFactory(session=first.session, exercise=exercise)
