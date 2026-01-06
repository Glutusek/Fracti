from rest_framework import serializers
from .models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer used for creating messages (does not expose `read`)."""
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']


class AdminContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for admin/list/detail views that includes `read`."""
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at', 'read']
        read_only_fields = ['id', 'created_at']
