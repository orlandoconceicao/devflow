from abc import ABC,abstractmethod
from django.conf import settings
class PaymentProvider(ABC):
    @abstractmethod
    def create_checkout(self,subscription,success_url,cancel_url):...
    @abstractmethod
    def create_portal(self,subscription,return_url):...
    @abstractmethod
    def cancel(self,subscription):...
    @abstractmethod
    def reactivate(self,subscription):...
    @abstractmethod
    def verify_webhook(self,payload,signature):...
class StripeProvider(PaymentProvider):
    def __init__(self):
        import stripe
        self.stripe=stripe;stripe.api_key=settings.PAYMENT_API_KEY
    def create_checkout(self,s,success_url,cancel_url):
        kwargs={"mode":"subscription","line_items":[{"price":settings.STRIPE_PRO_PRICE_ID,"quantity":1}],"success_url":success_url,"cancel_url":cancel_url,"client_reference_id":str(s.organization_id),"metadata":{"organization_id":str(s.organization_id)}}
        if s.provider_customer_id:kwargs["customer"]=s.provider_customer_id
        else:kwargs["customer_email"]=s.organization.owner.email
        row=self.stripe.checkout.Session.create(**kwargs);return {"url":row.url,"checkout_id":row.id}
    def create_portal(self,s,return_url):return {"url":self.stripe.billing_portal.Session.create(customer=s.provider_customer_id,return_url=return_url).url}
    def cancel(self,s):return self.stripe.Subscription.modify(s.provider_subscription_id,cancel_at_period_end=True)
    def reactivate(self,s):return self.stripe.Subscription.modify(s.provider_subscription_id,cancel_at_period_end=False)
    def verify_webhook(self,payload,signature):return self.stripe.Webhook.construct_event(payload,signature,settings.PAYMENT_WEBHOOK_SECRET)
def get_provider():
    if settings.PAYMENT_PROVIDER!="stripe" or not settings.PAYMENT_API_KEY:raise RuntimeError("Configure o Stripe em modo de teste para iniciar checkout.")
    return StripeProvider()
