from django.conf import settings
from django.core.validators import MaxValueValidator,MinValueValidator
from django.db import models
class Client(models.Model):
    class Status(models.TextChoices): ACTIVE="ACTIVE","Ativo"; INACTIVE="INACTIVE","Inativo"; LEAD="LEAD","Lead"
    organization=models.ForeignKey("organizations.Organization",on_delete=models.CASCADE,related_name="clients"); name=models.CharField(max_length=160); email=models.EmailField(blank=True); phone=models.CharField(max_length=30,blank=True); company=models.CharField(max_length=160,blank=True); document=models.CharField(max_length=40,blank=True); website=models.URLField(blank=True); notes=models.TextField(blank=True); status=models.CharField(max_length=10,choices=Status.choices,default=Status.ACTIVE); created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="clients_created"); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: indexes=[models.Index(fields=["organization","status"]),models.Index(fields=["organization","name"])]
class Project(models.Model):
    class Status(models.TextChoices): PLANNING="PLANNING","Planejamento"; ACTIVE="ACTIVE","Ativo"; ON_HOLD="ON_HOLD","Pausado"; COMPLETED="COMPLETED","Concluído"; CANCELLED="CANCELLED","Cancelado"
    class Priority(models.TextChoices): LOW="LOW","Baixa"; MEDIUM="MEDIUM","Média"; HIGH="HIGH","Alta"; URGENT="URGENT","Urgente"
    organization=models.ForeignKey("organizations.Organization",on_delete=models.CASCADE,related_name="projects"); client=models.ForeignKey(Client,on_delete=models.PROTECT,related_name="projects"); name=models.CharField(max_length=180); description=models.TextField(blank=True); status=models.CharField(max_length=12,choices=Status.choices,default=Status.PLANNING); priority=models.CharField(max_length=10,choices=Priority.choices,default=Priority.MEDIUM); start_date=models.DateField(null=True,blank=True); due_date=models.DateField(null=True,blank=True); progress=models.PositiveSmallIntegerField(default=0,validators=[MinValueValidator(0),MaxValueValidator(100)]); budget=models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True); created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="projects_created"); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: indexes=[models.Index(fields=["organization","status"]),models.Index(fields=["organization","due_date"])]
class ProjectMember(models.Model):
    class Role(models.TextChoices): PROJECT_MANAGER="PROJECT_MANAGER","Gerente"; DEVELOPER="DEVELOPER","Desenvolvedor"; DESIGNER="DESIGNER","Designer"; MEMBER="MEMBER","Membro"; CLIENT="CLIENT","Cliente"
    project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name="members"); user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="project_memberships"); role=models.CharField(max_length=20,choices=Role.choices,default=Role.MEMBER); joined_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["project","user"],name="unique_project_member")]
class ActivityLog(models.Model):
    organization=models.ForeignKey("organizations.Organization",on_delete=models.CASCADE,related_name="activities"); user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,related_name="activities"); action=models.CharField(max_length=50); entity_type=models.CharField(max_length=50); entity_id=models.PositiveBigIntegerField(); metadata=models.JSONField(default=dict,blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]; indexes=[models.Index(fields=["organization","created_at"])]
class TaskLabel(models.Model):
    organization=models.ForeignKey("organizations.Organization",on_delete=models.CASCADE,related_name="task_labels"); name=models.CharField(max_length=60); color=models.CharField(max_length=7,default="#6366F1"); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["organization","name"],name="unique_task_label_name")]; ordering=["name"]
class Task(models.Model):
    class Status(models.TextChoices): BACKLOG="BACKLOG","Backlog"; TODO="TODO","A fazer"; IN_PROGRESS="IN_PROGRESS","Em andamento"; REVIEW="REVIEW","Revisão"; DONE="DONE","Concluído"
    class Priority(models.TextChoices): LOW="LOW","Baixa"; MEDIUM="MEDIUM","Média"; HIGH="HIGH","Alta"; URGENT="URGENT","Urgente"
    organization=models.ForeignKey("organizations.Organization",on_delete=models.CASCADE,related_name="tasks"); project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name="tasks"); title=models.CharField(max_length=220); description=models.TextField(blank=True); status=models.CharField(max_length=15,choices=Status.choices,default=Status.TODO); priority=models.CharField(max_length=10,choices=Priority.choices,default=Priority.MEDIUM); position=models.PositiveIntegerField(default=0); created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="tasks_created"); due_date=models.DateField(null=True,blank=True); completed_at=models.DateTimeField(null=True,blank=True); labels=models.ManyToManyField(TaskLabel,blank=True,related_name="tasks"); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["status","position","id"]; indexes=[models.Index(fields=["organization","project","status","position"]),models.Index(fields=["organization","due_date"])]
class TaskAssignee(models.Model):
    task=models.ForeignKey(Task,on_delete=models.CASCADE,related_name="assignees"); user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="assigned_tasks"); assigned_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=["task","user"],name="unique_task_assignee")]
class TaskComment(models.Model):
    task=models.ForeignKey(Task,on_delete=models.CASCADE,related_name="comments"); author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="task_comments"); content=models.TextField(); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["created_at"]
class TaskAttachment(models.Model):
    task=models.ForeignKey(Task,on_delete=models.CASCADE,related_name="attachments"); uploaded_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="task_attachments"); file=models.FileField(upload_to="task_attachments/%Y/%m/"); original_name=models.CharField(max_length=255); file_size=models.PositiveBigIntegerField(); content_type=models.CharField(max_length=100); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]
