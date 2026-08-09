from datetime import date, timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.finance.models import Expense, Revenue
from apps.organizations.models import Organization, OrganizationMembership
from apps.portal.models import Notification, ProjectDeliverable
from apps.subscriptions.models import Plan, Subscription
from apps.work.models import Client, Project, ProjectMember, Task


class Command(BaseCommand):
    help = "Cria dados idempotentes para demonstração local"

    def handle(self, *args, **kwargs):
        call_command("seed_plans", verbosity=0)
        user, _ = User.objects.get_or_create(
            email="demo@devflow.local",
            defaults={"first_name": "Demo", "last_name": "Owner"},
        )
        user.set_password("DevFlowDemo!2026")
        user.save()
        org, _ = Organization.objects.get_or_create(
            slug="nexus-digital-demo", defaults={"name": "Nexus Digital", "owner": user}
        )
        OrganizationMembership.objects.get_or_create(
            organization=org, user=user, defaults={"role": "OWNER"}
        )
        Subscription.objects.get_or_create(
            organization=org,
            defaults={"plan": Plan.objects.get(slug="free"), "status": "ACTIVE"},
        )
        projects = []
        for index, (client_name, project_name) in enumerate(
            (
                ("Acme", "E-commerce Alpha"),
                ("Orion", "App Orion"),
                ("Lumina", "Portal Lumina"),
            )
        ):
            client, _ = Client.objects.get_or_create(
                organization=org,
                name=client_name,
                defaults={
                    "created_by": user,
                    "email": f"contato@{client_name.lower()}.demo",
                },
            )
            project, _ = Project.objects.get_or_create(
                organization=org,
                name=project_name,
                defaults={
                    "client": client,
                    "created_by": user,
                    "status": "ACTIVE",
                    "priority": "HIGH",
                    "due_date": date.today() + timedelta(days=14 + index * 7),
                },
            )
            ProjectMember.objects.get_or_create(
                project=project, user=user, defaults={"role": "PROJECT_MANAGER"}
            )
            projects.append(project)
            for pos, status in enumerate(("DONE", "IN_PROGRESS", "TODO")):
                Task.objects.get_or_create(
                    organization=org,
                    project=project,
                    title=f"{project_name} — etapa {pos+1}",
                    defaults={"created_by": user, "status": status, "position": pos},
                )
        Revenue.objects.get_or_create(
            organization=org,
            description="Projeto Acme",
            occurred_on=date.today(),
            defaults={
                "project": projects[0],
                "client": projects[0].client,
                "amount": "5000.00",
                "created_by": user,
            },
        )
        Expense.objects.get_or_create(
            organization=org,
            description="Ferramentas",
            occurred_on=date.today(),
            defaults={"amount": "350.00", "category": "SOFTWARE", "created_by": user},
        )
        ProjectDeliverable.objects.get_or_create(
            organization=org,
            project=projects[0],
            title="Layout final",
            defaults={"created_by": user, "status": "READY_FOR_REVIEW"},
        )
        Notification.objects.get_or_create(
            organization=org,
            user=user,
            title="Bem-vindo à demonstração",
            defaults={
                "type": "PROJECT_UPDATE",
                "message": "Explore os dados preparados do DevFlow.",
            },
        )
        self.stdout.write(
            self.style.SUCCESS("Demo pronta: demo@devflow.local / DevFlowDemo!2026")
        )
