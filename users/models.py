from django.db import models
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from datetime import datetime


class Cooperative(models.Model):
    """Modèle pour la coopérative"""
    FORME_JURIDIQUE_CHOICES = [
        ('COOPEC', 'Cooperative d\'epargne et de credit'),
        ('COOP_AGR', 'Cooperative agricole'),
        ('MUTUELLE', 'Mutuelle'),
        ('AUTRE', 'Autre'),
    ]
    
    nom = models.CharField(max_length=255)
    sigle = models.CharField(max_length=50, blank=True, null=True)
    forme_juridique = models.CharField(max_length=20, choices=FORME_JURIDIQUE_CHOICES, default='COOPEC')
    numero_rccm = models.CharField(max_length=100, blank=True, null=True, verbose_name='N° RCCM')
    numero_id_nat = models.CharField(max_length=100, blank=True, null=True, verbose_name='N° Identification nationale')
    date_creation = models.DateField(blank=True, null=True)
    agrement = models.CharField(max_length=100, blank=True, null=True, verbose_name='N° d\'agrement ministeriel')
    pays = models.CharField(max_length=100, default='RDC')
    province = models.CharField(max_length=100)
    ville = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    boite_postale = models.CharField(max_length=50, blank=True, null=True)
    telephone = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    site_web = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='cooperatives/logos/', blank=True, null=True, help_text='Logo de la coopérative (formats acceptés: JPG, PNG, SVG)')
    date_enregistrement = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Coopérative'
        verbose_name_plural = 'Coopératives'
        ordering = ['-date_enregistrement']

    def __str__(self):
        return f"{self.nom} ({self.sigle or 'sans sigle'})"




