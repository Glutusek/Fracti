from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReceiptsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'receipts'
    verbose_name = _('Paragony')
