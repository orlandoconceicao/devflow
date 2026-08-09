from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
class UserManager(BaseUserManager):
    use_in_migrations=True
    def create_user(self,email,password=None,**extra):
        if not email: raise ValueError("Email é obrigatório")
        user=self.model(email=self.normalize_email(email).lower(),**extra); user.set_password(password); user.save(using=self._db); return user
    def create_superuser(self,email,password,**extra):
        extra.update(is_staff=True,is_superuser=True); return self.create_user(email,password,**extra)
class User(AbstractUser):
    username=models.CharField(max_length=150,blank=True,null=True,unique=True); email=models.EmailField(unique=True); avatar=models.URLField(blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    USERNAME_FIELD="email"; REQUIRED_FIELDS=[]; objects=UserManager()
