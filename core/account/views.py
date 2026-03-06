# """
# views.py — Advanced Django Auth (CBV Edition)
# Features:
#   ✅ Class-Based Views (ListView, CreateView, UpdateView, DeleteView)
#   ✅ ModelForms with full validation (no raw request.POST)
#   ✅ RBAC: PermissionRequiredMixin + RoleRequiredMixin
#   ✅ User Profile with avatar upload
#   ✅ Audit log on every create / update / delete / password change
#   ✅ Login / Logout with session management
#   ✅ Group permission management
# """

# from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.contrib.auth.models import User, Group, Permission
# from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
# from django.contrib import messages
# from django.shortcuts import render, redirect, get_object_or_404
# from django.urls import reverse_lazy
# from django.db.models import Q
# from django.views.generic import (
#     ListView, CreateView, UpdateView, DeleteView, View, DetailView
# )

# from .forms import UserCreateForm, UserEditForm, UserProfileForm, GroupForm
# from .models import UserProfile, AuditLog, Notification
# from .mixins import AuditLogMixin, AuditDeleteMixin, RoleRequiredMixin


# # ═══════════════════════════════════════════
# # AUTH — Login / Logout
# # ═══════════════════════════════════════════

# class LoginView(View):
#     """
#     Session-based login. Uses Django's built-in AuthenticationForm.
#     Signals in signals.py handle audit logging automatically.
#     """
#     template_name = "account/login.html"

#     def get(self, request):
#         if request.user.is_authenticated:
#             return redirect("dashboard")
#         return render(request, self.template_name, {"form": AuthenticationForm()})

#     def post(self, request):
#         form = AuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)
#             next_url = request.GET.get("next", "dashboard")
#             return redirect(next_url)
#         messages.error(request, "Invalid username or password.")
#         return render(request, self.template_name, {"form": form})


# class LogoutView(LoginRequiredMixin, View):
#     """POST-only logout for CSRF safety."""
#     def post(self, request):
#         logout(request)
#         messages.success(request, "You have been logged out.")
#         return redirect("login")


# # ═══════════════════════════════════════════
# # DASHBOARD
# # ═══════════════════════════════════════════

# @login_required
# def dashboard(request):
#     from .models import Notification
#     context = {
#         "total_users":   User.objects.count(),
#         "total_groups":  Group.objects.count(),
#         "recent_logs":   AuditLog.objects.select_related("actor")[:10],
#         # Pass notification count directly as fallback
#         # (in case context processor isn't registered yet)
#         "notif_unread_count": Notification.objects.filter(
#             recipient=request.user, is_read=False
#         ).count() if request.user.is_authenticated else 0,
#     }
#     return render(request, "dashboard/dashboard.html", context)


# # ═══════════════════════════════════════════
# # USERS
# # ═══════════════════════════════════════════

# class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     model = User
#     template_name = "account/user_list.html"
#     context_object_name = "users"
#     permission_required = "auth.view_user"
#     paginate_by = 20
#     ordering = ["username"]

#     def get_queryset(self):
#         qs = super().get_queryset()
#         q = self.request.GET.get("q", "").strip()
#         if q:
#             qs = qs.filter(
#                 Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q)
#             ).distinct()
#         return qs.prefetch_related("groups", "profile")


# class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
#     model = User
#     form_class = UserCreateForm
#     template_name = "account/user_form.html"
#     permission_required = "auth.add_user"
#     success_url = reverse_lazy("user_list")
#     audit_action = "CREATE"

#     def form_valid(self, form):
#         messages.success(self.request, f"User '{form.cleaned_data['username']}' created.")
#         return super().form_valid(form)

#     def form_invalid(self, form):
#         messages.error(self.request, "Please fix the errors below.")
#         return super().form_invalid(form)


# class UserEditView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
#     model = User
#     form_class = UserEditForm
#     template_name = "account/user_edit.html"
#     permission_required = "auth.change_user"
#     success_url = reverse_lazy("user_list")
#     pk_url_kwarg = "id"
#     audit_action = "UPDATE"

#     def get_form_kwargs(self):
#         # Ensure the form is always bound to the existing User instance
#         # so all fields (username, email, etc.) are pre-populated on GET
#         kwargs = super().get_form_kwargs()
#         kwargs["instance"] = self.get_object()
#         return kwargs

