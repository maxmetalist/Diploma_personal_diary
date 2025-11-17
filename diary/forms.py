from django import forms

from diary.models import DiaryEntry, MediaFile



class DiaryEntryForm(forms.ModelForm):
    images = forms.ModelMultipleChoiceField(
        queryset=MediaFile.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "image-select"}),
        required=False,
        label="Добавить изображения",
    )

    class Meta:
        model = DiaryEntry
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введите заголовок"}),
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 10, "placeholder": "Введите содержание записи"}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Ограничиваем выбор только изображениями текущего пользователя
        if user:
            self.fields["images"].queryset = MediaFile.objects.filter(
                user=user, file_type__startswith="image"
            ).order_by("-created_at")
