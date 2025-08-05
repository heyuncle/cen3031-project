from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.utils import timezone
from datetime import datetime
from .models import StepRecord
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@login_required
@require_POST
@csrf_exempt
def edit_steps(request):
    user = request.user
    day_str = request.POST.get('edit_day')
    step_count = request.POST.get(f'step_count_{day_str}')
    if not day_str or step_count is None:
        return redirect('steps')
    try:
        day = datetime.strptime(day_str, '%Y-%m-%d').date()
        step_count = int(step_count)
    except Exception:
        return redirect('steps')
    # Remove all step records for this user and day
    StepRecord.objects.filter(user=user, timestamp__date=day).delete()
    # Set timestamp: now for today, 12:00 AM for other days
    from datetime import time
    if day == timezone.localdate():
        ts = timezone.now()
    else:
        ts = timezone.make_aware(datetime.combine(day, time(0, 0)))
    # Add new step record
    StepRecord.objects.create(user=user, step_count=step_count, timestamp=ts, is_auto_synced=False)
    return redirect('steps')