#     def form_valid(self, form):
#         messages.success(self.request, f"User '{form.instance.username}' updated successfully.")
#         return super().form_valid(form)

#     def form_invalid(self, form):
#         messages.error(self.request, "Please fix the errors below.")
#         return super().form_invalid(form)


# class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditDeleteMixin, DeleteView):
#     model = User
#     template_name = "account/user_confirm_delete.html"
#     permission_required = "auth.delete_user"
#     success_url = reverse_lazy("user_list")
#     pk_url_kwarg = "id"

#     def form_valid(self, form):
#         messages.success(self.request, "User deleted.")
#         return super().form_valid(form)


# class UserBulkDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     permission_required = "auth.delete_user"

#     def post(self, request):
#         ids = request.POST.getlist("selected_users")
#         if ids:
#             users = User.objects.filter(id__in=ids)
#             count = users.count()
#             usernames = list(users.values_list('username', flat=True))
#             for u in users:
#                 AuditLog.log(request, "DELETE", target_obj=u, detail=f"Bulk deleted user '{u.username}'")
#             users.delete()
#             Notification.notify_admins(
#                 notif_type="user_deleted",
#                 title=f"{count} user(s) bulk deleted",
#                 message=f"Deleted: {', '.join(usernames)}",
#             )
#             messages.success(request, f"{count} user(s) deleted.")
#         else:
#             messages.warning(request, "No users selected.")
#         return redirect("user_list")


# class UserChangePasswordView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     permission_required = "auth.change_user"
#     template_name = "account/change_password.html"

#     def get(self, request, id):
#         user = get_object_or_404(User, id=id)
#         return render(request, self.template_name, {"form": SetPasswordForm(user), "target_user": user})

#     def post(self, request, id):
#         user = get_object_or_404(User, id=id)
#         form = SetPasswordForm(user, request.POST)
#         if form.is_valid():
#             form.save()
#             update_session_auth_hash(request, user)
#             AuditLog.log(request, "PASSWORD_CHANGE", target_obj=user,
#                          detail=f"Password changed for '{user.username}' by '{request.user.username}'")
#             Notification.notify_admins(
#                 notif_type="password_changed",
#                 title=f"Password changed — '{user.username}'",
#                 message=f"Password was changed for '{user.username}' by '{request.user.username}'.",
#             )
#             messages.success(request, f"Password updated for '{user.username}'.")
#             return redirect("user_list")
#         messages.error(request, "Please fix the errors below.")
#         return render(request, self.template_name, {"form": form, "target_user": user})


# # ═══════════════════════════════════════════
# # USER PROFILE
# # ═══════════════════════════════════════════

# class UserProfileView(LoginRequiredMixin, View):
#     """View and edit your own profile + avatar."""
#     template_name = "account/profile.html"

#     def _get_profile(self, user):
#         profile, _ = UserProfile.objects.get_or_create(user=user)
#         return profile

#     def get(self, request, id=None):
#         # Admins can view anyone's profile; others only their own
#         if id and request.user.has_perm("auth.change_user"):
#             user = get_object_or_404(User, id=id)
#         else:
#             user = request.user
#         profile = self._get_profile(user)
#         form = UserProfileForm(instance=profile)
#         return render(request, self.template_name, {"form": form, "profile": profile, "target_user": user})

#     def post(self, request, id=None):
#         if id and request.user.has_perm("auth.change_user"):
#             user = get_object_or_404(User, id=id)
#         else:
#             user = request.user
#         profile = self._get_profile(user)
#         form = UserProfileForm(request.POST, request.FILES, instance=profile)
#         if form.is_valid():
#             form.save()
#             AuditLog.log(request, "UPDATE", target_obj=profile,
#                          detail=f"Profile updated for '{user.username}'")
#             Notification.notify_admins(
#                 notif_type="profile_updated",
#                 title=f"Profile updated — '{user.username}'",
#                 message=f"'{user.username}' updated their profile.",
#             )
#             # Also notify the user themselves
#             Notification.notify_user(
#                 user=user,
#                 notif_type="profile_updated",
#                 title="Your profile was updated",
#                 message="Your profile information has been saved successfully.",
#             )
#             messages.success(request, "Profile updated successfully.")
#             return redirect("user_profile")
#         messages.error(request, "Please fix the errors below.")
#         return render(request, self.template_name, {"form": form, "profile": profile, "target_user": user})


