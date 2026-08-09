from django.db.models import Count,Q
from .models import ActivityLog,Project,Task
def log_activity(*,organization,user,action,entity,metadata=None):
    return ActivityLog.objects.create(organization=organization,user=user,action=action,entity_type=entity.__class__.__name__,entity_id=entity.pk,metadata=metadata or {})
def recalculate_project_progress(project):
    counts=project.tasks.aggregate(total=Count("id"),done=Count("id",filter=Q(status=Task.Status.DONE))); progress=round((counts["done"]/counts["total"])*100) if counts["total"] else 0
    Project.objects.filter(pk=project.pk).update(progress=progress); project.progress=progress; return progress
def normalize_positions(*,project,status):
    for index,task_id in enumerate(Task.objects.filter(project=project,status=status).order_by("position","id").values_list("id",flat=True)): Task.objects.filter(pk=task_id).update(position=index)
