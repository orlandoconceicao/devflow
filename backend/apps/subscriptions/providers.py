from django.conf import settings

from apps.payments.mercado_pago import MercadoPagoClient


class MercadoPagoSubscriptionService:
    def __init__(self, client=None):
        self.client = client or MercadoPagoClient()

    def create_checkout(self, subscription):
        if subscription.provider_subscription_id:
            current = self.client.get_subscription(
                subscription.provider_subscription_id
            )
            if current.get("status") in ("pending", "authorized") and current.get(
                "init_point"
            ):
                return {"url": current["init_point"]}
        row = self.client.create_subscription(
            subscription, f"{settings.FRONTEND_URL}/billing/success"
        )
        subscription.provider = "mercado_pago"
        subscription.provider_subscription_id = str(row["id"])
        subscription.save(
            update_fields=["provider", "provider_subscription_id", "updated_at"]
        )
        return {"url": row["init_point"]}

    def cancel(self, subscription):
        return self.client.update_subscription(
            subscription.provider_subscription_id, "cancelled"
        )


def get_subscription_service():
    return MercadoPagoSubscriptionService()
