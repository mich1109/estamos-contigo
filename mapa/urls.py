from django.urls import path

from mapa import views

app_name = "mapa"

urlpatterns = [
    path("", views.mapa, name="mapa"),
    path("api/marcadores/", views.marcadores, name="marcadores"),
]
