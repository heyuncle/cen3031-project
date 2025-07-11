from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path("account/", include("django.contrib.auth.urls"), name="login"),  # Include Django's auth URLs
    path('signup/', views.SignUp.as_view(), name='signup'),  # Signup page
    path('logout/', views.logout_view, name='logout'),  # Logout view
    path('steps/manual/', views.manual_step_entry, name='manual_step_entry'),  # Manual step entry
    path('steps/', views.steps, name='steps'),  # View steps
]
