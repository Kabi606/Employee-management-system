"""
sidebar_config.py
═══════════════════════════════════════════════════════
THE SINGLE SOURCE OF TRUTH for sidebar navigation.

When you add a new sidebar item:
  1. Add it here in SIDEBAR_ITEMS
  2. Add the nav-item in base.html   (just copy-paste an existing one)
  3. Done — permissions page updates automatically

No other file needs to change.
═══════════════════════════════════════════════════════
"""

SIDEBAR_ITEMS = [
    # ── Main ──────────────────────────────────────────
    {
        "name":     "Dashboard",
        "url":      "dashboard",
        "section":  "Main",
        "models":   [],           # no model permissions needed
        "icon":     "home",
    },

    # ── User Management ───────────────────────────────
    {
        "name":     "Users",
        "url":      "user_list",
        "section":  "User Management",
        "models":   ["user", "logentry"],
        "icon":     "users",
    },
    {
        "name":     "Roles & Groups",
        "url":      "group_list",
        "section":  "User Management",
        "models":   ["group"],
        "icon":     "group",
    },
    {
        "name":     "Permissions",
        "url":      "group_permission_list",
        "section":  "User Management",
        "models":   ["permission", "contenttype"],
        "icon":     "permission",
    },

    # ── Account ───────────────────────────────────────
    {
        "name":     "My Profile",
        "url":      "user_profile",
        "section":  "Account",
        "models":   ["userprofile"],
        "icon":     "profile",
    },
    {
        "name":     "Audit Log",
        "url":      "audit_log",
        "section":  "Account",
        "models":   ["auditlog", "notification"],
        "icon":     "audit",
    },

    # ══════════════════════════════════════════════════
    # ADD YOUR NEW SIDEBAR ITEMS HERE:
    #
    # {
    #     "name":    "Students",          ← sidebar label
    #     "url":     "student_list",      ← Django url name
    #     "section": "School",            ← section header
    #     "models":  ["student"],         ← model names for permissions
    #     "icon":    "users",             ← icon key (see base.html icons)
    # },
    # ══════════════════════════════════════════════════
]


# Icon SVG paths — used in permission page sidebar
# Add new icons here when you add new sidebar items
ICON_PATHS = {
    "home":       "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
    "users":      "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75",
    "group":      "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
    "permission": "M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z",
    "profile":    "M5.121 17.804A7 7 0 0112 15a7 7 0 016.879 2.804M15 10a3 3 0 11-6 0 3 3 0 016 0z",
    "audit":      "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
    "other":      "M4 6h16M4 12h16M4 18h7",
    # Add your new icon paths here
}