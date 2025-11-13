from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from users.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'country', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

        placeholders = {
            'email': 'your@email.com',
            'first_name': 'Ваше имя',
            'country': 'Страна проживания',
            'phone': '+7 (XXX) XXX-XX-XX',
        }

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'placeholder': placeholders.get(field, '')
            })


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'country', 'phone', 'avatar')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Страна проживания'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (XXX) XXX-XX-XX'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Email поле только для чтения
        self.fields['email'] = forms.EmailField(
            widget=forms.EmailInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            required=True
        )

        # Устанавливаем начальное значение email
        if self.instance and self.instance.pk:
            self.fields['email'].initial = self.instance.email


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'country', 'phone', 'avatar', 'is_active', 'is_staff', 'is_superuser')
