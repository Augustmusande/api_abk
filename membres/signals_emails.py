"""
Signaux Django pour l'envoi automatique d'emails après les opérations
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DonnatEpargne, DonnatPartSocial, Retrait, FraisAdhesion
from rapports.email_services import (
    envoyer_email_depot_epargne,
    envoyer_email_versement_part_sociale,
    envoyer_email_retrait,
    envoyer_email_frais_adhesion
)


@receiver(post_save, sender=DonnatEpargne)
def envoyer_email_apres_depot_epargne(sender, instance, created, **kwargs):
    """
    Envoie automatiquement un email avec reçu PDF après la création d'un dépôt d'épargne
    """
    if created:  # Seulement à la création, pas à la mise à jour
        try:
            envoyer_email_depot_epargne(instance.id)
        except Exception as e:
            # Ne pas bloquer la création si l'email échoue
            print(f"Erreur lors de l'envoi de l'email pour le dépôt d'épargne {instance.id}: {str(e)}")


@receiver(post_save, sender=DonnatPartSocial)
def envoyer_email_apres_versement_part_sociale(sender, instance, created, **kwargs):
    """
    Envoie automatiquement un email avec reçu PDF après la création d'un versement de part sociale
    """
    if created:  # Seulement à la création, pas à la mise à jour
        try:
            envoyer_email_versement_part_sociale(instance.id)
        except Exception as e:
            # Ne pas bloquer la création si l'email échoue
            print(f"Erreur lors de l'envoi de l'email pour le versement de part sociale {instance.id}: {str(e)}")


@receiver(post_save, sender=Retrait)
def envoyer_email_apres_retrait(sender, instance, created, **kwargs):
    """
    Envoie automatiquement un email avec reçu PDF après la création d'un retrait
    """
    if created:  # Seulement à la création, pas à la mise à jour
        try:
            envoyer_email_retrait(instance.id)
        except Exception as e:
            # Ne pas bloquer la création si l'email échoue
            print(f"Erreur lors de l'envoi de l'email pour le retrait {instance.id}: {str(e)}")


@receiver(post_save, sender=FraisAdhesion)
def envoyer_email_apres_frais_adhesion(sender, instance, created, **kwargs):
    """
    Envoie automatiquement un email avec reçu PDF après le paiement de frais d'adhésion
    """
    if created:  # Seulement à la création, pas à la mise à jour
        try:
            envoyer_email_frais_adhesion(instance.id)
        except Exception as e:
            # Ne pas bloquer la création si l'email échoue
            print(f"Erreur lors de l'envoi de l'email pour les frais d'adhésion {instance.id}: {str(e)}")


