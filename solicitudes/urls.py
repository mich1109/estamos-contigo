from django.urls import path

from solicitudes import views

app_name = "solicitudes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nueva/", views.crear, name="crear"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/confirmacion/", views.confirmacion, name="confirmacion"),
]
