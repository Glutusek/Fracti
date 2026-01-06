from django.contrib import admin
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'subject', 'created_at', 'read')
    list_filter = ('read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(read=True)
        self.message_user(request, f"{updated} wiadomość(í) oznaczono jako przeczytane.")
    mark_as_read.short_description = "Oznacz jako przeczytane"
