from urllib.error import HTTPError
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


def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout

@login_required
def home(request):
    context = {
        "name": request.user,
        "steps_today": request.user.steps.filter(timestamp__date=date.today()).aggregate(Sum('step_count'))['step_count__sum'],
        "steps_weekly": request.user.steps.filter(timestamp__date__gte=date.today() - timedelta(days=6)).aggregate(Sum('step_count'))['step_count__sum'],
    }
    return render(request, "stridesyncapp/home.html", context)

@login_required
def fitbit_connect(request):
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
        'code': code,
        'redirect_uri': settings.FITBIT_REDIRECT_URI,
    }

    creds = f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}"
    b64_creds = base64.b64encode(creds.encode()).decode()

    headers = {
        'Authorization': f"Basic {b64_creds}",
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
    }

    req = urllib.request.Request(
        token_url,
        data=urllib.parse.urlencode(data).encode(),
        headers=headers
    )

    try:
        with urllib.request.urlopen(req) as resp:
            tokens = json.load(resp)
    except HTTPError as e:
        err = e.read().decode()
        print(f"Fitbit callback failed ({e.code}): {err}")
        # Optionally set a Django message here, then redirect
        return redirect('home')

    FitbitToken.objects.update_or_create(
        user=request.user,
        defaults={
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
             .annotate(step_count=Sum('step_count'),
                       is_auto_synced=Max('is_auto_synced')).order_by('-day'))

    return render(request, 'stridesyncapp/steps.html', {'steps': steps})

@login_required
def manual_step_entry(request):
    manual_steps = StepRecord.objects.filter(user=request.user, is_auto_synced=False).order_by('-timestamp')

    if request.method == 'POST':
        form = ManualStepEntryForm(request.POST)
        if form.is_valid():
            step_record = form.save(commit=False)
            step_record.user = request.user
            step_record.is_auto_synced = False
            step_record.save()
            return redirect('manual_step_entry')
    else:
        form = ManualStepEntryForm()

    return render(request, "stridesyncapp/manual_step_entry.html", {"form": form, 'manual_steps': manual_steps})

@login_required
def manual_step_edit(request, pk):
    step_record = StepRecord.objects.get(pk=pk, user=request.user, is_auto_synced=False)

    if request.method == 'POST':
        form = ManualStepEntryForm(request.POST, instance=step_record)
        if form.is_valid():
            form.save()
            return redirect('manual_step_entry')
    else:
        form = ManualStepEntryForm(instance=step_record)

    return render(request, "stridesyncapp/manual_step_edit.html", {
        "form": form,
        'manual_steps': StepRecord.objects.filter(user=request.user, is_auto_synced=False).order_by('-timestamp'),
        })

@login_required
def manual_step_delete(request, pk):
    step_record = StepRecord.objects.get(pk=pk, user=request.user, is_auto_synced=False)

    if request.method == 'POST':
        step_record.delete()
        return redirect('manual_step_entry')

    return render(request, "stridesyncapp/manual_step_confirm_delete.html", {
        'step_record': step_record,
    })

@login_required
def profile(request):
    return render(request, "stridesyncapp/profile.html")

@login_required
def leaderboards(request):
    return render(request, "stridesyncapp/leaderboards.html")