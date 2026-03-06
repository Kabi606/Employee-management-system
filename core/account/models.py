"""
models.py — Advanced Auth Models
- UserProfile: extends User with avatar, bio, phone
- AuditLog: tracks every create/edit/delete action
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


def avatar_upload_path(instance, filename):
    ext = filename.split(".")[-1]
    return f"avatars/user_{instance.user.id}.{ext}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to=avatar_upload_path, null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return "/static/account/img/default_avatar.png"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Created"),
        ("UPDATE", "Updated"),
        ("DELETE", "Deleted"),
        ("LOGIN",  "Logged In"),
        ("LOGOUT", "Logged Out"),
        ("PASSWORD_CHANGE", "Password Changed"),
        ("PERMISSION_CHANGE", "Permission Changed"),
    ]

    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name="audit_actions"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_model = models.CharField(max_length=50, blank=True)   # e.g. "User", "Group"
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_repr = models.CharField(max_length=200, blank=True)   # e.g. "john_doe"
    detail = models.TextField(blank=True)                         # extra context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.actor} → {self.action} {self.target_model}"

    @classmethod
    def log(cls, request, action, target_obj=None, detail=""):
        """Convenience factory method."""
        actor = request.user if request.user.is_authenticated else None
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() \
             or request.META.get("REMOTE_ADDR")
        cls.objects.create(
            actor=actor,
            action=action,
            target_model=target_obj.__class__.__name__ if target_obj else "",
            target_id=target_obj.pk if target_obj else None,
            target_repr=str(target_obj) if target_obj else "",
            detail=detail,
            ip_address=ip or None,
        )

class Notification(models.Model):
    NOTIF_TYPES = [
        ("user_created",        "New user created"),
        ("user_updated",        "User updated"),
        ("user_deleted",        "User deleted"),
        ("password_changed",    "Password changed"),
        ("permission_changed",  "Permission changed"),
        ("login_failed",        "Failed login attempt"),
        ("group_created",       "Group created"),
        ("group_deleted",       "Group deleted"),
        ("profile_updated",     "Profile updated"),
    ]

    recipient   = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notif_type  = models.CharField(max_length=30, choices=NOTIF_TYPES)
    title       = models.CharField(max_length=200)
    message     = models.TextField(blank=True)
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(default=timezone.now)
    # Optional link to related audit log entry
    audit_log   = models.ForeignKey(
        AuditLog, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="notifications"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.notif_type}] → {self.recipient.username}"

    @classmethod
    def notify_admins(cls, notif_type, title, message="", audit_log=None):
        """Send notification to all staff/superusers."""
        admins = User.objects.filter(
            models.Q(is_staff=True) | models.Q(is_superuser=True)
        ).distinct()
        notifications = [
            cls(
                recipient=admin,
                notif_type=notif_type,
                title=title,
                message=message,
                audit_log=audit_log,
            )
            for admin in admins
        ]
        cls.objects.bulk_create(notifications)

    @classmethod
    def notify_user(cls, user, notif_type, title, message="", audit_log=None):
        """Send notification to a specific user."""
        cls.objects.create(
            recipient=user,
            notif_type=notif_type,
            title=title,
            message=message,
            audit_log=audit_log,
        )