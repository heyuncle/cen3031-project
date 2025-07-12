from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignUpForm, ManualStepEntryForm
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import StepRecord
import urllib.parse
import urllib.request
from datetime import date, timedelta
from django.conf import settings
from django.shortcuts import redirect, render
from django.utils import timezone
from .models import FitbitToken
from .utils import get_fitbit_steps
from django.db.models.functions import TruncDate
from django.db.models import Sum, Max
import json, base64


class SignUp(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy('login')  # Redirect to login page after successful signup

@login_required
def home(request):
    context = {
        "name": request.user,
        "steps_today": request.user.steps.filter(timestamp__date=date.today()).aggregate(Sum('step_count'))['step_count__sum'],
        "steps_weekly": request.user.steps.filter(timestamp__date__gte=date.today() - timedelta(days=6)).aggregate(Sum('step_count'))['step_count__sum'],
    }
    return render(request, "stridesyncapp/home.html", context)

def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout


@login_required
def fitbit_connect():
    params = {
        'response_type': 'code',
        'client_id': settings.FITBIT_CLIENT_ID,
        'redirect_uri': settings.FITBIT_REDIRECT_URI,
        'scope': 'activity',
    }
    url = 'https://www.fitbit.com/oauth2/authorize?' + urllib.parse.urlencode(params)
    return redirect(url)

@login_required
def fitbit_callback(request):
    code = request.GET.get('code')
    token_url = 'https://api.fitbit.com/oauth2/token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': settings.FITBIT_CLIENT_ID,
        'redirect_uri': settings.FITBIT_REDIRECT_URI,
        'code': code,
        # 'expires_in': '604800',  # set to 1 week, default: 1 day (86400 seconds)
    }

    credentials = f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}"
    base64_creds = base64.b64encode(credentials.encode()).decode()
    req = urllib.request.Request(
        token_url,
        data = urllib.parse.urlencode(data).encode(),
        headers = {'Authorization': f"Basic {base64_creds}"}
    )

    with urllib.request.urlopen(req) as response:
        tokens = json.load(response)

    FitbitToken.objects.update_or_create(
        user = request.user, 
        defaults = {
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_at': timezone.now() + timedelta(seconds=tokens['expires_in']),
        }
    )
    
    return redirect('home')

@login_required
def steps(request):
      
    try:
        get_fitbit_steps(request.user, date.today().isoformat())
    except FitbitToken.DoesNotExist:
        pass

    steps = (request.user.steps.annotate(day=TruncDate('timestamp')).values('day')
             .annotate(step_count=Sum('step_count'), is_auto_synced=Max('is_auto_synced')).order_by('-day'))

    return render(request, 'stridesyncapp/steps.html', {'steps': steps})

@login_required
def manual_step_entry(request):
    if request.method == 'POST':
        form = ManualStepEntryForm(request.POST)
        if form.is_valid():
            step_record = form.save(commit=False)
            step_record.user = request.user
            step_record.is_auto_synced = False  # Manual entry

            step_record.save()
            return redirect('steps')    # Redirect to steps page after saving
    else:
        form = ManualStepEntryForm()
    return render(request, "stridesyncapp/manual_step_entry.html", {"form": form})

@login_required
def profile(request):
    return render(request, "stridesyncapp/profile.html")

@login_required
def leaderboards(request):
    return render(request, "stridesyncapp/leaderboards.html")