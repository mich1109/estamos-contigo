from django.urls import path

from informacion import views

app_name = "informacion"

urlpatterns = [
    path("", views.lista, name="lista"),
]
