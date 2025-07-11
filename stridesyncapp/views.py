from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignUpForm, ManualStepEntryForm
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import StepRecord

class SignUp(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy('login')  # Redirect to login page after successful signup

@login_required
def home(request):
    context = {"name": request.user}
    return render(request, "stridesyncapp/home.html", context)

def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect to login page after logout

@login_required
def manual_step_entry(request):
    if request.method == 'POST':
        form = ManualStepEntryForm(request.POST)
        if form.is_valid():
            step_record = form.save(commit=False)
            step_record.user = request.user
            step_record.is_auto_synced = False  # Manual entry
            step_record.save()
            return redirect('manual_step_entry')  # You can change this to another URL if you want
    else:
        form = ManualStepEntryForm()
    return render(request, "stridesyncapp/manual_step_entry.html", {"form": form})
