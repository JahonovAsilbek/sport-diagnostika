"""Audit signals — write an `AuditLog` row (synchronously, in the change's transaction) on
create/update/delete of the key models. Wired per-sender in `AuditConfig.ready()`."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save, pre_save

from apps.athletes.models import Athlete
from apps.audit.context import current_actor
from apps.audit.models import AuditLog
from apps.catalog.models import Norm
from apps.measurements.models import TestSession

User = get_user_model()

# "measurements" → TestSession granularity (individual Measurements are high-volume children);
# Evaluation is intentionally NOT audited (derived snapshot, delete+created on every recompute).
AUDITED = (Athlete, TestSession, User, Norm)

# password/last_login must never be logged; id/timestamps are noise.
_EXCLUDED = {"id", "created_at", "updated_at", "password", "last_login"}


def _attnames(model):
    return [f.attname for f in model._meta.concrete_fields if f.attname not in _EXCLUDED]


def _on_pre_save(sender, instance, **kwargs):
    if instance.pk is None:
        return
    # Fetch only the audited columns, so password is never even SELECTed into memory.
    instance._audit_old = sender.objects.filter(pk=instance.pk).values(*_attnames(sender)).first()


def _on_post_save(sender, instance, created, **kwargs):
    attnames = _attnames(sender)
    if created:
        changes = {name: getattr(instance, name) for name in attnames}
        action = AuditLog.Action.CREATED
    else:
        old = getattr(instance, "_audit_old", None) or {}
        changes = {
            name: [old.get(name), getattr(instance, name)]
            for name in attnames
            if old.get(name) != getattr(instance, name)
        }
        if not changes:
            return  # nothing audited changed (e.g. a login-only last_login save)
        action = AuditLog.Action.UPDATED
    _write(instance, action, changes)


def _on_post_delete(sender, instance, **kwargs):
    _write(instance, AuditLog.Action.DELETED, {})


def _write(instance, action, changes):
    user, ip = current_actor()
    AuditLog.objects.create(
        user=user, action=action,
        entity_type=instance._meta.model_name, entity_id=str(instance.pk),
        changes=changes, ip=ip,
    )


def connect():
    for model in AUDITED:
        label = model._meta.label_lower
        pre_save.connect(_on_pre_save, sender=model, dispatch_uid=f"audit_pre_{label}")
        post_save.connect(_on_post_save, sender=model, dispatch_uid=f"audit_post_{label}")
        post_delete.connect(_on_post_delete, sender=model, dispatch_uid=f"audit_del_{label}")