class Membre(models.Model):
    TYPE_MEMBRE_CHOICES = [
        ('PHYSIQUE', 'Personne physique'),
        ('MORALE', 'Personne morale (Entreprise)'),
    ]
    
    # Champs communs
    numero_compte = models.CharField(max_length=20, unique=True, editable=False)
    type_membre = models.CharField(max_length=10, choices=TYPE_MEMBRE_CHOICES, default='PHYSIQUE', help_text="Type de membre : personne physique ou morale")
    adresse = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=50)
    email = models.EmailField(
    max_length=99,   # ✅ valeur sûre MySQL + utf8mb4
    blank=True,
    null=True,
    unique=True,
    help_text="Email (optionnel pour superadmin/admin, obligatoire pour membre/client)"
)
    password = models.CharField(max_length=128, blank=False, null=False, help_text="Mot de passe (sera hashé automatiquement) - Minimum 6 caractères avec lettres, chiffres et caractères spéciaux")
    date_adhesion = models.DateField(auto_now_add=True)
    annee_adhesion = models.PositiveIntegerField(blank=True, null=True, help_text="Année d'adhésion (utilisée pour la génération du numéro de compte. Si non renseignée, utilise l'année courante)")
    ville = models.CharField(max_length=100, blank=True, null=True, help_text="Ville de résidence")
    profession = models.CharField(max_length=100, blank=True, null=True, help_text="Profession")
    photo_profil = models.ImageField(upload_to='membres/photos/', blank=True, null=True, help_text="Photo de profil (formats acceptés: JPG, PNG)")
    actif = models.BooleanField(default=False, editable=False)
    
    # Champs pour personne physique
    nom = models.CharField(max_length=100, blank=True, null=True, help_text="Nom de famille (personne physique uniquement)")
    postnom = models.CharField(max_length=100, blank=True, null=True, help_text="Postnom (personne physique uniquement)")
    prenom = models.CharField(max_length=100, blank=True, null=True, help_text="Prénom (personne physique uniquement)")
    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], blank=True, null=True, help_text="Sexe (personne physique uniquement)")
    date_naissance = models.DateField(blank=True, null=True, help_text="Date de naissance (personne physique uniquement)")
    
    # Champs pour personne morale (entreprise)
    raison_sociale = models.CharField(max_length=255, blank=True, null=True, help_text="Raison sociale (personne morale uniquement)")
    sigle = models.CharField(max_length=50, blank=True, null=True, help_text="Sigle de l'entreprise (personne morale uniquement)")
    numero_immatriculation = models.CharField(max_length=100, blank=True, null=True, help_text="Numéro d'immatriculation RCCM (personne morale uniquement)")
    forme_juridique = models.CharField(max_length=100, blank=True, null=True, help_text="Forme juridique (SARL, SA, etc.) (personne morale uniquement)")
    representant_legal = models.CharField(max_length=255, blank=True, null=True, help_text="Nom du représentant légal (personne morale uniquement)")
    secteur_activite = models.CharField(max_length=255, blank=True, null=True, help_text="Secteur d'activité (personne morale uniquement)")

    def save(self, *args, **kwargs):
        # Génération du numéro de compte si nécessaire
        if not self.numero_compte:
            # Utiliser annee_adhesion si renseignée, sinon l'année courante
            annee = self.annee_adhesion if self.annee_adhesion else datetime.now().year
            dernier = Membre.objects.filter(numero_compte__startswith=f"MB-{annee}-").order_by('-numero_compte').first()
            if dernier:
                dernier_num = int(dernier.numero_compte.split('-')[-1])
            else:
                dernier_num = 0
            nouveau_num = str(dernier_num + 1).zfill(5)
            self.numero_compte = f"MB-{annee}-{nouveau_num}"

        # Sauvegarde initiale pour obtenir une PK avant d'interroger les relations
        super().save(*args, **kwargs)

        # Vérification des conditions d'activation (part sociale ET frais d'adhésion)
        from membres.models import SouscriptionPartSocial, FraisAdhesion
        has_part_social = SouscriptionPartSocial.objects.filter(membre=self).exists()
        has_frais_adhesion = FraisAdhesion.objects.filter(titulaire_membre=self).exists()
        nouveau_actif = has_part_social and has_frais_adhesion

        # Si la valeur a changé, mettre à jour uniquement le champ 'actif'
        if self.actif != nouveau_actif:
            self.actif = nouveau_actif
            super().save(update_fields=['actif'])

    def calculer_score_moyen(self):
        """
        Calcule le score moyen basé sur tous les crédits du membre.
        Retourne un tuple (score_moyen, pourcentage, mention)
        """
        from credits.models import Credit
        from decimal import Decimal
        
        credits = Credit.objects.filter(membre=self)
        
        if not credits.exists():
            return {
                'score_moyen': 10.0,
                'pourcentage': 100.0,
                'mention': 'A+',
                'nombre_credits': 0
            }
        
        total_score = Decimal('0.0')
        nombre_credits = 0
        
        for credit in credits:
            # Chaque crédit a un score par défaut de 10/10 à l'octroi
            score = credit.score if hasattr(credit, 'score') else Decimal('10.0')
            total_score += score
            nombre_credits += 1
        
        score_moyen = float(total_score / Decimal(str(nombre_credits)))
        pourcentage = score_moyen * 10  # Convertir sur 100 (10/10 = 100%)
        
        # Déterminer la mention selon le score moyen
        if 9.0 <= score_moyen <= 10.0:
            mention = 'A+'
        elif 7.0 <= score_moyen < 9.0:
            mention = 'A'
        elif 5.0 <= score_moyen < 7.0:
            mention = 'B'
        elif 3.0 <= score_moyen < 5.0:
            mention = 'C'
        elif 1.0 <= score_moyen < 3.0:
            mention = 'D'
        else:
            mention = 'D'
        
        return {
            'score_moyen': round(score_moyen, 2),
            'pourcentage': round(pourcentage, 2),
            'mention': mention,
            'nombre_credits': nombre_credits
        }
    
    def get_mention_score(self):
        """
        Retourne la mention et le pourcentage du score sous forme de chaîne.
        Exemple: "A+ avec 95%"
        """
        score_data = self.calculer_score_moyen()
        return f"{score_data['mention']} avec {score_data['pourcentage']}%"
    
    def __str__(self):
        if self.type_membre == 'MORALE':
            return f"{self.numero_compte} - {self.raison_sociale or self.sigle or 'Entreprise'}"
        else:
            nom_complet = f"{self.nom or ''} {self.prenom or ''}".strip()
            return f"{self.numero_compte} - {nom_complet if nom_complet else 'Personne physique'}"
    
    class Meta:
        ordering = ['-date_adhesion', '-id']
        verbose_name = 'Membre'
        verbose_name_plural = 'Membres'


