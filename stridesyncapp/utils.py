import urllib.request
import urllib.parse
import base64
import json
from datetime import datetime
from django.utils import timezone
from .models import FitbitToken, StepRecord
from django.conf import settings

def refresh_fitbit_token(token_obj):
    if timezone.now() >= token_obj.expires_at:
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': token_obj.refresh_token,
        }

        credentials = f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}"
        base64_creds = base64.b64encode(credentials.encode()).decode()
        req = urllib.request.Request(
            'https://api.fitbit.com/oauth2/token', data=urllib.parse.urlencode(data).encode(), headers={'Authorization': f"Basic {base64_creds}"}
        )

        with urllib.request.urlopen(req) as response:
            tokens = json.load(response)

        token_obj.access_token = tokens['access_token']
        token_obj.refresh_token = tokens['refresh_token']
        token_obj.expires_at = timezone.now() + timezone.timedelta(seconds=tokens['expires_in'])
        token_obj.save()

def get_fitbit_steps(user, date_str):
    token_obj = FitbitToken.objects.get(user=user)
    refresh_fitbit_token(token_obj)

    url = f"https://api.fitbit.com/1/user/-/activities/date/{date_str}.json"
    req = urllib.request.Request(url, headers={'Authorization': f"Bearer {token_obj.access_token}"})
    
    with urllib.request.urlopen(req) as response:
        data = json.load(response)
    
    # print(data) # debugging to see data structure
    
    steps = data['summary']['steps']
    timestamp = timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))

    StepRecord.objects.update_or_create(user=user, timestamp=timestamp, defaults={'step_count': steps, 'is_auto_synced': True})
