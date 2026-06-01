from django.urls import path

from project.views import ProjectView, ProjectCreateView

urlpatterns = [
    path('', ProjectView.as_view(), name='project-list'),
    path('create/', ProjectCreateView.as_view(), name='project-create'),
]
