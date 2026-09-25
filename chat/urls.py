from django.urls import path

from .views import ThreadDetailView, ThreadListCreateView, ThreadMessagesView

urlpatterns = [
    path("threads/", ThreadListCreateView.as_view(), name="thread-list-create"),
    path("threads/<int:thread_id>/", ThreadDetailView.as_view(), name="thread-detail"),
    path("threads/<int:thread_id>/messages/", ThreadMessagesView.as_view(), name="thread-messages"),
]
