from django.urls import path

from core import views

app_name = "core"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("aviso-legal/", views.aviso_legal, name="aviso_legal"),
]
