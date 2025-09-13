from __future__ import annotations
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .forms import RegisterForm
from .serializers import UserRegisterSerializer


# Web

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            login(request, user)
            messages.success(request, "Вы успешно зарегистрированы.")
            return redirect("users:account")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def account(request):
    orders = request.user.orders.select_related().all()
    return render(request, "account/profile.html", {"orders": orders})


# API

class RegisterApiView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


# JWT views are imported from simplejwt
jwt_token_obtain_pair = TokenObtainPairView.as_view()
jwt_token_refresh = TokenRefreshView.as_view()
