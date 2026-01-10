from rest_framework import permissions


class IsSettlementMember(permissions.BasePermission):
    """
    Pozwala na dostęp do rozliczenia (Settlement) TYLKO osobom,
    które są na liście 'members'.
    """

    def has_object_permission(self, request, view, obj):
        # Admin ma wstęp wszędzie (opcjonalnie)
        if request.user.is_staff:
            return True

        # Sprawdź czy użytkownik jest na liście członków grupy
        return request.user in obj.members.all()