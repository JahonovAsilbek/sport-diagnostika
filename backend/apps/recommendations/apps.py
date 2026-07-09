from django.apps import AppConfig
from django.db import transaction


def _generate_on_evaluation(sender, instance, created, **kwargs):
    """Generate recommendations once a brand-new Evaluation's transaction commits.

    `created` guard: only a fresh Evaluation triggers generation — a later `.save()` must not.
    `on_commit` defers past `IndicatorScore.bulk_create` (which runs after `Evaluation.create`
    inside finalize's transaction), so the indicators are present. Keeps scoring unaware of
    recommendations (recommendations depends on scoring, never the reverse)."""
    if not created:
        return
    from apps.recommendations.services import generate_recommendations_for

    evaluation_pk = instance.pk
    transaction.on_commit(lambda: generate_recommendations_for(evaluation_pk))


class RecommendationsConfig(AppConfig):
    name = "apps.recommendations"

    def ready(self):
        from django.db.models.signals import post_save

        from apps.scoring.models import Evaluation

        post_save.connect(
            _generate_on_evaluation, sender=Evaluation, dispatch_uid="rec_generate_save"
        )
