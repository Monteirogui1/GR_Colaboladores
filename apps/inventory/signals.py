from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification, Machine
from .utils import send_notification_logic
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    if not created:
        return

    # 1. Determina o queryset de máquinas-alvo
    if instance.sent_to_all:
        qs = Machine.objects.all()
    else:
        qs = instance.machines.all()
        if instance.groups.exists():
            qs = qs.union(Machine.objects.filter(group__in=instance.groups.all()))

    # 2. Envia para cada máquina
    for machine in qs.distinct():
        try:
            send_notification_logic(machine.id, instance.title, instance.message)
        except Exception as e:
            logger.error(f"[Notification] erro enviando para {machine.hostname}: {e}")
