from django import template

register = template.Library()

@register.filter
def filter_by_status(tasks, status):
    """Фильтрует задачи по статусу"""
    return [task for task in tasks if task.status == status]

@register.filter
def get_nearest_deadline(tasks):
    """Возвращает ближайший дедлайн из списка задач"""
    tasks_with_deadline = [task for task in tasks if task.due_date and task.status != 'done']
    if tasks_with_deadline:
        return min(tasks_with_deadline, key=lambda x: x.due_date).due_date
    return None
