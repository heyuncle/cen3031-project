from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, StepRecord, Streak, Badge, UserBadge,
    Group, GroupMembership, LeaderboardEntry,
    GoalHistory, NotificationPreference
)

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('is_admin', 'step_goal')}),
    )

admin.site.register(User, UserAdmin)
admin.site.register(StepRecord)
admin.site.register(Streak)
admin.site.register(Badge)
admin.site.register(UserBadge)
admin.site.register(Group)
admin.site.register(GroupMembership)
admin.site.register(LeaderboardEntry)
admin.site.register(GoalHistory)
admin.site.register(NotificationPreference)
