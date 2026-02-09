from django.contrib import admin
from .models import Cooperative, Membre, Client

@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'sigle', 'forme_juridique', 'ville', 'telephone', 'email', 'date_enregistrement')
    list_filter = ('forme_juridique', 'pays', 'province', 'date_enregistrement')
    search_fields = ('nom', 'sigle', 'numero_rccm', 'email', 'telephone')
    readonly_fields = ('date_enregistrement',)
    fieldsets = (
        ('Informations juridiques', {
            'fields': ('nom', 'sigle', 'forme_juridique', 'numero_rccm', 'numero_id_nat', 'date_creation', 'agrement')
        }),
        ('Localisation', {
            'fields': ('pays', 'province', 'ville', 'adresse', 'boite_postale')
        }),
        ('Contact', {
            'fields': ('telephone', 'email', 'site_web')
        }),
        ('Logo', {
            'fields': ('logo',)
        }),
        ('Dates', {
            'fields': ('date_enregistrement',)
        }),
    )

@admin.register(Membre)
class MembreAdmin(admin.ModelAdmin):
    list_display = ('numero_compte', 'type_membre', 'get_nom_display', 'telephone', 'email', 'actif', 'date_adhesion')
    list_filter = ('actif', 'type_membre', 'sexe', 'date_adhesion')
    search_fields = ('numero_compte', 'nom', 'prenom', 'postnom', 'raison_sociale', 'sigle', 'telephone', 'email')
    readonly_fields = ('numero_compte', 'date_adhesion', 'actif')
    
    fieldsets = (
        ('Type de membre', {
            'fields': ('type_membre',)
        }),
        ('Informations personne physique', {
            'fields': ('nom', 'postnom', 'prenom', 'sexe', 'date_naissance'),
            'classes': ('collapse',)
        }),
        ('Informations personne morale', {
            'fields': ('raison_sociale', 'sigle', 'numero_immatriculation', 'forme_juridique', 'representant_legal', 'secteur_activite'),
            'classes': ('collapse',)
        }),
        ('Informations communes', {
            'fields': ('adresse', 'telephone', 'email')
        }),
        ('Statut', {
            'fields': ('numero_compte', 'date_adhesion', 'actif')
        }),
    )
    
    def get_nom_display(self, obj):
        """Affiche le nom selon le type de membre"""
        if obj.type_membre == 'MORALE':
            return obj.raison_sociale or obj.sigle or 'Entreprise'
        else:
            return f"{obj.nom or ''} {obj.prenom or ''}".strip() or '-'
    get_nom_display.short_description = 'Nom / Raison sociale'

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('numero_compte', 'nom', 'prenom', 'telephone', 'email', 'actif', 'date_inscription')
    list_filter = ('actif', 'sexe', 'date_inscription')
    search_fields = ('numero_compte', 'nom', 'prenom', 'postnom', 'telephone', 'email')
    readonly_fields = ('numero_compte', 'date_inscription', 'actif')
