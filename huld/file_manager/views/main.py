from django.views.generic.base import TemplateView


class MainScreen(TemplateView):
    template_name = "main.html"
