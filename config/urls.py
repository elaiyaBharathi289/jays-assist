"""URL configuration for Jays Assist."""

from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie


def home(request):
    if request.user.is_authenticated:
        return redirect("chat-page")
    return redirect("login-page")


@ensure_csrf_cookie
def login_page(request):
    if request.user.is_authenticated:
        return redirect("chat-page")
    return TemplateResponse(request, "login.html")


@ensure_csrf_cookie
def register_page(request):
    if request.user.is_authenticated:
        return redirect("chat-page")
    return TemplateResponse(request, "register.html")


@ensure_csrf_cookie
def chat_page(request):
    if not request.user.is_authenticated:
        return redirect("login-page")
    return TemplateResponse(request, "chat.html")


def health_check(request):
    return JsonResponse({"status": "ok", "service": "jays-assist"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("login/", login_page, name="login-page"),
    path("register/", register_page, name="register-page"),
    path("chat/", chat_page, name="chat-page"),
    path("health/", health_check, name="health-check"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("chat.urls")),
]
