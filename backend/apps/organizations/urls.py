from django.urls import path
from .views import OrganizationDetailView,OrganizationListCreateView,OrganizationMembersView
urlpatterns=[path("",OrganizationListCreateView.as_view()),path("<int:pk>/",OrganizationDetailView.as_view()),path("<int:pk>/members/",OrganizationMembersView.as_view())]

