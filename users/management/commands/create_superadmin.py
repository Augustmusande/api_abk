"""
Commande Django pour créer le superadmin initial
Usage: python manage.py create_superadmin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée le superadmin initial (le premier compte créé devient automatiquement superadmin)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nom d\'utilisateur du superadmin',
            default='superadmin'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email du superadmin',
            default='superadmin@coopec.com'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Mot de passe du superadmin',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options.get('password')
        
        # Vérifier si un superadmin existe déjà
        if User.objects.filter(user_type='SUPERADMIN').exists():
            self.stdout.write(
                self.style.WARNING('Un superadmin existe déjà dans le système.')
            )
            return
        
        # Si aucun utilisateur n'existe, le premier devient superadmin
        if not User.objects.exists():
            if not password:
                password = 'SuperAdmin123!@#'
                self.stdout.write(
                    self.style.WARNING(
                        f'Mot de passe non fourni. Utilisation du mot de passe par défaut: {password}'
                    )
                )
                self.stdout.write(
                    self.style.WARNING('⚠️  CHANGEZ CE MOT DE PASSE IMMÉDIATEMENT EN PRODUCTION!')
                )
            
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    user_type='SUPERADMIN',
                    is_staff=True,
                    is_superuser=True,
                    is_active=True
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Superadmin créé avec succès!\n'
                        f'   Username: {username}\n'
                        f'   Email: {email}\n'
                        f'   Type: SUPERADMIN'
                    )
                )
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Des utilisateurs existent déjà. Le premier utilisateur doit être créé manuellement.'
                )
            )

