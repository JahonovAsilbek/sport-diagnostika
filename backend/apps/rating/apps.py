from django.apps import AppConfig
from django.db import transaction


def _invalidate_rating_cache(sender, **kwargs):
    """Bump the rating cache generation once the writing transaction commits (so a rolled-back
    Evaluation doesn't invalidate, and the cache call stays off the write's critical path)."""
    from apps.rating.cache import bump_generation

    transaction.on_commit(bump_generation)


class RatingConfig(AppConfig):
    name = "apps.rating"

    def ready(self):
        # Invalidate cached rankings on any Evaluation write (finalize + recompute both go
        # through evaluate_session). Connecting here keeps scoring unaware of rating —
        # rating depends on scoring, never the reverse. Module-level receiver → no weakref GC.
        from django.db.models.signals import post_delete, post_save

        from apps.scoring.models import Evaluation

        post_save.connect(
            _invalidate_rating_cache, sender=Evaluation, dispatch_uid="rating_gen_save"
        )
        post_delete.connect(
            _invalidate_rating_cache, sender=Evaluation, dispatch_uid="rating_gen_delete"
        )
