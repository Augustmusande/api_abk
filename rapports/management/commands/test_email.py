"""
Commande Django pour tester l'envoi d'emails
Usage: python manage.py test_email
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from users.models import Cooperative
from rapports.models import EnvoiEmail


class Command(BaseCommand):
    help = 'Teste l\'envoi d\'emails et affiche les statistiques'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email de destination pour le test',
            default='test@example.com'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('TEST D\'ENVOI D\'EMAILS - COOPEC'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # Vérifier la configuration
        coop = Cooperative.objects.first()
        if not coop:
            self.stdout.write(self.style.ERROR('❌ Aucune coopérative trouvée. Créez d\'abord une coopérative.'))
            return
        
        self.stdout.write(f'\n📧 Configuration:')
        self.stdout.write(f'   Expéditeur: {coop.email if coop.email else "Non configuré"}')
        self.stdout.write(f'   Backend: {settings.EMAIL_BACKEND}')
        
        # Test d'envoi simple
        email_test = options['email']
        self.stdout.write(f'\n1. Test d\'envoi simple vers {email_test}...')
        
        try:
            send_mail(
                subject='Test Email COOPEC',
                message='Ceci est un email de test depuis COOPEC.',
                from_email=coop.email if coop.email else 'test@coopec.cd',
                recipient_list=[email_test],
                fail_silently=False
            )
            self.stdout.write(self.style.SUCCESS('✅ Email de test envoyé avec succès!'))
            self.stdout.write('   Vérifiez votre console ou le dossier emails/')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors de l\'envoi: {str(e)}'))
        
        # Afficher les statistiques
        self.afficher_statistiques()
        
        # Afficher les envois récents
        self.afficher_envois_recents()
    
    def afficher_statistiques(self):
        """Affiche les statistiques des envois d'emails"""
        total = EnvoiEmail.objects.count()
        envoyes = EnvoiEmail.objects.filter(statut='ENVOYE').count()
        echecs = EnvoiEmail.objects.filter(statut='ECHEC').count()
        en_attente = EnvoiEmail.objects.filter(statut='EN_ATTENTE').count()
        
        self.stdout.write(f'\n📊 Statistiques des envois d\'emails:')
        self.stdout.write(f'   Total: {total}')
        self.stdout.write(self.style.SUCCESS(f'   ✅ Envoyés: {envoyes}'))
        self.stdout.write(self.style.ERROR(f'   ❌ Échecs: {echecs}'))
        self.stdout.write(f'   ⏳ En attente: {en_attente}')
    
    def afficher_envois_recents(self):
        """Affiche les 10 derniers envois d'emails"""
        envois = EnvoiEmail.objects.all()[:10]
        
        if not envois:
            self.stdout.write('\nAucun envoi d\'email trouvé.')
            return
        
        self.stdout.write(f'\n📧 Derniers envois d\'emails (10):')
        self.stdout.write('-' * 80)
        for envoi in envois:
            statut_emoji = "✅" if envoi.statut == 'ENVOYE' else "❌" if envoi.statut == 'ECHEC' else "⏳"
            date_str = envoi.date_creation.strftime('%Y-%m-%d %H:%M')
            self.stdout.write(f'{statut_emoji} {date_str} | {envoi.email_destinataire} | {envoi.statut}')
            if envoi.erreur:
                self.stdout.write(self.style.ERROR(f'   Erreur: {envoi.erreur}'))
        self.stdout.write('-' * 80)

