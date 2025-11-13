from django.urls import path
from users.views import SignUpView, CustomLoginView, CustomLogoutView, ProfileEditView

app_name = 'users'

urlpatterns = [
    path('signup/', SignUpView.as_view(template_name='users/registration/signup.html'), name='signup'),
    path('login/', CustomLoginView.as_view(template_name='users/registration/login.html'), name='login'),
    path('logout/', CustomLogoutView.as_view(next_page='home'), name='logout'),
    path('profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
]
