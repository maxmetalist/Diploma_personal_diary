from django import forms

from alarm.models import Alarm, AlarmSound


class AlarmForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        choices=Alarm.DAYS_OF_WEEK, widget=forms.CheckboxSelectMultiple, required=False, label="Дни недели"
    )

    use_custom_sound = forms.BooleanField(required=False, initial=False, label="Использовать свою мелодию")

    class Meta:
        model = Alarm
        fields = [
            "name",
            "reminder_text",
            "alarm_time",
            "is_recurring",
            "days_of_week",
            "sound",
            "custom_sound",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Название будильника"}),
            "reminder_text": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Текст напоминания..."}
            ),
            "alarm_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "sound": forms.Select(attrs={"class": "form-control"}),
            "custom_sound": forms.FileInput(attrs={"class": "form-control"}),
            "is_recurring": forms.CheckboxInput(),
            "is_active": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Ограничиваем выбор только стандартными мелодиями
        self.fields["sound"].queryset = AlarmSound.objects.filter(is_default=True)
        self.fields["sound"].empty_label = "Выберите мелодию будильника"

        # Скрываем поле custom_sound по умолчанию
        self.fields["custom_sound"].required = False

    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get("is_recurring")
        days_of_week = self.data.getlist("days_of_week")  # Получаем из request.POST
        use_custom_sound = self.data.get("use_custom_sound") == "on"
        custom_sound = cleaned_data.get("custom_sound")

        if is_recurring and not days_of_week:
            raise forms.ValidationError("Для повторяющегося будильника выберите дни недели.")

        if use_custom_sound and not custom_sound:
            raise forms.ValidationError("При использовании своей мелодии необходимо загрузить файл.")

        if not use_custom_sound:
            cleaned_data["custom_sound"] = None

        return cleaned_data
