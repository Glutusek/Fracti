from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name} <{self.email}> - {self.subject or 'No subject'}"