class Client(models.Model):
    numero_compte = models.CharField(max_length=20, unique=True, editable=False)
    nom = models.CharField(max_length=100)
    postnom = models.CharField(max_length=100, blank=True, null=True)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    date_naissance = models.DateField(blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=50)
    email = models.EmailField(
    max_length=99,   # ✅ valeur sûre MySQL + utf8mb4
    blank=True,
    null=True,
    unique=True,
    help_text="Email (optionnel pour superadmin/admin, obligatoire pour membre/client)"
)
    password = models.CharField(max_length=128, blank=False, null=False, help_text="Mot de passe (sera hashé automatiquement) - Minimum 6 caractères avec lettres, chiffres et caractères spéciaux")
    profession = models.CharField(max_length=100, blank=True, null=True, help_text="Profession")
    date_inscription = models.DateField(auto_now_add=True)
    annee_adhesion = models.PositiveIntegerField(blank=True, null=True, help_text="Année d'adhésion (utilisée pour la génération du numéro de compte. Si non renseignée, utilise l'année courante)")
    ville = models.CharField(max_length=100, blank=True, null=True, help_text="Ville de résidence")
    photo_profil = models.ImageField(upload_to='clients/photos/', blank=True, null=True, help_text="Photo de profil (formats acceptés: JPG, PNG)")
    parrain = models.ForeignKey(Membre, on_delete=models.SET_NULL, null=True, blank=True, help_text="Membre qui a recommandé le client")
    actif = models.BooleanField(default=False, editable=False)

    def save(self, *args, **kwargs):
        # Génération du numéro de compte si nécessaire
        if not self.numero_compte:
            # Utiliser annee_adhesion si renseignée, sinon l'année courante
            annee = self.annee_adhesion if self.annee_adhesion else datetime.now().year
            dernier = Client.objects.filter(numero_compte__startswith=f"CL-{annee}-").order_by('-numero_compte').first()
            if dernier:
                dernier_num = int(dernier.numero_compte.split('-')[-1])
            else:
                dernier_num = 0
            nouveau_num = str(dernier_num + 1).zfill(5)
            self.numero_compte = f"CL-{annee}-{nouveau_num}"

        # Sauvegarde initiale pour obtenir une PK avant d'interroger les relations
        super().save(*args, **kwargs)

        # Vérification des conditions d'activation (frais d'adhésion)
        from membres.models import FraisAdhesion
        has_frais_adhesion = FraisAdhesion.objects.filter(titulaire_client=self).exists()
        nouveau_actif = has_frais_adhesion

        # Si la valeur a changé, mettre à jour uniquement le champ 'actif'
        if self.actif != nouveau_actif:
            self.actif = nouveau_actif
            super().save(update_fields=['actif'])

    def calculer_score_moyen(self):
        """
        Calcule le score moyen basé sur tous les crédits du client.
        Retourne un tuple (score_moyen, pourcentage, mention)
        """
        from credits.models import Credit
        from decimal import Decimal
        
        credits = Credit.objects.filter(client=self)
        
        if not credits.exists():
            return {
                'score_moyen': 10.0,
                'pourcentage': 100.0,
                'mention': 'A+',
                'nombre_credits': 0
            }
        
        total_score = Decimal('0.0')
        nombre_credits = 0
        
        for credit in credits:
            # Chaque crédit a un score par défaut de 10/10 à l'octroi
            score = credit.score if hasattr(credit, 'score') else Decimal('10.0')
            total_score += score
            nombre_credits += 1
        
        score_moyen = float(total_score / Decimal(str(nombre_credits)))
        pourcentage = score_moyen * 10  # Convertir sur 100 (10/10 = 100%)
        
        # Déterminer la mention selon le score moyen
        if 9.0 <= score_moyen <= 10.0:
            mention = 'A+'
        elif 7.0 <= score_moyen < 9.0:
            mention = 'A'
        elif 5.0 <= score_moyen < 7.0:
            mention = 'B'
        elif 3.0 <= score_moyen < 5.0:
            mention = 'C'
        elif 1.0 <= score_moyen < 3.0:
            mention = 'D'
        else:
            mention = 'D'
        
        return {
            'score_moyen': round(score_moyen, 2),
            'pourcentage': round(pourcentage, 2),
            'mention': mention,
            'nombre_credits': nombre_credits
        }
    
    def get_mention_score(self):
        """
        Retourne la mention et le pourcentage du score sous forme de chaîne.
        Exemple: "A+ avec 95%"
        """
        score_data = self.calculer_score_moyen()
        return f"{score_data['mention']} avec {score_data['pourcentage']}%"
    
    def __str__(self):
        return f"{self.numero_compte} - {self.nom} {self.prenom}"
    
    class Meta:
        ordering = ['-date_inscription', '-id']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'



