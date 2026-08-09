from .models import Plan, Subscription


def create_free_subscription(organization):
    plan, _ = Plan.objects.get_or_create(
        slug="free", defaults={"name": "Free", "price": "0.00"}
    )
    return Subscription.objects.create(
        organization=organization, plan=plan, status=Subscription.Status.ACTIVE
    )
