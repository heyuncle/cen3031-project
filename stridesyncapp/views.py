from .forms import SignUpForm, ManualStepEntryForm, GroupForm, StepGoalForm
from .models import StepRecord, FitbitToken, Group, GroupMembership, Badge, Streak, Points
from .utils import get_fitbit_steps
from .badge_utils import check_and_award_badges
from .streak_points import update_streak, update_points
from datetime import date, timedelta
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.functions import TruncDate
from django.db.models import Sum, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.shortcuts import redirect, render
from django.utils import timezone
from urllib.error import HTTPError
import urllib.parse
import urllib.request
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
    # awarded_badges will be a list of dicts, or None
    awarded_badges = request.session.pop('awarded_badges', None)

    streak, created = Streak.objects.get_or_create(user=request.user)
    update_streak(request.user)
    update_points(request.user)
    
    # Today’s & this week’s raw totals
    steps_today = request.user.steps \
        .filter(timestamp__date=date.today()) \
        .aggregate(Sum('step_count'))['step_count__sum'] or 0

    steps_weekly = request.user.steps \
        .filter(timestamp__date__gte=date.today() - timedelta(days=6)) \
        .aggregate(Sum('step_count'))['step_count__sum'] or 0

    # 7-day bar chart data
    start_week = date.today() - timedelta(days=6)
    weekly_qs = (
        request.user.steps
        .filter(timestamp__date__gte=start_week)
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(total=Sum('step_count'))
        .order_by('day')
    )
    week_days = [start_week + timedelta(days=i) for i in range(7)]

    weekly_data_map = {
        entry['day']: entry['total']
        for entry in weekly_qs
    }

    labels_weekly = [d.strftime('%b %d') for d in week_days]
    data_weekly   = [weekly_data_map.get(d, 0) for d in week_days]

    # 30-day line chart data
    start_month = date.today() - timedelta(days=29)
    monthly_qs = (
        request.user.steps
        .filter(timestamp__date__gte=start_month)
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(total=Sum('step_count'))
        .order_by('day')
    )
    month_days = [start_month + timedelta(days=i) for i in range(30)]
    monthly_data_map = {e['day']: e['total'] for e in monthly_qs}

    labels_monthly = [d.strftime('%b %d') for d in month_days]
    data_monthly   = [monthly_data_map.get(d, 0) for d in month_days]

    # Progress toward today’s goal
    percent_goal = int((steps_today / request.user.step_goal) * 100)

    context = {
        # your existing context...
        "steps_today": steps_today,
        "steps_weekly": steps_weekly,
        'streak': request.user.streak.current_streak,
        "user_points": request.user.points.current_points if hasattr(request.user, 'points') else 0,

        # new chart & progress data, JSON-encoded for template
        "labels_weekly": json.dumps(labels_weekly),
        "data_weekly": json.dumps(data_weekly),
        "labels_monthly": json.dumps(labels_monthly),
        "data_monthly": json.dumps(data_monthly),
        "percent_goal": percent_goal,
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

    # Can remove once user creation automatically creates streak and points
    if not hasattr(request.user, 'streak'):
                Streak.objects.create(user = request.user, last_logged_date=date.today())
    if not hasattr(request.user, 'points'):
                Points.objects.create(user = request.user)
    # Recalculate streak and points
    update_streak(request.user)
    update_points(request.user)

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

            # Can remove once user creation automatically creates streak and points
            if not hasattr(request.user, 'streak'):
                        Streak.objects.create(user = request.user, last_logged_date=date.today())
            if not hasattr(request.user, 'points'):
                        Points.objects.create(user = request.user)
            # Recalculate streak and points
            update_streak(request.user)
            update_points(request.user)

            # Check and award badges after manual step entry
            badges = check_and_award_badges(
                user=request.user,
                trigger_type="steps",
                value=step_record.step_count,
                request=request  # so session gets set
            )

            return redirect('home')
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

    update_streak(request.user)
    update_points(request.user)

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
    
    update_streak(request.user)
    update_points(request.user)

    return render(request, "stridesyncapp/manual_step_confirm_delete.html", {
        'step_record': step_record,
    })

@login_required
def profile(request):
    return render(request, "stridesyncapp/profile.html")

@login_required
def leaderboards(request):
    return render(request, "stridesyncapp/leaderboards.html")

class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'stridesyncapp/group_list.html'
    context_object_name = 'groups'

class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'stridesyncapp/group_form.html'
    success_url = reverse_lazy('group_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = 'stridesyncapp/group_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        context['is_member'] = group.members.filter(user=self.request.user).exists()
        return context

class GroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'stridesyncapp/group_form.html'
    success_url = reverse_lazy('group_list')

    def test_func(self):
        group = self.get_object()
        return group.created_by == self.request.user or self.request.user.is_admin

class GroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Group
    template_name = 'stridesyncapp/group_confirm_delete.html'
    success_url = reverse_lazy('group_list')

    def test_func(self):
        group = self.get_object()
        return group.created_by == self.request.user or self.request.user.is_admin
    
@login_required
def group_join(request, pk):
    group = get_object_or_404(Group, pk=pk)    
    GroupMembership.objects.get_or_create(user=request.user, group=group)

    return redirect('group_detail', pk=pk)

@login_required
def group_leave(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    GroupMembership.objects.filter(user=request.user, group=group).delete()
    return redirect('group_list')

@login_required
def edit_step_goal(request):
    """
    Let the logged-in user update their daily step_goal.
    """
    if request.method == 'POST':
        form = StepGoalForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = StepGoalForm(instance=request.user)

    return render(request, 'stridesyncapp/edit_step_goal.html', {
        'form': form
    })
