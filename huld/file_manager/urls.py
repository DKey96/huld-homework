from django.urls import path
from file_manager.views.main import MainScreen
from file_manager.views.transfer import TransferView

urlpatterns = [
    path("", MainScreen.as_view()),
    path("transfer/", TransferView.as_view({"post": "create"}), name="transfer"),
]
