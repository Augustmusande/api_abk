from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DonnatPartSocial, FraisAdhesion, SouscriptionPartSocial
from users.models import Membre, Client

def update_membre_actif(membre):
    from .models import FraisAdhesion, SouscriptionPartSocial
    # Un membre est actif s'il a une souscription de part sociale ET des frais d'adhésion
    has_part_social = SouscriptionPartSocial.objects.filter(membre=membre).exists()
    has_frais_adhesion = FraisAdhesion.objects.filter(titulaire_membre=membre).exists()
    membre.actif = has_part_social and has_frais_adhesion
    membre.save(update_fields=["actif"])

def update_client_actif(client):
    from .models import FraisAdhesion
    has_frais_adhesion = FraisAdhesion.objects.filter(titulaire_client=client).exists()
    client.actif = has_frais_adhesion
    client.save(update_fields=["actif"])

@receiver([post_save, post_delete], sender=SouscriptionPartSocial)
def souscription_part_social_changed(sender, instance, **kwargs):
    if instance.membre:
        update_membre_actif(instance.membre)

@receiver([post_save, post_delete], sender=DonnatPartSocial)
def donnat_part_social_changed(sender, instance, **kwargs):
    # Mettre à jour le membre via la souscription
    if instance.souscription_part_social and instance.souscription_part_social.membre:
        update_membre_actif(instance.souscription_part_social.membre)

@receiver([post_save, post_delete], sender=FraisAdhesion)
def frais_adhesion_changed(sender, instance, **kwargs):
    if instance.titulaire_membre:
        update_membre_actif(instance.titulaire_membre)
    if instance.titulaire_client:
        update_client_actif(instance.titulaire_client)
