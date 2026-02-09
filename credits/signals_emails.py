"""
Signaux Django pour l'envoi automatique d'emails après les opérations de crédit
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Credit, Remboursement
from rapports.email_services import (
    envoyer_email_credit,
    envoyer_email_remboursement
)


@receiver(post_save, sender=Credit)
def envoyer_email_apres_credit(sender, instance, created, **kwargs):
    """
    Envoie automatiquement un email avec reçu PDF après l'octroi d'un crédit
    """
    if created:  # Seulement à la création, pas à la mise à jour
        try:
            envoyer_email_credit(instance.id)
        except Exception as e:
            # Ne pas bloquer la création si l'email échoue
            print(f"Erreur lors de l'envoi de l'email pour le crédit {instance.id}: {str(e)}")


@receiver(post_save, sender=Remboursement)
def envoyer_email_apres_remboursement(sender, instance, created, **kwargs):
    """
    Envoie automatiquement un email avec reçu PDF après un remboursement
    """
    if created:  # Seulement à la création, pas à la mise à jour
        try:
            envoyer_email_remboursement(instance.id)
        except Exception as e:
            # Ne pas bloquer la création si l'email échoue
            print(f"Erreur lors de l'envoi de l'email pour le remboursement {instance.id}: {str(e)}")













