from .models import StepRecord, User, Streak, Points
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Sum, Max

def update_streak(user):
    cur_day = date.today()
    streak = 0
    while (StepRecord.objects.filter(user=user, timestamp__date=cur_day).exists()):
        streak += 1
        cur_day -= timedelta(days=1)
    user.streak.current_streak = streak
    user.streak.last_logged_date = date.today()
    if streak > user.streak.max_streak:
        user.streak.max_streak = streak
    user.streak.save()

def update_points(user):
    # This is arbitrary for now, but it's average(steps over past week) + 10 * (streak)
    week_average = user.steps.filter(timestamp__date__gte=date.today() - timedelta(days=6)).aggregate(Sum('step_count'))['step_count__sum'] // 7
    streak_points = user.streak.current_streak * 10
    user.points.current_points = week_average + streak_points
    user.points.save()
