"""
admin.py — Django Admin Registration
Gives you a working admin panel for AuditLog and UserProfile out of the box.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, AuditLog



admin.site.site_header = "Doer Services PLC"
admin.site.site_title = "Doer Services PLC"
admin.site.index_title = "Welcome to Dashboard"

# ── Inline Profile inside User admin ──────────────────────

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = ["avatar", "bio", "phone"]


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ["username", "email", "first_name", "last_name", "is_staff", "is_active", "date_joined"]
    list_filter = ["is_staff", "is_active", "groups"]
    search_fields = ["username", "email"]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ── AuditLog admin ────────────────────────────────────────

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "actor", "action", "target_model", "target_repr", "ip_address"]
    list_filter = ["action", "target_model"]
    search_fields = ["actor__username", "target_repr", "detail"]
    readonly_fields = ["actor", "action", "target_model", "target_id", "target_repr", "detail", "ip_address", "timestamp"]
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        return False  # Audit logs are read-only

    def has_change_permission(self, request, obj=None):
        return False


# ── UserProfile admin ─────────────────────────────────────

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone", "updated_at"]
    search_fields = ["user__username", "phone"]
    readonly_fields = ["created_at", "updated_at"]