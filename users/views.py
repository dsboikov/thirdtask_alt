from __future__ import annotations
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.shortcuts import redirect, render, get_object_or_404

from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .forms import RegisterForm, UserUpdateForm, ProfileForm
from .serializers import UserRegisterSerializer
from .models import Profile


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
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        if "save_profile" in request.POST:
            uform = UserUpdateForm(request.POST, instance=user)
            pform = ProfileForm(request.POST, instance=profile)
            pwd_form = PasswordChangeForm(user=user)  # пустая для рендера
            if uform.is_valid() and pform.is_valid():
                uform.save()
                pform.save()
                messages.success(request, "Профиль обновлён.")
                return redirect("users:account")
        elif "change_password" in request.POST:
            uform = UserUpdateForm(instance=user)
            pform = ProfileForm(instance=profile)
            pwd_form = PasswordChangeForm(user=user, data=request.POST)
            if pwd_form.is_valid():
                pwd_form.save()
                update_session_auth_hash(request, user)  # чтобы не разлогинило
                messages.success(request, "Пароль успешно изменён.")
                return redirect("users:account")
        else:
            uform = UserUpdateForm(instance=user)
            pform = ProfileForm(instance=profile)
            pwd_form = PasswordChangeForm(user=user)
    else:
        uform = UserUpdateForm(instance=user)
        pform = ProfileForm(instance=profile)
        pwd_form = PasswordChangeForm(user=user)

    orders = request.user.orders.select_related().all()
    return render(
        request,
        "account/profile.html",
        {"orders": orders, "uform": uform, "pform": pform, "pwd_form": pwd_form},
    )


# API

class RegisterApiView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


# JWT views are imported from simplejwt
jwt_token_obtain_pair = TokenObtainPairView.as_view()
jwt_token_refresh = TokenRefreshView.as_view()
