"""
Modèles pour la gestion des rapports et envois d'emails
"""
from django.db import models
from django.utils import timezone
from decimal import Decimal

class TypeRapport(models.TextChoices):
    """Types de rapports disponibles"""
    RAPPORT_MENSUEL = 'MENSUEL', 'Rapport mensuel'
    RAPPORT_ANNUEL = 'ANNUEL', 'Rapport annuel'
    RAPPORT_APPORTS = 'APPORTS', 'Rapport des apports'
    RAPPORT_INTERETS = 'INTERETS', 'Rapport des intérêts'
    RAPPORT_CAISSE = 'CAISSE', 'Rapport de caisse'
    RAPPORT_CREDITS = 'CREDITS', 'Rapport des crédits'
    RAPPORT_OPERATIONS = 'OPERATIONS', 'Rapport des opérations'

class StatutEnvoi(models.TextChoices):
    """Statuts d'envoi d'email"""
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    EN_COURS = 'EN_COURS', 'En cours'
    ENVOYE = 'ENVOYE', 'Envoyé'
    ECHEC = 'ECHEC', 'Échec'

class Rapport(models.Model):
    """
    Modèle pour stocker les rapports générés
    """
    type_rapport = models.CharField(
        max_length=20,
        choices=TypeRapport.choices,
        help_text="Type de rapport"
    )
    periode_mois = models.IntegerField(null=True, blank=True, help_text="Mois (1-12)")
    periode_annee = models.IntegerField(help_text="Année")
    date_generation = models.DateTimeField(auto_now_add=True, help_text="Date de génération")
    contenu = models.JSONField(help_text="Contenu du rapport (JSON)")
    fichier_pdf = models.FileField(
        upload_to='rapports/pdf/',
        null=True,
        blank=True,
        help_text="Fichier PDF du rapport (optionnel)"
    )
    envoye = models.BooleanField(default=False, help_text="Rapport envoyé par email")
    date_envoi = models.DateTimeField(null=True, blank=True, help_text="Date d'envoi")
    
    class Meta:
        ordering = ['-date_generation']
        verbose_name = 'Rapport'
        verbose_name_plural = 'Rapports'
    
    def __str__(self):
        return f"{self.get_type_rapport_display()} - {self.periode_annee}"

class EnvoiEmail(models.Model):
    """
    Modèle pour suivre les envois d'emails
    """
    rapport = models.ForeignKey(
        Rapport,
        on_delete=models.CASCADE,
        related_name='envois',
        null=True,
        blank=True,
        help_text="Rapport associé (si applicable)"
    )
    destinataire_type = models.CharField(
        max_length=10,
        choices=[('MEMBRE', 'Membre'), ('CLIENT', 'Client'), ('ADMIN', 'Administrateur')],
        help_text="Type de destinataire"
    )
    destinataire_id = models.IntegerField(help_text="ID du destinataire (membre ou client)")
    email_destinataire = models.EmailField(help_text="Email du destinataire")
    sujet = models.CharField(max_length=255, help_text="Sujet de l'email")
    message = models.TextField(help_text="Message de l'email")
    statut = models.CharField(
        max_length=20,
        choices=StatutEnvoi.choices,
        default=StatutEnvoi.EN_ATTENTE,
        help_text="Statut de l'envoi"
    )
    date_envoi = models.DateTimeField(null=True, blank=True, help_text="Date d'envoi")
    date_creation = models.DateTimeField(auto_now_add=True, help_text="Date de création")
    erreur = models.TextField(null=True, blank=True, help_text="Message d'erreur si échec")
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Envoi Email'
        verbose_name_plural = 'Envois Emails'
    
    def __str__(self):
        return f"Email à {self.email_destinataire} - {self.statut}"
