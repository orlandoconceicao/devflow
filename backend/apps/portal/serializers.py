from rest_framework import serializers
from .models import DeliverableAttachment,DeliverableComment,Notification,NotificationPreference,ProjectDeliverable
class DeliverableCommentSerializer(serializers.ModelSerializer):
    author_name=serializers.SerializerMethodField()
    class Meta:model=DeliverableComment;fields=("id","author_name","message","created_at");read_only_fields=("author_name","created_at")
    def get_author_name(self,o):return o.author.get_full_name() or o.author.email
class DeliverableAttachmentSerializer(serializers.ModelSerializer):
    class Meta:model=DeliverableAttachment;fields=("id","file","original_name","file_size","content_type","created_at");read_only_fields=("original_name","file_size","content_type","created_at")
class DeliverableSerializer(serializers.ModelSerializer):
    comments=DeliverableCommentSerializer(many=True,read_only=True);attachments=DeliverableAttachmentSerializer(many=True,read_only=True);project_name=serializers.CharField(source="project.name",read_only=True)
    class Meta:model=ProjectDeliverable;fields=("id","project","project_name","title","description","status","due_date","comments","attachments","created_at","updated_at");read_only_fields=("created_at","updated_at")
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:model=Notification;fields=("id","type","title","message","data","read_at","created_at");read_only_fields=fields
class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:model=NotificationPreference;fields=("email_enabled","in_app_enabled")
