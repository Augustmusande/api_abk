"""
Configuration de l'admin pour l'application rapports
"""
from django.contrib import admin
from .models import Rapport, EnvoiEmail


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ['id', 'type_rapport', 'periode_mois', 'periode_annee', 'date_generation', 'envoye']
    list_filter = ['type_rapport', 'envoye', 'date_generation']
    search_fields = ['type_rapport', 'periode_annee']
    readonly_fields = ['date_generation', 'date_envoi']


@admin.register(EnvoiEmail)
class EnvoiEmailAdmin(admin.ModelAdmin):
    list_display = ['id', 'email_destinataire', 'sujet', 'statut', 'date_creation', 'date_envoi']
    list_filter = ['statut', 'destinataire_type', 'date_creation']
    search_fields = ['email_destinataire', 'sujet']
    readonly_fields = ['date_creation', 'date_envoi']
