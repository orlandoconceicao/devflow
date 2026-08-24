from django.urls import path

from .views import (
    OrganizationDetailView,
    OrganizationListCreateView,
    OrganizationMemberDetailView,
    OrganizationMembersView,
    TeamInvitationAcceptView,
    TeamInvitationCreateView,
    TeamInvitationDetailView,
    TeamMessageListCreateView,
)

urlpatterns = [
    path("", OrganizationListCreateView.as_view()),
    path("<int:pk>/", OrganizationDetailView.as_view()),
    path("<int:pk>/members/", OrganizationMembersView.as_view()),
    path("<int:pk>/members/<int:membership_id>/", OrganizationMemberDetailView.as_view()),
    path("<int:pk>/team-invitations/", TeamInvitationCreateView.as_view()),
    path("team-invitations/accept/", TeamInvitationAcceptView.as_view()),
    path("team-invitations/<str:token>/", TeamInvitationDetailView.as_view()),
    path("team-chat/", TeamMessageListCreateView.as_view()),
]
