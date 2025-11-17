from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from planner.models import Task


@login_required
def tasks_by_date(request):
    """API для получения задач по конкретной дате"""
    date_str = request.GET.get("date")
    if not date_str:
        return JsonResponse({"error": "Date parameter required"}, status=400)

    try:
        target_date = timezone.datetime.fromisoformat(date_str).date()
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    tasks = Task.objects.filter(user=request.user, due_date__date=target_date).order_by("due_date")

    tasks_data = []
    for task in tasks:
        tasks_data.append(
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "priority_display": task.get_priority_display(),
                "status": task.status,
                "status_display": task.get_status_display(),
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat(),
            }
        )

    return JsonResponse({"date": date_str, "tasks": tasks_data})
