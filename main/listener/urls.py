from django.urls import path
from . import views

urlpatterns = [
    path('listener/', views.webhook)
]
