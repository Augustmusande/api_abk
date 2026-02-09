"""
Script de test pour vérifier l'envoi d'emails
Utilisez ce script pour tester manuellement l'envoi d'emails
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coopec.settings')
django.setup()

from django.core.mail import send_mail
from users.models import Cooperative
from membres.models import DonnatEpargne, DonnatPartSocial, Retrait
from credits.models import Credit, Remboursement
from rapports.models import EnvoiEmail
from rapports.email_templates import (
    envoyer_email_depot_epargne,
    envoyer_email_versement_part_sociale,
    envoyer_email_retrait,
    envoyer_email_credit,
    envoyer_email_remboursement
)


def test_email_simple():
    """Test simple d'envoi d'email"""
    coop = Cooperative.objects.first()
    if not coop:
        print("❌ Aucune coopérative trouvée. Créez d'abord une coopérative.")
        return False
    
    try:
        send_mail(
            subject='Test Email COOPEC',
            message='Ceci est un email de test.',
            from_email=coop.email if coop.email else 'test@coopec.cd',
            recipient_list=['test@example.com'],
            fail_silently=False
        )
        print("✅ Email de test envoyé avec succès!")
        print(f"   Expéditeur: {coop.email if coop.email else 'test@coopec.cd'}")
        print("   Vérifiez votre console ou le fichier emails/")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {str(e)}")
        return False


def test_email_depot_epargne(donnat_epargne_id):
    """Test d'envoi d'email pour un dépôt d'épargne"""
    try:
        donnat_epargne = DonnatEpargne.objects.get(id=donnat_epargne_id)
        envoi = envoyer_email_depot_epargne(donnat_epargne.id)
        
        if envoi and envoi.statut == 'ENVOYE':
            print(f"✅ Email envoyé avec succès pour le dépôt d'épargne #{donnat_epargne_id}")
            print(f"   Destinataire: {envoi.email_destinataire}")
            print(f"   Statut: {envoi.statut}")
            return True
        else:
            print(f"❌ Échec de l'envoi pour le dépôt d'épargne #{donnat_epargne_id}")
            if envoi:
                print(f"   Erreur: {envoi.erreur}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False


def afficher_envois_recents():
    """Affiche les 10 derniers envois d'emails"""
    envois = EnvoiEmail.objects.all()[:10]
    
    if not envois:
        print("Aucun envoi d'email trouvé.")
        return
    
    print("\n📧 Derniers envois d'emails:")
    print("-" * 80)
    for envoi in envois:
        statut_emoji = "✅" if envoi.statut == 'ENVOYE' else "❌" if envoi.statut == 'ECHEC' else "⏳"
        print(f"{statut_emoji} {envoi.date_creation.strftime('%Y-%m-%d %H:%M')} | "
              f"{envoi.email_destinataire} | {envoi.statut}")
        if envoi.erreur:
            print(f"   Erreur: {envoi.erreur}")
    print("-" * 80)


def afficher_statistiques():
    """Affiche les statistiques des envois d'emails"""
    total = EnvoiEmail.objects.count()
    envoyes = EnvoiEmail.objects.filter(statut='ENVOYE').count()
    echecs = EnvoiEmail.objects.filter(statut='ECHEC').count()
    en_attente = EnvoiEmail.objects.filter(statut='EN_ATTENTE').count()
    
    print("\n📊 Statistiques des envois d'emails:")
    print(f"   Total: {total}")
    print(f"   ✅ Envoyés: {envoyes}")
    print(f"   ❌ Échecs: {echecs}")
    print(f"   ⏳ En attente: {en_attente}")


if __name__ == '__main__':
    print("=" * 80)
    print("TEST D'ENVOI D'EMAILS - COOPEC")
    print("=" * 80)
    
    # Test simple
    print("\n1. Test d'envoi simple...")
    test_email_simple()
    
    # Afficher les statistiques
    afficher_statistiques()
    
    # Afficher les envois récents
    afficher_envois_recents()
    
    print("\n💡 Pour tester un envoi spécifique:")
    print("   python manage.py shell")
    print("   >>> from rapports.test_emails import test_email_depot_epargne")
    print("   >>> test_email_depot_epargne(1)  # Remplacez 1 par l'ID du dépôt")













