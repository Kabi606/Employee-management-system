"""
urls.py — Complete Auth URL Configuration
"""

from django.urls import path
from . import views
from . import notification_views as nv

urlpatterns = [
    # ── Auth ────────────────────────────────────────────────
    path("login/",   views.LoginView.as_view(),  name="login"),
    path("logout/",  views.LogoutView.as_view(), name="logout"),

    # ── Dashboard ───────────────────────────────────────────
    path("", views.dashboard, name="dashboard"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # ── Users ───────────────────────────────────────────────
    path("users/",                          views.UserListView.as_view(),          name="user_list"),
    path("users/create/",                   views.UserCreateView.as_view(),        name="user_create"),
    path("users/<int:id>/edit/",            views.UserEditView.as_view(),          name="user_edit"),
    path("users/<int:id>/delete/",          views.UserDeleteView.as_view(),        name="user_delete"),
    path("users/<int:id>/password/",        views.UserChangePasswordView.as_view(),name="change_password"),
    path("users/bulk-delete/",              views.UserBulkDeleteView.as_view(),    name="user_bulk_delete"),

    # ── Profile ─────────────────────────────────────────────
    path("profile/",                        views.UserProfileView.as_view(),       name="user_profile"),
    path("profile/<int:id>/",               views.UserProfileView.as_view(),       name="user_profile_admin"),

    # ── Groups ──────────────────────────────────────────────
    path("groups/",                         views.GroupListView.as_view(),         name="group_list"),
    path("groups/create/",                  views.GroupCreateView.as_view(),       name="group_create"),
    path("groups/<int:id>/edit/",           views.GroupEditView.as_view(),         name="group_edit"),
    path("groups/<int:id>/delete/",         views.GroupDeleteView.as_view(),       name="group_delete"),
    path("groups/bulk-delete/",             views.GroupBulkDeleteView.as_view(),   name="group_bulk_delete"),

    # ── Permissions ─────────────────────────────────────────
    path("permissions/",                    views.GroupPermissionListView.as_view(), name="group_permission_list"),
    path("permissions/<int:group_id>/edit/",views.GroupPermissionEditView.as_view(), name="group_permission_edit"),

    # ── Audit Log ───────────────────────────────────────────
    path("audit-log/",                      views.AuditLogListView.as_view(),      name="audit_log"),

    # ── Notifications ────────────────────────────────────────
    path("notifications/",                          nv.NotificationListView.as_view(),      name="notifications"),
    path("notifications/mark-all-read/",            nv.NotificationMarkAllReadView.as_view(),name="notif_mark_all_read"),
    path("notifications/<int:pk>/mark-read/",       nv.NotificationMarkReadView.as_view(),  name="notif_mark_read"),
    path("notifications/<int:pk>/delete/",          nv.NotificationDeleteView.as_view(),    name="notif_delete"),
    path("notifications/clear-all/",                nv.NotificationClearAllView.as_view(),  name="notif_clear_all"),
]