class UserManager(BaseUserManager):
    """Manager personnalisé pour le modèle User"""
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """Crée et enregistre un utilisateur avec le username et password fournis"""
        if not username:
            raise ValueError('Le username doit être défini')
        
        if email:
            email = self.normalize_email(email)
        
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Crée et enregistre un superutilisateur"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'SUPERADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superuser doit avoir is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle User personnalisé avec 4 types d'utilisateurs :
    - SUPERADMIN : Le premier compte créé, le boss du système
    - ADMIN : Comptes pour caissiers, trésoriers, etc. (utilisateurs permanents)
    - MEMBRE : Membres de la coopérative
    - CLIENT : Clients de la coopérative
    """
    USER_TYPE_CHOICES = [
        ('SUPERADMIN', 'Super Administrateur'),
        ('ADMIN', 'Administrateur'),
        ('MEMBRE', 'Membre'),
        ('CLIENT', 'Client'),
    ]
    email = models.EmailField(
    max_length=99,   # ✅ valeur sûre MySQL + utf8mb4
    blank=True,
    null=True,
    unique=True,
    help_text="Email (optionnel pour superadmin/admin, obligatoire pour membre/client)"
)

    username = models.CharField(max_length=150, unique=True, help_text="Nom d'utilisateur unique")
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    # Type d'utilisateur
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='MEMBRE',
        help_text="Type d'utilisateur"
    )
    
    # Relations avec Membre et Client (optionnelles)
    membre = models.OneToOneField(
        'Membre',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_account',
        help_text="Lien vers le profil Membre (si user_type=MEMBRE)"
    )
    client = models.OneToOneField(
        'Client',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_account',
        help_text="Lien vers le profil Client (si user_type=CLIENT)"
    )
    
    # Champs Django standards
    is_staff = models.BooleanField(
        default=False,
        help_text="Indique si l'utilisateur peut accéder à l'interface d'administration"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indique si ce compte utilisateur est actif"
    )
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']
    
    def __str__(self):
        if self.user_type == 'SUPERADMIN':
            return f"SuperAdmin: {self.username}"
        elif self.user_type == 'ADMIN':
            return f"Admin: {self.username}"
        elif self.user_type == 'MEMBRE' and self.membre:
            return f"Membre: {self.membre.numero_compte}"
        elif self.user_type == 'CLIENT' and self.client:
            return f"Client: {self.client.numero_compte}"
        else:
            return f"{self.get_user_type_display()}: {self.username}"
    
    def get_full_name(self):
        if self.user_type == 'MEMBRE' and self.membre:
            if self.membre.type_membre == 'MORALE':
                return self.membre.raison_sociale or self.membre.sigle or 'Entreprise'
            else:
                return f"{self.membre.nom or ''} {self.membre.prenom or ''}".strip()
        elif self.user_type == 'CLIENT' and self.client:
            return f"{self.client.nom} {self.client.prenom}"
        else:
            return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_short_name(self):
        if self.user_type == 'MEMBRE' and self.membre:
            return self.membre.prenom or self.membre.nom or self.username
        elif self.user_type == 'CLIENT' and self.client:
            return self.client.prenom or self.client.nom or self.username
        else:
            return self.first_name or self.username
    
    def save(self, *args, **kwargs):
        # Ne changer le type en SUPERADMIN que si aucun type n'a été explicitement défini
        # et que c'est le premier utilisateur créé (pas de User existant du tout)
        if not self.pk:
            # Vérifier si c'est le tout premier utilisateur à être créé
            if not User.objects.exists():
                # Seulement si user_type n'a pas été explicitement défini
                # Vérifier si user_type a été passé explicitement dans kwargs ou si c'est la valeur par défaut
                if not hasattr(self, '_skip_superadmin_auto_assignment'):
                    self.user_type = 'SUPERADMIN'
                    self.is_staff = True
                    self.is_superuser = True
        
        super().save(*args, **kwargs)

