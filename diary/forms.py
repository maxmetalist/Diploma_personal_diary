from django import forms
from diary.models import DiaryEntry


class DiaryEntryForm(forms.ModelForm):
    class Meta:
        model = DiaryEntry
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введите заголовок"}),
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 10, "placeholder": "Введите содержание записи"}
            ),
        }
