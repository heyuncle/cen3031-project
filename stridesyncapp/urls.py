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

    path('profile/', views.profile, name='profile'),
    path('leaderboards/', views.leaderboards, name='leaderboards'),

    # --- Leaderboard API (Task 13) ---
    path('api/leaderboard/global/', views.api_leaderboard_global, name='api_leaderboard_global'),
    path('api/leaderboard/group/<int:pk>/', views.api_leaderboard_group, name='api_leaderboard_group'),

    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('groups/create/', views.GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:pk>/edit/', views.GroupUpdateView.as_view(), name='group_edit'),
    path('groups/<int:pk>/delete/', views.GroupDeleteView.as_view(), name='group_delete'),
    path('groups/<int:pk>/join/', views.group_join, name='group_join'),
    path('groups/<int:pk>/leave/', views.group_leave, name='group_leave'),

    path('settings/step-goal/', views.edit_step_goal, name='edit_step_goal'),
]
