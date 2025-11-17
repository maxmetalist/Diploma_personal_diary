from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from users.forms import CustomUserCreationForm, ProfileEditForm
from users.models import CustomUser


class CustomLoginView(SuccessMessageMixin, LoginView):
    template_name = "users/login.html"
    success_message = "Бобро поржаловать!"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("home")


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("users:login")
    template_name = "registration/signup.html"
    success_message = "Регистрация прошла успешно! Теперь вы можете войти."


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CustomUser
    form_class = ProfileEditForm
    template_name = "users/profile_edit.html"
    success_url = reverse_lazy("diary:entry_list")
    success_message = "Профиль успешно обновлен!"

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs
