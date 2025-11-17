from django import forms

from planner.models import Task


class TaskForm(forms.ModelForm):
    # Поля для дней недели
    monday = forms.BooleanField(required=False, label="Пн")
    tuesday = forms.BooleanField(required=False, label="Вт")
    wednesday = forms.BooleanField(required=False, label="Ср")
    thursday = forms.BooleanField(required=False, label="Чт")
    friday = forms.BooleanField(required=False, label="Пт")
    saturday = forms.BooleanField(required=False, label="Сб")
    sunday = forms.BooleanField(required=False, label="Вс")

    # Поля для чисел месяца
    monthly_days_field = forms.MultipleChoiceField(
        choices=[(str(i), str(i)) for i in range(1, 32)],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Числа месяца",
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "is_recurring",
            "recurrence_end_date",
            "notification_setting",
            "custom_notification_time",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Введите название задачи"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Описание задачи (необязательно)"}
            ),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "is_recurring": forms.Select(attrs={"class": "form-select", "onchange": "toggleRecurrenceFields()"}),
            "recurrence_end_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "notification_setting": forms.Select(
                attrs={"class": "form-select", "onchange": "toggleNotificationFields()"}
            ),
            "custom_notification_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        }
        labels = {
            "title": "Название задачи",
            "description": "Описание",
            "priority": "Приоритет",
            "status": "Статус",
            "due_date": "Срок выполнения",
            "is_recurring": "Повторение задачи",
            "recurrence_end_date": "Повторять до",
            "notification_setting": "Уведомление",
            "custom_notification_time": "Время уведомления",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Устанавливаем начальные значения для дней недели из существующей задачи
        if self.instance and self.instance.weekly_days:
            for day in self.instance.weekly_days:
                field_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][int(day)]
                self.fields[field_name].initial = True

        # Устанавливаем начальные значения для чисел месяца из существующей задачи
        if self.instance and self.instance.monthly_days:
            self.fields["monthly_days_field"].initial = [str(day) for day in self.instance.monthly_days]

    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get("is_recurring")

        # Собираем выбранные дни недели
        weekly_days = []
        day_mapping = {
            "monday": "0",
            "tuesday": "1",
            "wednesday": "2",
            "thursday": "3",
            "friday": "4",
            "saturday": "5",
            "sunday": "6",
        }

        for field_name, day_value in day_mapping.items():
            if cleaned_data.get(field_name):
                weekly_days.append(day_value)

        # Собираем выбранные числа месяца
        monthly_days = cleaned_data.get("monthly_days_field", [])

        # Валидация для еженедельного повторения
        if is_recurring == "weekly" and not weekly_days:
            raise forms.ValidationError("Для еженедельного повторения выберите хотя бы один день недели")

        # Валидация для ежемесячного повторения
        if is_recurring == "monthly" and not monthly_days:
            raise forms.ValidationError("Для ежемесячного повторения выберите хотя бы одно число месяца")

        # Сохраняем данные в форме
        self.weekly_days_data = weekly_days
        self.monthly_days_data = monthly_days

        return cleaned_data

    def save(self, commit=True):
        task = super().save(commit=False)

        # Сохраняем дни недели и числа месяца
        if hasattr(self, "weekly_days_data"):
            task.weekly_days = self.weekly_days_data
        if hasattr(self, "monthly_days_data"):
            task.monthly_days = self.monthly_days_data

        if commit:
            task.save()
        return task
