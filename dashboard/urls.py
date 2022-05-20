from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
   path('', views.index, name='index'),
   path('compare/', views.compare, name='compare'),
   
   # API Route
  path("data", views.database, name="database"),
]