from rest_framework.permissions import BasePermission


class IsThreadOwner(BasePermission):
    """Allow access only when the thread belongs to the authenticated user."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id
