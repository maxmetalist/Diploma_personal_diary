from django.urls import path
from django.contrib.auth import views as auth_views

from users.views import SignUpView, CustomLoginView, CustomLogoutView, ProfileEditView

app_name = "users"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", CustomLoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", CustomLogoutView.as_view(next_page="diary:home"), name="logout"),
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
]
