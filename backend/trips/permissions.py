from rest_framework import permissions


class IsTripOwnerOrSettlementMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if obj.owner == request.user:
            return True
        if obj.settlement and request.user in obj.settlement.members.all():
            return True
        return False
