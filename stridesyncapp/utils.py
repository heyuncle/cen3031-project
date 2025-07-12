import urllib.request
import urllib.parse
import base64
import json
from datetime import datetime, timedelta
from django.utils import timezone
from .models import FitbitToken, StepRecord
from django.conf import settings
from urllib.error import HTTPError

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
