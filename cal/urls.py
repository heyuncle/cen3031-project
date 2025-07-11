from django.urls import path, include
from . import views

app_name = 'cal'
urlpatterns = [
    path("index/", views.index, name='index'),
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
]
