from django.urls import path

from panel import views

app_name = "panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("moderacion/", views.moderacion, name="moderacion"),
    path("estado/<str:modelo>/<int:pk>/", views.cambiar_estado, name="cambiar_estado"),
    path("verificar-punto/<int:pk>/", views.verificar_punto, name="verificar_punto"),
]
