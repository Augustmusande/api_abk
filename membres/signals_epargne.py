from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import DonnatEpargne

@receiver(post_delete, sender=DonnatEpargne)
def update_total_donne_on_delete(sender, instance, **kwargs):
    # Rien à faire ici car total_donne est calculé dynamiquement dans le serializer
    # Mais si tu veux déclencher une action, tu peux le faire ici
    pass
