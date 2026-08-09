from rest_framework import serializers
from .models import Plan,Subscription
class PlanSerializer(serializers.ModelSerializer):
    class Meta: model=Plan; fields=("id","name","slug","price","billing_interval")
class SubscriptionSerializer(serializers.ModelSerializer):
    plan=PlanSerializer(read_only=True); organization=serializers.IntegerField(source="organization_id",read_only=True)
    class Meta: model=Subscription; fields=("id","organization","plan","status","started_at","current_period_start","current_period_end","cancel_at_period_end","canceled_at")
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:model=__import__('apps.subscriptions.models',fromlist=['SubscriptionPayment']).SubscriptionPayment;fields=("id","provider_payment_id","amount","currency","status","paid_at","created_at")