# # ═══════════════════════════════════════════
# # GROUPS
# # ═══════════════════════════════════════════

# class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     model = Group
#     template_name = "account/group_list.html"
#     context_object_name = "groups"
#     permission_required = "auth.view_group"

#     def get_queryset(self):
#         # Order in get_queryset — avoids conflict between class-level ordering and prefetch_related
#         return Group.objects.prefetch_related("permissions").order_by("name")


# class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
#     model = Group
#     form_class = GroupForm
#     template_name = "account/group_form.html"
#     permission_required = "auth.add_group"
#     success_url = reverse_lazy("group_list")
#     audit_action = "CREATE"

#     def form_valid(self, form):
#         messages.success(self.request, f"Group '{form.cleaned_data['name']}' created.")
#         return super().form_valid(form)


# class GroupEditView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
#     model = Group
#     form_class = GroupForm
#     template_name = "account/group_form.html"
#     permission_required = "auth.change_group"
#     success_url = reverse_lazy("group_list")
#     pk_url_kwarg = "id"
#     audit_action = "UPDATE"

#     def form_valid(self, form):
#         messages.success(self.request, f"Group '{self.object.name}' updated.")
#         return super().form_valid(form)


# class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditDeleteMixin, DeleteView):
#     model = Group
#     template_name = "account/group_confirm_delete.html"
#     permission_required = "auth.delete_group"
#     success_url = reverse_lazy("group_list")
#     pk_url_kwarg = "id"

#     def form_valid(self, form):
#         messages.success(self.request, "Group deleted.")
#         return super().form_valid(form)


# class GroupBulkDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     permission_required = "auth.delete_group"

#     def post(self, request):
#         ids = request.POST.getlist("ids")
#         if ids:
#             groups = Group.objects.filter(id__in=ids)
#             count = groups.count()
#             names = list(groups.values_list('name', flat=True))
#             for g in groups:
#                 AuditLog.log(request, "DELETE", target_obj=g, detail=f"Bulk deleted group '{g.name}'")
#             groups.delete()
#             Notification.notify_admins(
#                 notif_type="group_deleted",
#                 title=f"{count} group(s) bulk deleted",
#                 message=f"Deleted: {', '.join(names)}",
#             )
#             messages.success(request, f"{count} group(s) deleted.")
#         else:
#             messages.warning(request, "No groups selected.")
#         return redirect("group_list")


# # ═══════════════════════════════════════════
# # PERMISSIONS
# # ═══════════════════════════════════════════

# class GroupPermissionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     model = Group
#     template_name = "account/group_permission_list.html"
#     context_object_name = "groups"
#     permission_required = "auth.change_group"


# class GroupPermissionEditView(LoginRequiredMixin, PermissionRequiredMixin, View):
#     permission_required = "auth.change_group"
#     template_name = "account/group_permission_edit.html"

#     def _grouped_permissions(self):
#         # Returns dict: { app_label: [permission, ...] }
#         # Permissions include content_type so template can use {% regroup %} by model
#         perms = Permission.objects.select_related("content_type").order_by(
#             "content_type__app_label", "content_type__model", "codename"
#         )
#         grouped = {}
#         for p in perms:
#             grouped.setdefault(p.content_type.app_label, []).append(p)
#         return grouped

#     def get(self, request, group_id):
#         group = get_object_or_404(Group, id=group_id)
#         return render(request, self.template_name, {
#             "group": group,
#             "grouped_permissions": self._grouped_permissions(),
#             "group_permissions": set(group.permissions.values_list("id", flat=True)),
#         })

#     def post(self, request, group_id):
#         group = get_object_or_404(Group, id=group_id)
#         selected = request.POST.getlist("permissions")
#         old_perms = set(group.permissions.values_list("codename", flat=True))
#         group.permissions.set(selected)
#         new_perms = set(group.permissions.values_list("codename", flat=True))
#         AuditLog.log(request, "PERMISSION_CHANGE", target_obj=group,
#                      detail=f"Permissions changed for '{group.name}'. "
#                             f"Added: {new_perms - old_perms}, Removed: {old_perms - new_perms}")
#         Notification.notify_admins(
#             notif_type="permission_changed",
#             title=f"Permissions changed — '{group.name}'",
#             message=f"Added: {new_perms - old_perms} | Removed: {old_perms - new_perms}",
#         )
#         messages.success(request, f"Permissions updated for '{group.name}'.")
#         return redirect("group_permission_list")


