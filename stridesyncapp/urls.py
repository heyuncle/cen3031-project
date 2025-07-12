from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path("account/", include("django.contrib.auth.urls"), name="login"),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('logout/', views.logout_view, name='logout'),

    path('steps/', views.steps, name='steps'),
    path('steps/manual/', views.manual_step_entry, name='manual_step_entry'),
    path('steps/<int:pk>/edit/',   views.manual_step_edit,   name='manual_step_edit'),
    path('steps/<int:pk>/delete/', views.manual_step_delete, name='manual_step_delete'),

    path('fitbit/connect/',  views.fitbit_connect,  name='fitbit_connect'),
    path('fitbit/callback/', views.fitbit_callback, name='fitbit_callback'),
    path('steps/', views.steps, name='steps'),

    path('profile/', views.profile, name='profile'),  # User profile
    path('leaderboards/', views.leaderboards, name='leaderboards'),  # Leaderboards
]
