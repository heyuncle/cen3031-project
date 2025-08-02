from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import datetime, time
from django.conf import settings

# Use a function for default time (Django can't serialize .time directly)
def default_reminder_time():
    return time(19, 0)  # 7:00 PM

# Custom User model
class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    step_goal = models.PositiveIntegerField(default=10000)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

# Fitbit Token model
class FitbitToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"FitbitToken({self.user.username})"

class StepRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='steps')
    step_count = models.PositiveIntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_auto_synced = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.timestamp.date()} - {self.step_count} steps"

class Streak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.PositiveIntegerField(default=0)
    max_streak = models.PositiveIntegerField(default=0)
    last_logged_date = models.DateField(null=True, blank=True, default=datetime.today())

class Points(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points')
    current_points = models.PositiveIntegerField(default=0)
    total_points   = models.PositiveIntegerField(default=0)

class Badge(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    image_url = models.URLField()
    rarity = models.CharField(max_length=20, choices=[
        ('common', 'Common'), 
        ('rare', 'Rare'), 
        ('legendary', 'Legendary')
    ])
    trigger_type = models.CharField(max_length=20, choices=[
        ('steps', 'Steps'), 
        ('streak', 'Streak'), 
        ('leaderboard', 'Leaderboard')
    ])
    trigger_value = models.PositiveIntegerField()

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_on = models.DateTimeField(auto_now_add=True)

class Group(models.Model):
    name = models.CharField(max_length=50)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    created_on = models.DateTimeField(auto_now_add=True)

class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    joined_on = models.DateTimeField(auto_now_add=True)

class LeaderboardEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='leaderboard_entries')
    week_start = models.DateField()
    weekly_step_total = models.PositiveIntegerField()

    class Meta:
        unique_together = ('user', 'group', 'week_start')
        ordering = ['-weekly_step_total']

class GoalHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goal_history')
    date = models.DateField()
    goal_value = models.PositiveIntegerField()
    steps_taken = models.PositiveIntegerField()

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notifications')
    reminder_time = models.TimeField(default=default_reminder_time)
    receive_reminders = models.BooleanField(default=True)
