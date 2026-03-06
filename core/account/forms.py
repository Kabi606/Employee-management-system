"""
forms.py — ModelForms for User, Profile, Group
- Full validation (duplicates, required fields, password strength)
- Avatar upload with file-type validation
- Role (Group) assignment baked into User forms
"""

from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from .models import UserProfile


# ─────────────────────────────────────────
# USER FORMS
# ─────────────────────────────────────────

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Minimum 8 characters"}),
        min_length=8,
        label="Password",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat password"}),
        label="Confirm Password",
    )
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        empty_label="— No Role —",
        label="Role / Group",
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "e.g. john_doe"}),
            "email": forms.EmailInput(attrs={"placeholder": "user@example.com"}),
        }

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            role = self.cleaned_data.get("role")
            user.groups.set([role] if role else [])
        return user


class UserEditForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        empty_label="— No Role —",
        label="Role / Group",
    )
    is_active = forms.BooleanField(required=False, label="Active account")

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["role"].initial = self.instance.groups.first()

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        qs = User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            role = self.cleaned_data.get("role")
            user.groups.set([role] if role else [])
        return user


# ─────────────────────────────────────────
# PROFILE FORM
# ─────────────────────────────────────────

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]
MAX_AVATAR_SIZE_MB = 2


class UserProfileForm(forms.ModelForm):
    # email lives on User, not UserProfile — add it as an extra field
    email = forms.EmailField(
        required=False,
        label="Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "your@email.com"}),
    )

    class Meta:
        model = UserProfile
        fields = ["avatar", "bio", "phone"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3, "placeholder": "Tell us about yourself..."}),
            "phone": forms.TextInput(attrs={"placeholder": "+880 1700 000000"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate email from the related User instance
        if self.instance and self.instance.pk:
            self.fields["email"].initial = self.instance.user.email

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if email:
            # Check no other user already has this email
            qs = User.objects.filter(email__iexact=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.user.pk)
            if qs.exists():
                raise ValidationError("This email address is already in use.")
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            if hasattr(avatar, "content_type") and avatar.content_type not in ALLOWED_IMAGE_TYPES:
                raise ValidationError("Only JPEG, PNG, WebP, or GIF images are allowed.")
            if avatar.size > MAX_AVATAR_SIZE_MB * 1024 * 1024:
                raise ValidationError(f"Image must be under {MAX_AVATAR_SIZE_MB}MB.")
        return avatar

    def save(self, commit=True):
        profile = super().save(commit=commit)
        # Save email back to the User model
        if commit:
            email = self.cleaned_data.get("email", "").strip()
            profile.user.email = email
            profile.user.save(update_fields=["email"])
        return profile


# ─────────────────────────────────────────
# GROUP FORM
# ─────────────────────────────────────────

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Editors, Managers"}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise ValidationError("Group name is required.")
        qs = Group.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A group with this name already exists.")
        return name