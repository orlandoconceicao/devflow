from django.conf import settings
from django.db import models
class Organization(models.Model):
    name=models.CharField(max_length=160); slug=models.SlugField(unique=True); owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="owned_organizations"); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
class OrganizationMembership(models.Model):
    class Role(models.TextChoices): OWNER="OWNER","Owner"; ADMIN="ADMIN","Admin"; MEMBER="MEMBER","Member"; CLIENT="CLIENT","Client"
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE,related_name="memberships"); user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="memberships"); role=models.CharField(max_length=10,choices=Role.choices,default=Role.MEMBER); joined_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=("organization","user"),name="unique_org_member")]

