from decimal import Decimal

import factory
from django.utils import timezone

from apps.catalog.factories import ExerciseFactory
from apps.measurements.factories import TestSessionFactory
from apps.scoring.models import Evaluation, IndicatorScore


class EvaluationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Evaluation

    session = factory.SubFactory(TestSessionFactory)
    # Snapshot dims mirror the session (as evaluate_session copies them).
    athlete = factory.SelfAttribute("session.athlete")
    age_category = factory.SelfAttribute("session.age_category")
    gender = factory.SelfAttribute("session.gender")
    region = factory.SelfAttribute("session.region")
    sport_type = factory.SelfAttribute("session.sport_type")
    session_date = factory.SelfAttribute("session.date")
    physical_total = 42
    daraja = Evaluation.Daraja.SECOND
    color = Evaluation.Color.YELLOW
    ranking_score = 42
    computed_at = factory.LazyFunction(timezone.now)


class IndicatorScoreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IndicatorScore

    evaluation = factory.SubFactory(EvaluationFactory)
    exercise = factory.SubFactory(ExerciseFactory)
    raw_value = Decimal("14.40")
    points = 8
