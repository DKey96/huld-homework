from django.urls import path
from file_manager.views.main import MainScreen

urlpatterns = [path("", MainScreen.as_view())]
