import urllib.request
import urllib.parse
import base64
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from urllib.error import HTTPError
from django.db.models import F, Value, Sum
from django.db.models.functions import Coalesce, TruncWeek, TruncMonth

from .models import FitbitToken, StepRecord, User


def refresh_fitbit_token(token_obj):
    if timezone.now() < token_obj.expires_at:
        return True

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': token_obj.refresh_token,
        'client_id': settings.FITBIT_CLIENT_ID,
    }

    creds = f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}"
    b64 = base64.b64encode(creds.encode()).decode()

    headers = {
        'Authorization': f"Basic {b64}",
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
    }

    req = urllib.request.Request(
        'https://api.fitbit.com/oauth2/token',
        data=urllib.parse.urlencode(data).encode(),
        headers=headers
    )

    try:
        with urllib.request.urlopen(req) as resp:
            tokens = json.load(resp)
    except HTTPError as e:
        body = e.read().decode()
        print(f"Fitbit token refresh failed ({e.code}): {body}")

        if '"errorType":"invalid_grant"' in body:
            token_obj.delete()
        return False

    token_obj.access_token = tokens['access_token']
    token_obj.refresh_token = tokens['refresh_token']
    token_obj.expires_at = timezone.now() + timedelta(seconds=tokens['expires_in'])
    token_obj.save()
    return True


def get_fitbit_steps(user, date_str):
    try:
        token_obj = FitbitToken.objects.get(user=user)
    except FitbitToken.DoesNotExist:
        return

    if not refresh_fitbit_token(token_obj):
        return

    url = f"https://api.fitbit.com/1/user/-/activities/date/{date_str}.json"
    headers = {
        'Authorization': f"Bearer {token_obj.access_token}",
        'Accept': 'application/json',
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
    except HTTPError as e:
        body = e.read().decode()
        print(f"Fitbit fetch failed ({e.code}): {body}")
        return

    steps = data['summary']['steps']
    stamp = timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
    StepRecord.objects.update_or_create(
        user=user,
        timestamp=stamp,
        defaults={'step_count': steps, 'is_auto_synced': True}
    )


# Leaderboard utilities for global and group ranking (Task 13)

def _dense_rank_users(qs, points_attr='points_val', streak_attr='streak_val'):
    ranked = []
    last_points = None
    rank = 0
    for idx, u in enumerate(qs, start=1):
        pts = getattr(u, points_attr)
        if pts != last_points:
            rank = idx
            last_points = pts
        ranked.append({
            "rank": rank,
            "user_id": u.id,
            "username": u.username,
            "points": pts,
            "streak": getattr(u, streak_attr, 0),
        })
    return ranked


def get_global_leaderboard(limit=10):
    qs = (
        User.objects.filter(is_active=True)
        .annotate(
            points_val=Coalesce(F('points__current_points'), Value(0)),
            streak_val=Coalesce(F('streak__current_streak'), Value(0)),
        )
        .order_by('-points_val', '-streak_val', 'username')[:limit]
    )
    return _dense_rank_users(qs)


def get_group_leaderboard(group_id, limit=10):
    qs = (
        User.objects.filter(is_active=True, group_memberships__group_id=group_id)
        .distinct()
        .annotate(
            points_val=Coalesce(F('points__current_points'), Value(0)),
            streak_val=Coalesce(F('streak__current_streak'), Value(0)),
        )
        .order_by('-points_val', '-streak_val', 'username')[:limit]
    )
    return _dense_rank_users(qs)


# Trend analysis functions (Task 16)

def get_weekly_step_totals(user):
    """
    Returns a list of weekly step totals for the given user.
    Format: [{'week': date, 'total_steps': int}]
    """
    return (
        StepRecord.objects
        .filter(user=user)
        .annotate(week=TruncWeek('timestamp'))
        .values('week')
        .annotate(total_steps=Sum('step_count'))
        .order_by('week')
    )


def get_monthly_step_totals(user):
    """
    Returns a list of monthly step totals for the given user.
    Format: [{'month': date, 'total_steps': int}]
    """
    return (
        StepRecord.objects
        .filter(user=user)
        .annotate(month=TruncMonth('timestamp'))
        .values('month')
        .annotate(total_steps=Sum('step_count'))
        .order_by('month')
    )
