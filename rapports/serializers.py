"""
Serializers pour l'API des rapports
"""
from rest_framework import serializers
from .models import Rapport, EnvoiEmail, TypeRapport, StatutEnvoi

class RapportSerializer(serializers.ModelSerializer):
    """Serializer pour les rapports"""
    type_rapport_display = serializers.CharField(source='get_type_rapport_display', read_only=True)
    
    class Meta:
        model = Rapport
        fields = [
            'id', 'type_rapport', 'type_rapport_display',
            'periode_mois', 'periode_annee',
            'date_generation', 'contenu', 'fichier_pdf',
            'envoye', 'date_envoi'
        ]
        read_only_fields = ['date_generation', 'envoye', 'date_envoi']

class EnvoiEmailSerializer(serializers.ModelSerializer):
    """Serializer pour les envois d'emails"""
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    destinataire_type_display = serializers.CharField(source='get_destinataire_type_display', read_only=True)
    rapport = RapportSerializer(read_only=True)
    rapport_id = serializers.PrimaryKeyRelatedField(
        queryset=Rapport.objects.all(),
        source='rapport',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = EnvoiEmail
        fields = [
            'id', 'rapport', 'rapport_id',
            'destinataire_type', 'destinataire_type_display',
            'destinataire_id', 'email_destinataire',
            'sujet', 'message', 'statut', 'statut_display',
            'date_envoi', 'date_creation', 'erreur'
        ]
        read_only_fields = ['date_creation', 'date_envoi', 'statut']

class GenererRapportSerializer(serializers.Serializer):
    """Serializer pour générer un rapport"""
    type_rapport = serializers.ChoiceField(choices=TypeRapport.choices)
    periode_mois = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=12)
    periode_annee = serializers.IntegerField(required=False, allow_null=True)
    pourcentage_frais_gestion = serializers.FloatField(required=False, default=20.0)
    type_operation = serializers.ChoiceField(
        choices=[('ENTREE', 'Entrée'), ('SORTIE', 'Sortie'), ('ENTREE_APRES_CALCUL_FRAIS_GESTION', 'Entrée après calcul frais gestion')],
        required=False,
        allow_null=True
    )
    sauvegarder = serializers.BooleanField(required=False, default=True)
    envoyer_email = serializers.BooleanField(required=False, default=False)
    destinataire_email = serializers.EmailField(required=False, allow_null=True)

class EnvoyerRapportSerializer(serializers.Serializer):
    """Serializer pour envoyer un rapport par email"""
    rapport_id = serializers.IntegerField()
    destinataire_email = serializers.EmailField()
    destinataire_type = serializers.ChoiceField(
        choices=[('MEMBRE', 'Membre'), ('CLIENT', 'Client'), ('ADMIN', 'Administrateur')],
        default='ADMIN'
    )
    destinataire_id = serializers.IntegerField(required=False, allow_null=True)

