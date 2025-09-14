from __future__ import annotations
from typing import List, Union
from django.urls import path, include, URLPattern, URLResolver
from .views import register, account, RegisterApiView, jwt_token_obtain_pair, jwt_token_refresh
from django.contrib.auth import views as auth_views


app_name = "users"


# Web
urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("account/", account, name="account"),
    path("register/", register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

# API
api_urlpatterns: List[Union[URLPattern, URLResolver]] = [
    path("users/register/", RegisterApiView.as_view(), name="api-register"),
    path("users/login/", jwt_token_obtain_pair, name="api-login"),
    path("users/refresh/", jwt_token_refresh, name="api-refresh"),
]

urlpatterns += [
    path("api/", include((api_urlpatterns, "users"), namespace="api-users")),
]
