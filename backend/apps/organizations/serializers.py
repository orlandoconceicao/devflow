from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import Organization,OrganizationMembership
from .services import create_organization
class MembershipSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)
    class Meta: model=OrganizationMembership; fields=("id","user","role","joined_at")
class OrganizationSerializer(serializers.ModelSerializer):
    role=serializers.SerializerMethodField()
    class Meta: model=Organization; fields=("id","name","slug","owner","role","created_at","updated_at"); read_only_fields=("slug","owner")
    def get_role(self,obj):
        membership=obj.memberships.filter(user=self.context["request"].user).first(); return membership.role if membership else None
    def create(self,data): return create_organization(user=self.context["request"].user,name=data["name"])

