from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import OrganizationMembership

from .models import Project, ProjectMember


class WorkApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_plans", verbosity=0)

    def user(self, email):
        return User.objects.create_user(
            email=email, password="StrongPass!2026", first_name=email.split("@")[0]
        )

    def token(self, user):
        response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "StrongPass!2026"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def org(self, user, name):
        self.token(user)
        return self.client.post(
            "/api/organizations/", {"name": name}, format="json"
        ).data

    def headers(self, org):
        return {"HTTP_X_ORGANIZATION_ID": str(org["id"])}

    def test_organization_header_requires_active_membership(self):
        member_a = self.user("tenant-a@local.test")
        org_a = self.org(member_a, "Tenant A")
        member_b = self.user("tenant-b@local.test")
        org_b = self.org(member_b, "Tenant B")

        self.token(member_a)
        self.assertEqual(
            self.client.get("/api/dashboard/", **self.headers(org_a)).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/dashboard/", **self.headers(org_b)).status_code,
            403,
        )

        user_without_workspace = self.user("no-workspace@local.test")
        self.token(user_without_workspace)
        self.assertEqual(self.client.get("/api/dashboard/").status_code, 403)

    def test_client_crud_filters_search_pagination_and_rbac(self):
        owner = self.user("owner@local.test")
        org = self.org(owner, "Alpha")
        response = self.client.post(
            "/api/clients/",
            {
                "name": "Acme",
                "email": "contact@acme.test",
                "company": "Acme Ltd",
                "status": "LEAD",
            },
            format="json",
            **self.headers(org),
        )
        self.assertEqual(response.status_code, 201)
        client_id = response.data["id"]
        self.assertEqual(
            self.client.get(
                "/api/clients/?search=Acme&status=LEAD", **self.headers(org)
            ).data["count"],
            1,
        )
        self.assertEqual(
            self.client.patch(
                f"/api/clients/{client_id}/",
                {"status": "ACTIVE"},
                format="json",
                **self.headers(org),
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/clients/",
                {"name": "Bad", "email": "invalid"},
                format="json",
                **self.headers(org),
            ).status_code,
            400,
        )
        admin = self.user("admin@local.test")
        OrganizationMembership.objects.create(
            organization_id=org["id"], user=admin, role="ADMIN"
        )
        self.token(admin)
        self.assertEqual(
            self.client.post(
                "/api/clients/",
                {"name": "Admin Client"},
                format="json",
                **self.headers(org),
            ).status_code,
            201,
        )
        member = self.user("member@local.test")
        OrganizationMembership.objects.create(
            organization_id=org["id"], user=member, role="MEMBER"
        )
        self.token(member)
        self.assertEqual(
            self.client.get("/api/clients/", **self.headers(org)).status_code, 200
        )
        self.assertEqual(
            self.client.delete(
                f"/api/clients/{client_id}/", **self.headers(org)
            ).status_code,
            403,
        )
        portal = self.user("client@local.test")
        OrganizationMembership.objects.create(
            organization_id=org["id"], user=portal, role="CLIENT"
        )
        self.token(portal)
        self.assertEqual(
            self.client.get("/api/clients/", **self.headers(org)).status_code, 403
        )

    def test_project_validation_members_dashboard_and_tenant_isolation(self):
        owner = self.user("a@local.test")
        org_a = self.org(owner, "Org A")
        client = self.client.post(
            "/api/clients/", {"name": "Client A"}, format="json", **self.headers(org_a)
        ).data
        payload = {
            "name": "Project A",
            "client": client["id"],
            "status": "ACTIVE",
            "priority": "HIGH",
            "progress": 40,
            "start_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=5)),
            "budget": "1000.00",
        }
        project = self.client.post(
            "/api/projects/", payload, format="json", **self.headers(org_a)
        )
        self.assertEqual(project.status_code, 201)
        project_id = project.data["id"]
        self.assertEqual(
            self.client.get("/api/dashboard/", **self.headers(org_a)).data[
                "active_projects"
            ],
            1,
        )
        self.assertEqual(
            self.client.get(
                "/api/projects/?search=Project&priority=HIGH", **self.headers(org_a)
            ).data["count"],
            1,
        )
        ignored = self.client.post(
            "/api/projects/",
            {**payload, "name": "Progress is server owned", "progress": 101},
            format="json",
            **self.headers(org_a),
        )
        self.assertEqual(ignored.status_code, 201)
        self.assertEqual(ignored.data["progress"], 0)
        member = self.user("member2@local.test")
        OrganizationMembership.objects.create(
            organization_id=org_a["id"], user=member, role="MEMBER"
        )
        add = self.client.post(
            f"/api/projects/{project_id}/members/",
            {"user": member.id, "role": "DEVELOPER"},
            format="json",
            **self.headers(org_a),
        )
        self.assertEqual(add.status_code, 201)
        self.token(member)
        self.assertEqual(
            self.client.get(
                f"/api/projects/{project_id}/", **self.headers(org_a)
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/projects/", payload, format="json", **self.headers(org_a)
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                f"/api/projects/{project_id}/members/",
                {"user": owner.id, "role": "MEMBER"},
                format="json",
                **self.headers(org_a),
            ).status_code,
            403,
        )
        outsider = self.user("b@local.test")
        org_b = self.org(outsider, "Org B")
        foreign_client = self.client.post(
            "/api/clients/", {"name": "Client B"}, format="json", **self.headers(org_b)
        ).data
        self.token(owner)
        self.assertEqual(
            self.client.post(
                "/api/projects/",
                {**payload, "client": foreign_client["id"]},
                format="json",
                **self.headers(org_a),
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get(
                f"/api/clients/{foreign_client['id']}/", **self.headers(org_a)
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                f"/api/projects/{project_id}/", **self.headers(org_b)
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                f"/api/projects/{project_id}/members/",
                {"user": outsider.id, "role": "MEMBER"},
                format="json",
                **self.headers(org_a),
            ).status_code,
            400,
        )
        self.assertTrue(
            ProjectMember.objects.filter(project_id=project_id, user=member).exists()
        )
        self.assertEqual(
            self.client.delete(
                f"/api/projects/{project_id}/members/{add.data['id']}/",
                **self.headers(org_a),
            ).status_code,
            204,
        )

    def test_secondary_admin_creates_project_in_selected_organization(self):
        owner = self.user("project-owner@local.test")
        selected_org = self.org(owner, "Selected Org")
        selected_client = self.client.post(
            "/api/clients/",
            {"name": "Selected Client"},
            format="json",
            **self.headers(selected_org),
        ).data
        other_org = self.org(owner, "Other Org")
        admin = self.user("project-admin@local.test")
        OrganizationMembership.objects.create(
            organization_id=selected_org["id"], user=admin, role="ADMIN"
        )

        self.token(admin)
        response = self.client.post(
            "/api/projects/",
            {
                "name": "Admin Project",
                "client": selected_client["id"],
                "status": "PLANNING",
                "priority": "MEDIUM",
            },
            format="json",
            **self.headers(selected_org),
        )
        self.assertEqual(response.status_code, 201, response.data)
        project = Project.objects.get(pk=response.data["id"])
        self.assertEqual(project.organization_id, selected_org["id"])
        self.assertEqual(project.created_by_id, admin.id)
        self.assertFalse(Project.objects.filter(organization_id=other_org["id"]).exists())

        wrong_header = self.client.post(
            "/api/projects/",
            {"name": "Wrong tenant", "client": selected_client["id"]},
            format="json",
            **self.headers(other_org),
        )
        self.assertEqual(wrong_header.status_code, 403)

    def task_setup(self):
        owner = self.user("taskowner@local.test")
        org = self.org(owner, "Task Org")
        client = self.client.post(
            "/api/clients/", {"name": "Task Client"}, format="json", **self.headers(org)
        ).data
        project = self.client.post(
            "/api/projects/",
            {"name": "Task Project", "client": client["id"], "status": "ACTIVE"},
            format="json",
            **self.headers(org),
        ).data
        member = self.user("taskmember@local.test")
        OrganizationMembership.objects.create(
            organization_id=org["id"], user=member, role="MEMBER"
        )
        self.client.post(
            f"/api/projects/{project['id']}/members/",
            {"user": member.id, "role": "DEVELOPER"},
            format="json",
            **self.headers(org),
        )
        return owner, member, org, project

    def test_tasks_move_assignees_progress_filters_and_rbac(self):
        owner, member, org, project = self.task_setup()
        label = self.client.post(
            "/api/task-labels/",
            {"name": "Backend", "color": "#6366F1"},
            format="json",
            **self.headers(org),
        ).data
        ids = []
        for index in range(4):
            response = self.client.post(
                "/api/tasks/",
                {
                    "project": project["id"],
                    "title": f"Task {index}",
                    "status": "DONE" if index < 2 else "TODO",
                    "priority": "HIGH",
                    "assignee_ids": [member.id],
                    "label_ids": [label["id"]],
                },
                format="json",
                **self.headers(org),
            )
            self.assertEqual(response.status_code, 201)
            ids.append(response.data["id"])
        self.assertEqual(Project.objects.get(pk=project["id"]).progress, 50)
        moved = self.client.patch(
            f"/api/tasks/{ids[2]}/move/",
            {"status": "DONE", "position": 0},
            format="json",
            **self.headers(org),
        )
        self.assertEqual(moved.status_code, 200)
        self.assertIsNotNone(moved.data["completed_at"])
        self.assertEqual(Project.objects.get(pk=project["id"]).progress, 75)
        reopened = self.client.patch(
            f"/api/tasks/{ids[2]}/move/",
            {"status": "REVIEW", "position": 0},
            format="json",
            **self.headers(org),
        )
        self.assertIsNone(reopened.data["completed_at"])
        self.assertEqual(Project.objects.get(pk=project["id"]).progress, 50)
        self.assertEqual(
            self.client.get(
                f"/api/tasks/?project={project['id']}&priority=HIGH&assignees__user={member.id}",
                **self.headers(org),
            ).data["count"],
            4,
        )
        self.token(member)
        self.assertEqual(
            self.client.post(
                "/api/tasks/",
                {"project": project["id"], "title": "Member task"},
                format="json",
                **self.headers(org),
            ).status_code,
            201,
        )
        outsider = self.user("taskoutside@local.test")
        foreign = self.org(outsider, "Foreign")
        self.assertEqual(
            self.client.get(
                f"/api/tasks/{ids[0]}/", **self.headers(foreign)
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.patch(
                f"/api/tasks/{ids[0]}/move/",
                {"status": "DONE", "position": 0},
                format="json",
                **self.headers(foreign),
            ).status_code,
            404,
        )
        self.token(owner)
        self.client.delete(f"/api/tasks/{ids[3]}/", **self.headers(org))
        self.assertEqual(Project.objects.get(pk=project["id"]).progress, 50)

    def test_comments_attachments_validation_and_private_download(self):
        owner, member, org, project = self.task_setup()
        task = self.client.post(
            "/api/tasks/",
            {"project": project["id"], "title": "Document task"},
            format="json",
            **self.headers(org),
        ).data
        comment = self.client.post(
            f"/api/tasks/{task['id']}/comments/",
            {"content": "Revisar documento"},
            format="json",
            **self.headers(org),
        )
        self.assertEqual(comment.status_code, 201)
        self.assertEqual(
            self.client.post(
                f"/api/tasks/{task['id']}/comments/",
                {"content": "  "},
                format="json",
                **self.headers(org),
            ).status_code,
            400,
        )
        self.token(member)
        self.assertEqual(
            self.client.patch(
                f"/api/task-comments/{comment.data['id']}/",
                {"content": "Alterado"},
                format="json",
                **self.headers(org),
            ).status_code,
            403,
        )
        self.token(owner)
        allowed = SimpleUploadedFile(
            "brief.txt", b"conteudo", content_type="text/plain"
        )
        upload = self.client.post(
            f"/api/tasks/{task['id']}/attachments/",
            {"file": allowed},
            format="multipart",
            **self.headers(org),
        )
        self.assertEqual(upload.status_code, 201)
        self.assertEqual(
            self.client.get(
                f"/api/task-attachments/{upload.data['id']}/download/",
                **self.headers(org),
            ).status_code,
            200,
        )
        blocked = SimpleUploadedFile(
            "virus.exe", b"MZ", content_type="application/octet-stream"
        )
        self.assertEqual(
            self.client.post(
                f"/api/tasks/{task['id']}/attachments/",
                {"file": blocked},
                format="multipart",
                **self.headers(org),
            ).status_code,
            400,
        )
        outsider = self.user("fileoutside@local.test")
        foreign = self.org(outsider, "File Foreign")
        self.assertEqual(
            self.client.get(
                f"/api/task-attachments/{upload.data['id']}/download/",
                **self.headers(foreign),
            ).status_code,
            404,
        )
