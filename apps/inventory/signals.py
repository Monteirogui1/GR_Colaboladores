from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification, Machine
from .utils import send_notification_logic
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    """Signal executado após criar/atualizar uma notificação"""
    if created:
        # Notificação foi criada
        print(f"Nova notificação criada: {instance.title}")
    else:
        # Notificação foi atualizada
        if instance.is_read:
            print(f"Notificação marcada como lida: {instance.title}")
