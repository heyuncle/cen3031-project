from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignUpForm
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

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