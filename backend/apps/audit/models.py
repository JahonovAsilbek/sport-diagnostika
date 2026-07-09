from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class AuditLog(models.Model):
    """An append-only record of one mutation on a key model — who/what/when/where + the field
    diff. Written synchronously by the audit signals; never updated (no `TimeStampedModel`)."""

    class Action(models.TextChoices):
        CREATED = "created", "Yaratildi"
        UPDATED = "updated", "O'zgartirildi"
        DELETED = "deleted", "O'chirildi"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    action = models.CharField(max_length=8, choices=Action.choices)
    entity_type = models.CharField(max_length=50)  # the model label, e.g. "athlete"
    entity_id = models.CharField(max_length=64)
    changes = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_id"], name="audit_entity_idx"),
            models.Index(fields=["user", "-created_at"], name="audit_user_idx"),
        ]

    def __str__(self):
        return f"{self.action} {self.entity_type}#{self.entity_id}"
