"""
Vues pour l'API des rapports et envois d'emails
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from coopec.pagination import StandardResultsSetPagination
from .models import Rapport, EnvoiEmail
from .serializers import (
    RapportSerializer,
    EnvoiEmailSerializer,
    GenererRapportSerializer,
    EnvoyerRapportSerializer
)
from .services import (
    generer_rapport_apports,
    generer_rapport_interets,
    generer_rapport_caisse,
    generer_rapport_credits,
    generer_rapport_operations,
    generer_rapport_mensuel,
    generer_rapport_annuel,
    sauvegarder_rapport,
    envoyer_email_rapport,
    envoyer_rapport_membre
)
from .receipts import (
    generate_receipt_depot_epargne,
    generate_receipt_versement_part_sociale,
    generate_receipt_retrait,
    generate_receipt_credit,
    generate_receipt_remboursement,
    generate_receipt_frais_adhesion,
    generate_receipt_transaction
)
from .account_statement import generate_account_statement
from datetime import date

@extend_schema(tags=['Rapports'])
class RapportViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les rapports
    """
    queryset = Rapport.objects.all()
    serializer_class = RapportSerializer
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        summary="Générer un rapport",
        description="Génère un nouveau rapport selon le type spécifié (MENSUEL, ANNUEL, APPORTS, INTERETS, CAISSE, CREDITS, OPERATIONS)",
        request=GenererRapportSerializer,
        tags=['Rapports']
    )
    @action(detail=False, methods=['post'])
    def generer(self, request):
        """
        Génère un nouveau rapport
        
        POST /api/rapports/generer/
        {
            "type_rapport": "MENSUEL",
            "periode_mois": 12,
            "periode_annee": 2025,
            "sauvegarder": true,
            "envoyer_email": false
        }
        """
        serializer = GenererRapportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        type_rapport = data['type_rapport']
        periode_mois = data.get('periode_mois')
        periode_annee = data.get('periode_annee') or date.today().year
        sauvegarder = data.get('sauvegarder', True)
        envoyer_email = data.get('envoyer_email', False)
        destinataire_email = data.get('destinataire_email')
        
        try:
            # Générer le rapport selon le type
            if type_rapport == 'APPORTS':
                contenu = generer_rapport_apports(periode_mois, periode_annee)
            elif type_rapport == 'INTERETS':
                pourcentage = data.get('pourcentage_frais_gestion', 20.0)
                contenu = generer_rapport_interets(pourcentage, periode_mois, periode_annee)
            elif type_rapport == 'CAISSE':
                contenu = generer_rapport_caisse()
            elif type_rapport == 'CREDITS':
                contenu = generer_rapport_credits()
            elif type_rapport == 'OPERATIONS':
                type_operation = data.get('type_operation')
                contenu = generer_rapport_operations(periode_mois, periode_annee, type_operation)
            elif type_rapport == 'MENSUEL':
                if not periode_mois:
                    return Response(
                        {'error': 'periode_mois est requis pour un rapport mensuel'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                contenu = generer_rapport_mensuel(periode_mois, periode_annee)
            elif type_rapport == 'ANNUEL':
                contenu = generer_rapport_annuel(periode_annee)
            else:
                return Response(
                    {'error': f'Type de rapport non supporté: {type_rapport}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Sauvegarder si demandé
            rapport = None
            if sauvegarder:
                rapport = sauvegarder_rapport(type_rapport, contenu, periode_mois, periode_annee)
                contenu['rapport_id'] = rapport.id
            
            # Envoyer par email si demandé
            envoi = None
            if envoyer_email and destinataire_email:
                if not rapport:
                    rapport = sauvegarder_rapport(type_rapport, contenu, periode_mois, periode_annee)
                envoi = envoyer_email_rapport(rapport, destinataire_email)
                contenu['envoi_id'] = envoi.id
            
            return Response({
                'message': 'Rapport généré avec succès',
                'rapport': contenu,
                'rapport_sauvegarde': RapportSerializer(rapport).data if rapport else None,
                'envoi': EnvoiEmailSerializer(envoi).data if envoi else None
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du rapport: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def envoyer(self, request, pk=None):
        """
        Envoie un rapport existant par email
        
        POST /api/rapports/{id}/envoyer/
        {
            "destinataire_email": "membre@example.com",
            "destinataire_type": "MEMBRE",
            "destinataire_id": 1
        }
        """
        rapport = self.get_object()
        serializer = EnvoyerRapportSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        envoi = envoyer_email_rapport(
            rapport,
            data['destinataire_email'],
            data.get('destinataire_type', 'ADMIN'),
            data.get('destinataire_id')
        )
        
        return Response({
            'message': 'Email envoyé avec succès' if envoi.statut == 'ENVOYE' else f'Erreur: {envoi.erreur}',
            'envoi': EnvoiEmailSerializer(envoi).data
        }, status=status.HTTP_200_OK)

class EnvoiEmailViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter les envois d'emails (lecture seule)
    """
    queryset = EnvoiEmail.objects.all()
    serializer_class = EnvoiEmailSerializer
    pagination_class = StandardResultsSetPagination
    
    @action(detail=False, methods=['get'])
    def par_statut(self, request):
        """
        Liste les envois par statut
        
        GET /api/envois-emails/par_statut/?statut=ENVOYE
        """
        statut = request.query_params.get('statut')
        if statut:
            queryset = self.queryset.filter(statut=statut)
        else:
            queryset = self.queryset
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

@extend_schema(tags=['Rapports'])
class ReceiptViewSet(viewsets.ViewSet):
    """
    ViewSet pour générer et télécharger les reçus PDF
    """
    
    @extend_schema(
        summary="Reçu de dépôt d'épargne",
        description="Génère un reçu PDF pour un dépôt d'épargne",
        parameters=[
            OpenApiParameter(name='donnat_epargne_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True, description='ID du dépôt d\'épargne')
        ],
        tags=['Rapports']
    )
    @action(detail=False, methods=['get'])
    def depot_epargne(self, request):
        """
        Génère un reçu PDF pour un dépôt d'épargne
        
        GET /api/receipts/depot_epargne/?donnat_epargne_id=1
        """
        donnat_epargne_id = request.query_params.get('donnat_epargne_id')
        if not donnat_epargne_id:
            return Response(
                {'error': 'donnat_epargne_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pdf_buffer = generate_receipt_depot_epargne(int(donnat_epargne_id))
            if not pdf_buffer:
                return Response(
                    {'error': 'Dépôt d\'épargne non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_depot_epargne_{donnat_epargne_id}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du reçu: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Reçu de versement de part sociale",
        description="Génère un reçu PDF pour un versement de part sociale",
        parameters=[
            OpenApiParameter(name='donnat_part_social_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True, description='ID du versement de part sociale')
        ],
        tags=['Rapports']
    )
    @action(detail=False, methods=['get'])
    def versement_part_sociale(self, request):
        """
        Génère un reçu PDF pour un versement de part sociale
        
        GET /api/receipts/versement_part_sociale/?donnat_part_social_id=1
        """
        donnat_part_social_id = request.query_params.get('donnat_part_social_id')
        if not donnat_part_social_id:
            return Response(
                {'error': 'donnat_part_social_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pdf_buffer = generate_receipt_versement_part_sociale(int(donnat_part_social_id))
            if not pdf_buffer:
                return Response(
                    {'error': 'Versement de part sociale non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_versement_part_sociale_{donnat_part_social_id}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du reçu: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Reçu de retrait",
        description="Génère un reçu PDF pour un retrait d'épargne",
        parameters=[
            OpenApiParameter(name='retrait_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True, description='ID du retrait')
        ],
        tags=['Rapports']
    )
    @action(detail=False, methods=['get'])
    def retrait(self, request):
        """
        Génère un reçu PDF pour un retrait
        
        GET /api/receipts/retrait/?retrait_id=1
        """
        retrait_id = request.query_params.get('retrait_id')
        if not retrait_id:
            return Response(
                {'error': 'retrait_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pdf_buffer = generate_receipt_retrait(int(retrait_id))
            if not pdf_buffer:
                return Response(
                    {'error': 'Retrait non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_retrait_{retrait_id}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du reçu: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Reçu de crédit",
        description="Génère un reçu PDF pour un crédit octroyé",
        parameters=[
            OpenApiParameter(name='credit_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True, description='ID du crédit')
        ],
        tags=['Rapports']
    )
    @action(detail=False, methods=['get'])
    def credit(self, request):
        """
        Génère un reçu PDF pour un crédit octroyé
        
        GET /api/receipts/credit/?credit_id=1
        """
        credit_id = request.query_params.get('credit_id')
        if not credit_id:
            return Response(
                {'error': 'credit_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pdf_buffer = generate_receipt_credit(int(credit_id))
            if not pdf_buffer:
                return Response(
                    {'error': 'Crédit non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_credit_{credit_id}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du reçu: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Reçu de remboursement",
        description="Génère un reçu PDF pour un remboursement de crédit",
        parameters=[
            OpenApiParameter(name='remboursement_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True, description='ID du remboursement')
        ],
        tags=['Rapports']
    )
    @action(detail=False, methods=['get'])
    def remboursement(self, request):
        """
        Génère un reçu PDF pour un remboursement
        
        GET /api/receipts/remboursement/?remboursement_id=1
        """
        remboursement_id = request.query_params.get('remboursement_id')
        if not remboursement_id:
            return Response(
                {'error': 'remboursement_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pdf_buffer = generate_receipt_remboursement(int(remboursement_id))
            if not pdf_buffer:
                return Response(
                    {'error': 'Remboursement non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_remboursement_{remboursement_id}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du reçu: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Reçu de frais d'adhésion",
        description="Génère un reçu PDF pour un paiement de frais d'adhésion",
        parameters=[
            OpenApiParameter(name='frais_adhesion_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True, description='ID des frais d\'adhésion')
        ],
        tags=['Rapports']
    )
    @action(detail=False, methods=['get'])
    def frais_adhesion(self, request):
        """
        Génère un reçu PDF pour un paiement de frais d'adhésion
        
        GET /api/receipts/frais_adhesion/?frais_adhesion_id=1
        """
        frais_adhesion_id = request.query_params.get('frais_adhesion_id')
        if not frais_adhesion_id:
            return Response(
                {'error': 'frais_adhesion_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pdf_buffer = generate_receipt_frais_adhesion(int(frais_adhesion_id))
            if not pdf_buffer:
                return Response(
                    {'error': 'Frais d\'adhésion non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_frais_adhesion_{frais_adhesion_id}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du reçu: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Reçu d'opération",
        description="Génère un reçu PDF pour une opération de caisse",
        parameters=[
            OpenApiParameter(name='operation_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True, description="ID de l'opération")
        ],
        tags=['Rapports']
    )
    @action(detail=False, methods=['get'])
    def operation(self, request):
        """
        Génère un reçu PDF pour une opération de caisse
        
        GET /api/receipts/operation/?operation_id=1
        """
        operation_id = request.query_params.get('operation_id')
        if not operation_id:
            return Response(
                {'error': 'operation_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pdf_buffer = generate_receipt_transaction(int(operation_id))
            if not pdf_buffer:
                return Response(
                    {'error': 'Opération non trouvée'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_operation_{operation_id}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du reçu: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Relevé de compte",
        description="Génère un relevé de compte PDF pour un membre ou un client avec toutes ses OPERATIONS",
        parameters=[
            OpenApiParameter(name='membre_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description='ID du membre'),
            OpenApiParameter(name='client_id', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description='ID du client'),
            OpenApiParameter(name='date_debut', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False, description='Date de début (format: YYYY-MM-DD)'),
            OpenApiParameter(name='date_fin', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False, description='Date de fin (format: YYYY-MM-DD)')
        ],
        tags=['Rapports']
    )
    @action(detail=False, methods=['get'])
    def releve_compte(self, request):
        """
        Génère un relevé de compte PDF pour un membre ou un client
        
        GET /api/receipts/releve_compte/?membre_id=1&date_debut=2025-01-01&date_fin=2025-12-31
        GET /api/receipts/releve_compte/?client_id=1&date_debut=2025-01-01&date_fin=2025-12-31
        """
        membre_id = request.query_params.get('membre_id')
        client_id = request.query_params.get('client_id')
        date_debut_str = request.query_params.get('date_debut')
        date_fin_str = request.query_params.get('date_fin')
        
        if not membre_id and not client_id:
            return Response(
                {'error': 'membre_id ou client_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if membre_id and client_id:
            return Response(
                {'error': 'Spécifiez soit membre_id soit client_id, pas les deux'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parser les dates
        date_debut = None
        date_fin = None
        
        if date_debut_str:
            try:
                date_debut = date.fromisoformat(date_debut_str)
            except ValueError:
                return Response(
                    {'error': 'Format de date_debut invalide. Utilisez YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if date_fin_str:
            try:
                date_fin = date.fromisoformat(date_fin_str)
            except ValueError:
                return Response(
                    {'error': 'Format de date_fin invalide. Utilisez YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            pdf_buffer = generate_account_statement(
                membre_id=int(membre_id) if membre_id else None,
                client_id=int(client_id) if client_id else None,
                date_debut=date_debut,
                date_fin=date_fin
            )
            
            if not pdf_buffer:
                return Response(
                    {'error': 'Membre/Client non trouvé ou aucune opération'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Nom du fichier
            if membre_id:
                filename = f"releve_compte_membre_{membre_id}"
            else:
                filename = f"releve_compte_client_{client_id}"
            
            if date_debut and date_fin:
                filename += f"_{date_debut.strftime('%Y%m%d')}_{date_fin.strftime('%Y%m%d')}"
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la génération du relevé: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )