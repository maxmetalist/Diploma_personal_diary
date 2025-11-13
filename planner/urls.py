from django.urls import path

from planner.api import tasks_by_date
from planner.views import PlanningView, TaskCreateView, CalendarView, TaskListView, TaskUpdateView, TaskDeleteView, \
    NotificationView, NotificationPreferenceView

app_name = "planner"

urlpatterns = [
    path("", PlanningView.as_view(), name="planning"),
    path("tasks/", TaskListView.as_view(), name="task_list"),
    path("task/create/", TaskCreateView.as_view(), name="task_create"),
    path("task/<int:pk>/edit/", TaskUpdateView.as_view(), name="task_update"),
    path("task/<int:pk>/delete/", TaskDeleteView.as_view(), name="task_delete"),
    path("calendar/", CalendarView.as_view(), name="calendar"),
    # API endpoints
    path("api/tasks-by-date/", tasks_by_date, name="tasks_by_date"),
    path("calendar/update-date/<int:task_id>/", CalendarView.as_view(), name="calendar_update_date"),
    # Уведомления
    path('api/notifications/', NotificationView.as_view(), name='notifications_api'),
    path('api/notification-preferences/', NotificationPreferenceView.as_view(),
         name='notification_preferences_api'),
]
