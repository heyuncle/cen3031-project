from django.db import transaction
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from .models import Streak, StepRecord, Points

def update_streak(user):
    # 1. get or create the Streak row
    streak_obj, _ = Streak.objects.get_or_create(
        user=user,
        defaults={'current_streak': 0, 'max_streak': 0, 'last_logged_date': None},
    )

    today = timezone.localdate()

    # 2. fetch all distinct days with any steps up to today
    days = (
        StepRecord.objects
        .filter(user=user, timestamp__date__lte=today)
        .annotate(day=TruncDate('timestamp'))
        .values_list('day', flat=True)
        .distinct()
        .order_by('-day')
    )

    # 3. count consecutive days starting from today
    streak = 0
    for d in days:
        if d == today - timedelta(days=streak):
            streak += 1
        else:
            break

    # 4. update fields atomically
    with transaction.atomic():
        streak_obj.current_streak = streak
        streak_obj.last_logged_date = today
        if streak > streak_obj.max_streak:
            streak_obj.max_streak = streak
        streak_obj.save()

def update_points(user):
    # 1. get or create the Points row
    points_obj, _ = Points.objects.get_or_create(
        user=user,
        defaults={'current_points': 0, 'total_points': 0}
    )

    # 2. compute weekly average safely
    week_start = timezone.localdate() - timedelta(days=6)
    total_steps = (
        user.steps
        .filter(timestamp__date__gte=week_start)
        .aggregate(total=Sum('step_count'))['total']
    ) or 0

    week_average = total_steps // 7

    # 3. add streak bonus
    streak_points = user.streak.current_streak * 10
    new_points = week_average + streak_points

    # 4. update inside a transaction
    with transaction.atomic():
        points_obj.current_points = new_points
        # keep track of all-time high if you want
        points_obj.total_points = max(points_obj.total_points, new_points)
        points_obj.save()


# def update_streak(user):
#     cur_day = date.today()
#     streak = 0
#     while (StepRecord.objects.filter(user=user, timestamp__date=cur_day).exists()):
#         streak += 1
#         cur_day -= timedelta(days=1)
#     user.streak.current_streak = streak
#     user.streak.last_logged_date = date.today()
#     if streak > user.streak.max_streak:
#         user.streak.max_streak = streak
#     user.streak.save()

# def update_points(user):
#     # This is arbitrary for now, but it's average(steps over past week) + 10 * (streak)
#     week_average = user.steps.filter(timestamp__date__gte=date.today() - timedelta(days=6)).aggregate(Sum('step_count'))['step_count__sum'] // 7
#     streak_points = user.streak.current_streak * 10
#     user.points.current_points = week_average + streak_points
#     user.points.save()