# # ═══════════════════════════════════════════
# # AUDIT LOG
# # ═══════════════════════════════════════════

# class AuditLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
#     """View the audit trail — admin eyes only."""
#     model = AuditLog
#     template_name = "account/audit_log.html"
#     context_object_name = "logs"
#     permission_required = "auth.view_user"
#     paginate_by = 50

#     def get_queryset(self):
#         qs = AuditLog.objects.select_related("actor")
#         action = self.request.GET.get("action")
#         actor = self.request.GET.get("actor")
#         if action:
#             qs = qs.filter(action=action)
#         if actor:
#             qs = qs.filter(actor__username__icontains=actor)
#         return qs

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         ctx["action_choices"] = AuditLog.ACTION_CHOICES
#         return ctx




#New code

"""
views.py — Advanced Django Auth (CBV Edition)
Features:
  ✅ Class-Based Views (ListView, CreateView, UpdateView, DeleteView)
  ✅ ModelForms with full validation (no raw request.POST)
  ✅ RBAC: PermissionRequiredMixin + RoleRequiredMixin
  ✅ User Profile with avatar upload
  ✅ Audit log on every create / update / delete / password change
  ✅ Login / Logout with session management
  ✅ Group permission management
"""

from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, View, DetailView
)

from .forms import UserCreateForm, UserEditForm, UserProfileForm, GroupForm
from .models import UserProfile, AuditLog, Notification
from .mixins import AuditLogMixin, AuditDeleteMixin, RoleRequiredMixin


# ═══════════════════════════════════════════
# AUTH — Login / Logout
# ═══════════════════════════════════════════

class LoginView(View):
    """
    Session-based login. Uses Django's built-in AuthenticationForm.
    Signals in signals.py handle audit logging automatically.
    """
    template_name = "account/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, self.template_name, {"form": AuthenticationForm()})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get("next", "dashboard")
            return redirect(next_url)
        messages.error(request, "Invalid username or password.")
        return render(request, self.template_name, {"form": form})


class LogoutView(LoginRequiredMixin, View):
    """POST-only logout for CSRF safety."""
    def post(self, request):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("login")


# ═══════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════

@login_required
def dashboard(request):
    from .models import Notification
    context = {
        "total_users":   User.objects.count(),
        "total_groups":  Group.objects.count(),
        "recent_logs":   AuditLog.objects.select_related("actor")[:10],
        # Pass notification count directly as fallback
        # (in case context processor isn't registered yet)
        "notif_unread_count": Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count() if request.user.is_authenticated else 0,
    }
    return render(request, "account/dashboard.html", context)


# ═══════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════

class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = "account/user_list.html"
    context_object_name = "users"
    permission_required = "auth.view_user"
    paginate_by = 20
    ordering = ["username"]

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q)
            ).distinct()
        return qs.prefetch_related("groups", "profile")


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "account/user_form.html"
    permission_required = "auth.add_user"
    success_url = reverse_lazy("user_list")
    audit_action = "CREATE"

    def form_valid(self, form):
        messages.success(self.request, f"User '{form.cleaned_data['username']}' created.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)


class UserEditView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "account/user_edit.html"
    permission_required = "auth.change_user"
    success_url = reverse_lazy("user_list")
    pk_url_kwarg = "id"
    audit_action = "UPDATE"

    def get_form_kwargs(self):
        # Ensure the form is always bound to the existing User instance
        # so all fields (username, email, etc.) are pre-populated on GET
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"User '{form.instance.username}' updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below.")
        return super().form_invalid(form)


class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditDeleteMixin, DeleteView):
    model = User
    template_name = "account/user_confirm_delete.html"
    permission_required = "auth.delete_user"
    success_url = reverse_lazy("user_list")
    pk_url_kwarg = "id"

    def form_valid(self, form):
        messages.success(self.request, "User deleted.")
        return super().form_valid(form)


class UserBulkDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "auth.delete_user"

    def post(self, request):
        ids = request.POST.getlist("selected_users")
        if ids:
            users = User.objects.filter(id__in=ids)
            count = users.count()
            usernames = list(users.values_list('username', flat=True))
            for u in users:
                AuditLog.log(request, "DELETE", target_obj=u, detail=f"Bulk deleted user '{u.username}'")
            users.delete()
            Notification.notify_admins(
                notif_type="user_deleted",
                title=f"{count} user(s) bulk deleted",
                message=f"Deleted: {', '.join(usernames)}",
            )
            messages.success(request, f"{count} user(s) deleted.")
        else:
            messages.warning(request, "No users selected.")
        return redirect("user_list")


class UserChangePasswordView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "auth.change_user"
    template_name = "account/change_password.html"

    def get(self, request, id):
        user = get_object_or_404(User, id=id)
        return render(request, self.template_name, {"form": SetPasswordForm(user), "target_user": user})

    def post(self, request, id):
        user = get_object_or_404(User, id=id)
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, user)
            AuditLog.log(request, "PASSWORD_CHANGE", target_obj=user,
                         detail=f"Password changed for '{user.username}' by '{request.user.username}'")
            Notification.notify_admins(
                notif_type="password_changed",
                title=f"Password changed — '{user.username}'",
                message=f"Password was changed for '{user.username}' by '{request.user.username}'.",
            )
            messages.success(request, f"Password updated for '{user.username}'.")
            return redirect("user_list")
        messages.error(request, "Please fix the errors below.")
        return render(request, self.template_name, {"form": form, "target_user": user})


# ═══════════════════════════════════════════
# USER PROFILE
# ═══════════════════════════════════════════

class UserProfileView(LoginRequiredMixin, View):
    """View and edit your own profile + avatar."""
    template_name = "account/profile.html"

    def _get_profile(self, user):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile

    def get(self, request, id=None):
        # Admins can view anyone's profile; others only their own
        if id and request.user.has_perm("auth.change_user"):
            user = get_object_or_404(User, id=id)
        else:
            user = request.user
        profile = self._get_profile(user)
        form = UserProfileForm(instance=profile)
        return render(request, self.template_name, {"form": form, "profile": profile, "target_user": user})

    def post(self, request, id=None):
        if id and request.user.has_perm("auth.change_user"):
            user = get_object_or_404(User, id=id)
        else:
            user = request.user
        profile = self._get_profile(user)
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            AuditLog.log(request, "UPDATE", target_obj=profile,
                         detail=f"Profile updated for '{user.username}'")
            Notification.notify_admins(
                notif_type="profile_updated",
                title=f"Profile updated — '{user.username}'",
                message=f"'{user.username}' updated their profile.",
            )
            # Also notify the user themselves
            Notification.notify_user(
                user=user,
                notif_type="profile_updated",
                title="Your profile was updated",
                message="Your profile information has been saved successfully.",
            )
            messages.success(request, "Profile updated successfully.")
            return redirect("user_profile")
        messages.error(request, "Please fix the errors below.")
        return render(request, self.template_name, {"form": form, "profile": profile, "target_user": user})


# ═══════════════════════════════════════════
# GROUPS
# ═══════════════════════════════════════════

class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    template_name = "account/group_list.html"
    context_object_name = "groups"
    permission_required = "auth.view_group"

    def get_queryset(self):
        # Order in get_queryset — avoids conflict between class-level ordering and prefetch_related
        return Group.objects.prefetch_related("permissions").order_by("name")


class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = "account/group_form.html"
    permission_required = "auth.add_group"
    success_url = reverse_lazy("group_list")
    audit_action = "CREATE"

    def form_valid(self, form):
        messages.success(self.request, f"Group '{form.cleaned_data['name']}' created.")
        return super().form_valid(form)


class GroupEditView(LoginRequiredMixin, PermissionRequiredMixin, AuditLogMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = "account/group_form.html"
    permission_required = "auth.change_group"
    success_url = reverse_lazy("group_list")
    pk_url_kwarg = "id"
    audit_action = "UPDATE"

    def form_valid(self, form):
        messages.success(self.request, f"Group '{self.object.name}' updated.")
        return super().form_valid(form)


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, AuditDeleteMixin, DeleteView):
    model = Group
    template_name = "account/group_confirm_delete.html"
    permission_required = "auth.delete_group"
    success_url = reverse_lazy("group_list")
    pk_url_kwarg = "id"

    def form_valid(self, form):
        messages.success(self.request, "Group deleted.")
        return super().form_valid(form)


class GroupBulkDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "auth.delete_group"

    def post(self, request):
        ids = request.POST.getlist("ids")
        if ids:
            groups = Group.objects.filter(id__in=ids)
            count = groups.count()
            names = list(groups.values_list('name', flat=True))
            for g in groups:
                AuditLog.log(request, "DELETE", target_obj=g, detail=f"Bulk deleted group '{g.name}'")
            groups.delete()
            Notification.notify_admins(
                notif_type="group_deleted",
                title=f"{count} group(s) bulk deleted",
                message=f"Deleted: {', '.join(names)}",
            )
            messages.success(request, f"{count} group(s) deleted.")
        else:
            messages.warning(request, "No groups selected.")
        return redirect("group_list")


# ═══════════════════════════════════════════
# PERMISSIONS
# ═══════════════════════════════════════════

class GroupPermissionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    template_name = "account/group_permission_list.html"
    context_object_name = "groups"
    permission_required = "auth.change_group"


class GroupPermissionEditView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "auth.change_group"
    template_name = "account/group_permission_edit.html"

    def _sidebar_grouped_permissions(self):
        """
        Reads sidebar items from sidebar_config.py — fully dynamic.
        Add a new item to SIDEBAR_ITEMS and it appears here automatically.
        """
        from .sidebar_config import SIDEBAR_ITEMS, ICON_PATHS

        all_perms = list(
            Permission.objects.select_related("content_type")
            .order_by("content_type__model", "codename")
        )

        # Collect all model names assigned to sidebar items
        assigned_models = set(
            m for item in SIDEBAR_ITEMS for m in item.get("models", [])
        )

        # Build buckets per sidebar item name
        buckets = {item["name"]: [] for item in SIDEBAR_ITEMS}
        buckets["Other"] = []

        for perm in all_perms:
            model = perm.content_type.model.lower()
            placed = False
            for item in SIDEBAR_ITEMS:
                if model in item.get("models", []):
                    buckets[item["name"]].append(perm)
                    placed = True
                    break
            if not placed:
                buckets["Other"].append(perm)

        # Build result — skip items with no permissions
        result = []
        for item in SIDEBAR_ITEMS:
            perms = buckets[item["name"]]
            if perms:
                result.append({
                    "name":     item["name"],
                    "icon":     item.get("icon", "other"),
                    "iconpath": ICON_PATHS.get(item.get("icon", "other"), ICON_PATHS["other"]),
                    "perms":    perms,
                    "total":    len(perms),
                })

        # Add catch-all "Other" section if needed
        other_perms = buckets["Other"]
        if other_perms:
            result.append({
                "name":     "Other",
                "icon":     "other",
                "iconpath": ICON_PATHS["other"],
                "perms":    other_perms,
                "total":    len(other_perms),
            })

        return result


    def get(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        return render(request, self.template_name, {
            "group":            group,
            "sidebar_sections": self._sidebar_grouped_permissions(),
            "group_permissions": set(group.permissions.values_list("id", flat=True)),
        })

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        selected = request.POST.getlist("permissions")
        old_perms = set(group.permissions.values_list("codename", flat=True))
        group.permissions.set(selected)   # selected = list of permission IDs
        new_perms = set(group.permissions.values_list("codename", flat=True))
        AuditLog.log(request, "PERMISSION_CHANGE", target_obj=group,
                     detail=f"Permissions changed for '{group.name}'. "
                            f"Added: {new_perms - old_perms}, Removed: {old_perms - new_perms}")
        Notification.notify_admins(
            notif_type="permission_changed",
            title=f"Permissions changed — '{group.name}'",
            message=f"Added: {new_perms - old_perms} | Removed: {old_perms - new_perms}",
        )
        messages.success(request, f"Permissions updated for '{group.name}'.")
        return redirect("group_permission_list")


# ═══════════════════════════════════════════
# AUDIT LOG
# ═══════════════════════════════════════════

class AuditLogListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """View the audit trail — admin eyes only."""
    model = AuditLog
    template_name = "account/audit_log.html"
    context_object_name = "logs"
    permission_required = "auth.view_user"
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor")
        action = self.request.GET.get("action")
        actor = self.request.GET.get("actor")
        if action:
            qs = qs.filter(action=action)
        if actor:
            qs = qs.filter(actor__username__icontains=actor)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["action_choices"] = AuditLog.ACTION_CHOICES
        return ctx